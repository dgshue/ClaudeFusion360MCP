# Pitfalls Research

**Domain:** Fusion 360 MCP Server -- Python API automation for CAD operations
**Researched:** 2026-03-13
**Confidence:** HIGH (verified against official Autodesk docs, codebase analysis, and documented empirical errors)

## Critical Pitfalls

### Pitfall 1: Threading Violation -- Calling Fusion API from Worker Thread

**What goes wrong:**
The current add-in calls Fusion 360 API functions directly from a background `threading.Thread` in `monitor_commands()`. Fusion 360 is single-threaded. Calling ANY Fusion API function from a worker thread -- even `ui.messageBox()` -- can crash Fusion silently or produce corrupted geometry. The current code works by luck, not correctness.

**Why it happens:**
The file-polling pattern naturally lives in a background thread. Developers assume "it reads a file, processes, writes a response" is safe. But `execute_command()` calls `rootComp.sketches.add()`, `extrudes.add()`, etc. -- all Fusion API calls that MUST execute on the main thread.

**How to avoid:**
Use Fusion's `CustomEvent` pattern:
1. Register a custom event in `run()` with `app.registerCustomEvent(eventId)`
2. Worker thread monitors files and calls `app.fireCustomEvent(eventId, jsonData)` instead of executing commands directly
3. Custom event handler runs on the main thread and executes the Fusion API calls
4. Worker thread waits for response via a threading event or shared variable

This is the officially documented pattern from Autodesk for add-ins that need background processing.

**Warning signs:**
- Fusion crashes intermittently with no error message
- Geometry operations succeed sometimes and fail silently other times
- `traceback.format_exc()` in bare `except:` blocks never fires because the crash is at the C++ level
- Adding more concurrent tools makes crashes more frequent

**Phase to address:**
Phase 1 (Foundation/Infrastructure). This is the single most important architectural fix. Every subsequent tool implementation builds on this pattern. Fixing it later means rewriting every handler.

---

### Pitfall 2: Face/Edge Index Instability After Geometry Operations

**What goes wrong:**
Edge and face indices change after ANY geometry-modifying operation (fillet, chamfer, shell, extrude, boolean). Code that stores an index from `get_body_info()` and uses it in a subsequent operation (like `shell(faces_to_remove=[4])`) operates on the WRONG face. The project already documented this as Error Case 004 in SPATIAL_AWARENESS.md -- face 4 (top) became face 2 after filleting, causing shell to destroy the model.

**Why it happens:**
Fusion 360's B-Rep kernel regenerates topology after each feature. New faces from fillets insert into the index list, shifting everything. Developers assume indices are stable identifiers, but they are positional offsets into a regenerated list.

**How to avoid:**
- ALWAYS re-query `get_body_info()` immediately before any operation that uses face/edge indices
- Identify faces/edges by geometric properties (centroid position, area, normal direction) rather than stored indices
- Build helper functions: `find_face_by_position(body, "top")` that looks for `centroid.z == bbox.max.z`
- For the MCP tools, accept semantic selectors ("top", "bottom", "largest") alongside raw indices

**Warning signs:**
- Shell/chamfer/fillet applied to wrong face after prior operations
- "Index out of range" errors that only happen in multi-step workflows
- Operations work in isolation but fail in batch sequences

**Phase to address:**
Phase 1 (Foundation). Build face/edge identification helpers before implementing shell, draft, chamfer, or any tool that selects specific geometry.

---

### Pitfall 3: Profile Index Non-Determinism

**What goes wrong:**
When a sketch contains multiple closed profiles (e.g., a rectangle with a circle inside it creates 2 profiles), the profile indices are NOT deterministic. The same sketch geometry can produce different profile ordering on different runs. The current `extrude_profile()` always takes `profiles.item(profiles.count - 1)` which may not be the intended profile.

**Why it happens:**
Fusion's internal profile detection depends on geometry processing order, which is not guaranteed stable. A rectangle with a hole produces profile 0 = the ring (rectangle minus circle area) and profile 1 = the circle interior, but this ordering can flip. The official Fusion docs confirm: only closed profiles are counted, and ordering is not guaranteed.

**How to avoid:**
- When only one profile exists, `profiles.item(0)` is safe
- When multiple profiles exist, identify the correct one by area or centroid position, not index
- Add a `profile_index` parameter (already in MCP server, not in add-in) but document that indices may shift
- For complex sketches, consider one sketch per profile to guarantee profile count = 1
- Return profile count and areas in `create_sketch`/`finish_sketch` response so the caller can make informed choices

**Warning signs:**
- Extrude creates the wrong shape (extruding the hole instead of the ring, or vice versa)
- Batch operations that work 90% of the time but occasionally produce wrong geometry
- Works perfectly with simple sketches, breaks with complex ones

**Phase to address:**
Phase 2 (Sketch tools expansion). When implementing advanced sketch geometry that creates multiple closed regions, profile selection logic must be robust.

---

### Pitfall 4: XZ Plane Y-Axis Inversion (Confirmed by Autodesk Engineering)

**What goes wrong:**
Sketch Y on the XZ plane maps to World -Z (negated). Sketch X on the YZ plane also maps to World -Z. This means geometry drawn at `center_y=0.3` on the XZ plane appears at World Z=-0.3. This is BY DESIGN per Autodesk's Jeff Strater -- it satisfies right-hand coordinate system requirements while keeping positive extrusion going toward +Y.

**Why it happens:**
It is not a bug. Two competing requirements (right-handed coordinate system AND positive extrusion toward +Y) force the inversion. But it is deeply non-intuitive and the project has already documented three separate error cases from this behavior.

**How to avoid:**
- Encapsulate the negation in the add-in's handlers, NOT in the AI caller. The add-in should accept `world_z` parameters and internally apply `sketch_y = -world_z` for XZ plane operations
- Alternatively, provide a coordinate transformation utility that all sketch tools call before placing geometry
- Document the transformation clearly in every tool that accepts sketch coordinates
- Consider offering "world coordinate mode" vs "sketch coordinate mode" as a parameter

**Warning signs:**
- Geometry appears mirrored on the Z axis
- Parts are "upside down" when drawn on XZ or YZ planes
- Repeatedly needing to negate values manually in tool calls

**Phase to address:**
Phase 1 (Foundation). Build the coordinate transformation layer before implementing additional sketch geometry tools. Every subsequent sketch tool inherits the fix.

---

### Pitfall 5: Bare Exception Swallowing All Errors

**What goes wrong:**
The current add-in has multiple `except: pass` blocks (lines 26, 36-37, 52-53, 55-56 in FusionMCP.py). When a Fusion API call fails, the exception is silently swallowed. The MCP server times out after 45 seconds, and the user sees "Timeout -- is Fusion 360 running?" instead of the actual error message. This makes debugging impossible.

**Why it happens:**
Defensive coding instinct -- "catch everything so the add-in doesn't crash." But in an automation context, silent failure is worse than a crash. The add-in keeps running but stops processing the failed command, and no response file is ever written.

**How to avoid:**
- Replace ALL `except: pass` with `except Exception as e:` and write the error to the response file
- In `monitor_commands()`, if command processing fails, write an error response: `{"success": false, "error": str(e), "traceback": traceback.format_exc()}`
- Log errors to a file (`~/fusion_mcp_comm/error.log`) with timestamps for debugging
- Never use bare `except:` -- always catch `Exception` at minimum

**Warning signs:**
- MCP server times out but Fusion appears healthy
- Commands "disappear" -- command file is consumed but no response file appears
- User reports "it worked yesterday but not today" with no error messages

**Phase to address:**
Phase 1 (Foundation). This is a prerequisite for debugging any subsequent tool implementation.

---

### Pitfall 6: Server-Addin Tool Mismatch (39 Tools Defined, 9 Implemented)

**What goes wrong:**
The MCP server defines 39 tools. The add-in implements 9 handlers. 30 tools return `{"success": false, "error": "Unknown tool: <name>"}`. Users discover tools via the MCP protocol, call them, and get cryptic failures. The MCP server's `send_fusion_command()` treats ANY `success: false` as an exception, so calling `shell()` raises `Exception("Unknown tool: shell")`.

**Why it happens:**
The MCP server was written aspirationally -- defining the desired tool surface. The add-in was written incrementally -- implementing what was immediately needed. No contract enforcement exists between them.

**How to avoid:**
- Implement a tool registry pattern: the add-in declares which tools it supports, and the MCP server only registers those
- Or: implement ALL tools in the add-in before exposing them via MCP
- Add a startup handshake: MCP server queries the add-in for its supported tools list
- Use code generation: auto-generate the add-in's dispatch table from the MCP server's tool definitions, with stub handlers that return "not yet implemented" with clear messaging

**Warning signs:**
- Users report "Unknown tool" errors for tools that appear in documentation
- Tool reference docs describe capabilities that don't work
- Adding new MCP tools without corresponding add-in handlers

**Phase to address:**
Phase 1 (Foundation). The gap must be closed before expanding to new tools. Either remove unimplemented tools from the MCP server or implement them in the add-in.

---

### Pitfall 7: No Design History / Undo Transaction Grouping

**What goes wrong:**
Each Fusion API call creates a separate entry in the design timeline. A batch of 20 operations creates 20 undo entries. If the user needs to undo, they must press Ctrl+Z 20 times. The `undo(count=N)` tool exists but undoing a partial batch leaves the design in an inconsistent intermediate state.

**Why it happens:**
Fusion 360 treats each API call as an independent command. Without explicit transaction grouping, there is no way to undo a logical operation (like "create a box with filleted edges") as a single step.

**How to avoid:**
- Use `design.timeline` API to group operations: create a timeline group that wraps all operations from a single MCP command or batch
- For batch operations, wrap the entire batch in a timeline group so undo reverts the whole batch
- Consider using the `BaseFeature` pattern for direct modeling operations that should be atomic
- At minimum, document which operations are "safe to undo" and which leave inconsistent state

**Warning signs:**
- Timeline becomes extremely long after batch operations
- Undoing one operation breaks subsequent geometry
- Users cannot return to a known-good state after a failed multi-step workflow

**Phase to address:**
Phase 2 or 3 (after core tools work). Timeline grouping is important for usability but not a blocker for individual tool implementation.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| "Last sketch/body" default selection | Simpler API -- no need to specify targets | Breaks when design has multiple sketches/bodies from prior operations; wrong target selected silently | Only for single-body, single-sketch workflows. Add explicit target selection for multi-body designs. |
| File-system IPC with polling | Simple to implement, no dependencies | 50ms polling wastes CPU. Orphaned files accumulate. No back-pressure. Race conditions possible with rapid commands. | Acceptable for personal use with <10 commands/sec. Not acceptable for CI/CD or multi-agent scenarios. |
| Hardcoded `rootComp` for all operations | Works for flat designs | Breaks when working inside nested components. Operations always target root, not active component context. | Never acceptable once component/assembly tools are implemented. Must resolve active component context. |
| No input validation on parameters | Faster tool implementation | Fusion API throws cryptic C++ errors for invalid inputs (negative radius, zero-length extrusion). User sees meaningless stack traces. | Never -- validate before calling Fusion API. Return human-readable errors. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Fusion 360 Python API | Calling API from background thread | Use CustomEvent pattern: worker thread fires event, handler runs on main thread |
| Fusion 360 Python API | Using `adsk.core.Application.get()` once at startup and caching | Acceptable IF kept as global. But `design = app.activeProduct` must be called fresh each time -- user may have switched documents |
| Fusion 360 Python API | Assuming `app.activeProduct` is always a `Design` | It returns `Product` base class. Could be `CAMProduct` or `None` if no document is open. Always check type. |
| File-system IPC | Using timestamp as unique command ID | `int(time.time() * 1000)` can produce duplicates if two commands arrive in the same millisecond. Use UUID or atomic counter. |
| File-system IPC | Reading command file while it is still being written | MCP server writes directly to target path. Add-in may read partial JSON. Write to temp file, then rename (atomic on most OS). |
| Sketch profiles | Assuming profile count matches expected geometry | Overlapping or self-intersecting sketch geometry creates unexpected profile counts. Validate `sketch.profiles.count` before extruding. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-querying `get_design_info()` / `get_body_info()` on every call | Response times increase linearly with design complexity | Cache body/sketch metadata, invalidate on mutation operations | Designs with >50 bodies or >100 sketches |
| Creating one sketch per geometric entity | Sketch count explodes, timeline becomes unmanageable, design slows down | Group related geometry into single sketches. Use construction geometry for reference. | >20 sketches in a design |
| Rectangular/circular pattern with large counts | Fusion UI freezes, memory spikes, potential crash | Validate count * spacing fits within reasonable bounds. Warn if pattern creates >100 instances. | Pattern count > 100 instances |
| Batch operations without error boundaries | One failure kills entire batch, no partial results returned | Implement per-command try/catch in batch. Return success/failure per command. | Any batch with >5 commands where one might fail |
| Full edge iteration for body info | Scanning all edges/faces of complex bodies is slow | Limit `get_body_info()` response to summary (count, bounding box) unless detail is requested | Bodies with >500 edges (common after fillets on complex shapes) |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| No file path sanitization on export/import | Directory traversal attack -- export to system directories | Validate paths are within allowed directories. Reject paths containing `..`. Require absolute paths. |
| No command authentication | Any local process can write command files and execute Fusion operations | Add a shared secret/nonce generated at MCP startup, required in all command files |
| JSON command files readable/writable by any user | Sensitive design data or export paths exposed | Set restrictive file permissions on `~/fusion_mcp_comm/` directory |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Timeout error instead of actual error message | User thinks Fusion is not running when the real issue is a parameter error | Always write error response files, even for failures. Timeout should be last resort. |
| "Unknown tool" for unimplemented tools | User discovers tool in docs, tries it, gets unhelpful error | Either implement the tool or don't expose it in MCP. Clear "not yet implemented" message. |
| Units always in centimeters, no indication | User enters millimeters, gets 10x oversized parts | Include unit context in tool descriptions. Add a `units` parameter or conversion helper. Warn if values seem too large (>50cm). |
| No visual feedback during long operations | User doesn't know if Fusion is processing or frozen | Return progress updates for long operations. At minimum, log "processing command X" to Fusion console. |
| Combine/join without user confirmation | Wrong geometry permanently merged into model | Always create new bodies first. Require explicit confirmation before boolean operations. |

## "Looks Done But Isn't" Checklist

- [ ] **Sketch tool:** Returns success but sketch has zero profiles -- verify `sketch.profiles.count > 0` before considering geometry complete
- [ ] **Extrude:** Returns success but created body is zero-volume -- verify body exists in `rootComp.bRepBodies` after extrude
- [ ] **Fillet/Chamfer:** Returns success but silently skipped invalid edges -- verify edge count changed or feature was actually added to timeline
- [ ] **Component creation:** Returns success but body was moved to component and is no longer in `rootComp.bRepBodies` -- update body tracking after component creation
- [ ] **Batch operation:** Returns overall success but individual commands may have failed silently -- verify each sub-result
- [ ] **Shell:** Returns success but wall thickness was too large for geometry, creating invalid topology -- check body is still valid after shell
- [ ] **Export:** Returns success but file is 0 bytes -- verify file size after export

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong face/edge selected | LOW | Undo operation, re-query `get_body_info()`, retry with correct index |
| XZ plane inversion applied wrong | LOW | Undo, negate the Y values, retry |
| Threading crash | HIGH | Restart Fusion 360. Unsaved work is lost. Implement auto-save before operations. |
| Bare exception swallowed error | MEDIUM | Check `~/fusion_mcp_comm/` for orphaned command files. Re-run with logging enabled. |
| Profile index wrong | LOW | Undo extrude, check profile count and areas, retry with correct index |
| Server-addin tool mismatch | LOW | Check add-in handler list against MCP tool list. Implement missing handler. |
| Batch partial failure | MEDIUM | Use `undo(count=N)` to revert all operations in the batch. Requires knowing how many succeeded. |
| Pattern created too many bodies | HIGH | Undo is possible but Fusion may be frozen. May need to force-quit and recover from last save. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Threading violation (CustomEvent) | Phase 1 - Foundation | All Fusion API calls execute inside custom event handler. Worker thread only fires events. |
| Bare exception handling | Phase 1 - Foundation | Zero `except: pass` blocks remain. All errors produce response files with error details. |
| Server-addin tool mismatch | Phase 1 - Foundation | `len(mcp_tools) == len(addin_handlers)`. No "Unknown tool" errors for registered tools. |
| Face/edge index instability | Phase 1 - Foundation | Helper functions exist for semantic face selection (by position, area, normal). |
| XZ plane coordinate inversion | Phase 1 - Foundation | Coordinate transformation layer tested. Sketch tools accept world coordinates. |
| Profile index non-determinism | Phase 2 - Sketch Expansion | Profile selection by area/centroid available. Single-profile sketches documented as best practice. |
| No transaction grouping | Phase 2/3 - Features | Batch operations create single timeline group. Undo reverts entire batch. |
| Pattern count validation | Phase 3 - 3D Features | Input validation rejects pattern counts > configurable limit (default 100). |
| Component context (`rootComp` hardcoding) | Phase 4 - Assemblies | Active component context resolved before operations. Nested components supported. |
| File path sanitization | Phase 1 - Foundation | Export/import paths validated. Directory traversal rejected. |

## Sources

- [Autodesk: Working in a Separate Thread](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Threading_UM.htm) -- Official threading requirements (HIGH confidence)
- [Autodesk: Application.fireCustomEvent](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Application_fireCustomEvent.htm) -- Custom event API (HIGH confidence)
- [Autodesk: Custom Event Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomEventSample_Sample.htm) -- Reference implementation (HIGH confidence)
- [Autodesk: Python Specific Issues](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonSpecific_UM.htm) -- Type casting pitfalls (HIGH confidence)
- [Autodesk: Profiles.count Property](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Profiles_count.htm) -- Profile counting behavior (HIGH confidence)
- [Autodesk Forum: How Profiles in Sketch are Indexed](https://forums.autodesk.com/t5/fusion-360-api-and-scripts/how-profiles-in-sketch-are-index/td-p/11895478) -- Profile index non-determinism (MEDIUM confidence)
- [Autodesk Forum: XZ Plane Z-Axis Inversion](https://forums.autodesk.com/t5/fusion-support-forum/sketch-on-xz-plane-shows-z-positive-downwards-left-handed-coord/td-p/11675127) -- Confirmed by Autodesk engineering (HIGH confidence)
- [Autodesk: Application.activeEditObject](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Application_activeEditObject.htm) -- Edit context behavior (HIGH confidence)
- Project docs: `docs/KNOWN_ISSUES.md`, `docs/SPATIAL_AWARENESS.md` -- Empirically verified error cases (HIGH confidence)
- Project analysis: `fusion-addin/FusionMCP.py`, `mcp-server/fusion360_mcp_server.py` -- Direct code review (HIGH confidence)

---
*Pitfalls research for: Fusion 360 MCP Server (Python API automation)*
*Researched: 2026-03-13*
