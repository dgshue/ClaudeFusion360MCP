# Codebase Concerns

**Analysis Date:** 2026-03-13

## Tech Debt

**Bare Exception Handling in Add-in:**
- Issue: Multiple bare `except:` clauses catch all exceptions without logging or specific error handling
- Files: `fusion-addin/FusionMCP.py` (lines 26, 36-37, 52-53, 55-56)
- Impact: Silent failures make debugging difficult. Errors in command execution are swallowed completely, leaving no trace for the user or developer. The user sees a timeout rather than the actual error message.
- Fix approach: Replace bare `except:` with `except Exception as e:` and log to a file or UI message box. Store errors with timestamps for debugging sessions.

**Incomplete Command Filtering in Add-in:**
- Issue: `FusionMCP.py` line 88 returns generic "Unknown tool" error for unimplemented tools, but the MCP server (`fusion360_mcp_server.py`) has 60+ tool definitions that the add-in doesn't implement
- Files: `fusion-addin/FusionMCP.py` (lines 58-87) vs `mcp-server/fusion360_mcp_server.py` (full implementation)
- Impact: Most MCP tools will fail silently. Users will get "Unknown tool" errors when calling legitimate tools like `move_component`, `rotate_component`, `shell`, `draft`, `pattern_rectangular`, etc.
- Fix approach: Either implement all 60+ tools in the add-in, or create a dispatch layer that maps tools to a Fusion Python API wrapper. Consider code generation from the MCP server definition.

**Unlink Operations Ignore Failures:**
- Issue: Lines 56-59 in `mcp-server/fusion360_mcp_server.py` attempt to unlink command and response files with blanket `try/except`
- Files: `mcp-server/fusion360_mcp_server.py` (lines 56-59)
- Impact: Orphaned JSON files accumulate in `~/fusion_mcp_comm/` directory, consuming disk space and making debugging harder. No indication that cleanup failed.
- Fix approach: Log cleanup failures separately. Implement periodic cleanup of stale files (>1 hour old).

**No Versioning Between Server and Add-in:**
- Issue: MCP server version (v7.2 in docstring) and add-in version have no compatibility checking
- Files: `mcp-server/fusion360_mcp_server.py` (line 38 mentions v7.2) vs `fusion-addin/FusionMCP.py` (no version info)
- Impact: Version mismatch causes silent tool failures. Users won't know if their add-in is too old for the server.
- Fix approach: Add version field to command JSON. Add-in should validate server version on startup.

## Known Bugs

**Sketch Edit Mode State Corruption:**
- Symptoms: After `draw_circle()` or `draw_rectangle()` calls, the add-in doesn't enter sketch edit mode. The drawing functions use hardcoded sketch index (last sketch) without verifying edit state.
- Files: `fusion-addin/FusionMCP.py` (lines 103-108, 111-117)
- Trigger: Call `create_sketch()` then `draw_circle()` rapidly. The sketch may not be in edit mode, causing geometry to fail silently.
- Workaround: The newer code uses `rootComp.sketches.item()` instead of `activeEditObject`, which works without entering edit mode. This is a workaround, not a fix.

**finish_sketch Implementation Gap:**
- Symptoms: `finish_sketch()` was updated to do nothing (lines 160-163), but if users call it before extrude, the sketch is still active and extrude fails.
- Files: `fusion-addin/FusionMCP.py` (lines 160-163) - comment says "Sketch drawing is done directly" but this isn't validated
- Trigger: Workflow that explicitly calls finish_sketch before extrude
- Workaround: Skip finish_sketch entirely

**Fillet Applies to ALL Edges Without Exception:**
- Symptoms: The `add_fillet()` function (line 150-158) applies fillets to every edge in the body
- Files: `fusion-addin/FusionMCP.py` (lines 150-158)
- Trigger: Try to fillet only specific edges - the function ignores the `edges` parameter that the MCP server accepts
- Workaround: None - function doesn't support selective edge filtering despite MCP server declaring it does

## Security Considerations

**File System Permissions Not Validated:**
- Risk: The MCP server writes to `~/fusion_mcp_comm/` directory without checking permissions. If home directory is on a network share or has restricted permissions, commands fail silently.
- Files: `mcp-server/fusion360_mcp_server.py` (lines 35-36, 43-44, 46-47, 52)
- Current mitigation: `COMM_DIR.mkdir(exist_ok=True)` creates directory but doesn't verify write access
- Recommendations: Check write permissions on startup. Test by writing a test file. Raise exception if directory is not writable.

**Export Paths Not Sanitized:**
- Risk: `export_stl()`, `export_step()`, `export_3mf()` and `import_mesh()` accept arbitrary filepath strings (lines 599-620)
- Files: `mcp-server/fusion360_mcp_server.py` (lines 598-620)
- Current mitigation: None - file paths are passed directly to Fusion API
- Recommendations: Validate filepaths are within expected directories. Prevent directory traversal (../../../etc/passwd). Require absolute paths only.

**JSON Command Injection Risk:**
- Risk: The add-in reads JSON directly from command files without validation (FusionMCP.py line 47)
- Files: `fusion-addin/FusionMCP.py` (line 47: `command = json.load(f)`)
- Current mitigation: None
- Recommendations: Implement schema validation on command JSON. Use jsonschema library to validate structure before processing.

**No Authentication Between Server and Add-in:**
- Risk: Any process can write to `~/fusion_mcp_comm/` and execute arbitrary tools
- Files: Communication protocol in `mcp-server/fusion360_mcp_server.py` (lines 43-52) and `fusion-addin/FusionMCP.py` (lines 39-56)
- Current mitigation: None
- Recommendations: Add a simple token/nonce system. Generate random token on MCP startup and require it in all commands.

## Performance Bottlenecks

**Polling Loop with Fixed Sleep:**
- Problem: MCP server polls for commands at fixed 50ms intervals (line 51) regardless of how many files exist
- Files: `mcp-server/fusion360_mcp_server.py` (line 51: `time.sleep(0.05)`)
- Cause: Busy-waiting in loop. With many commands, the loop wakes up 20x per second even if no new commands exist.
- Improvement path: Use file system watchers (watchdog library) instead of polling. Or scan only recent files using modification time.

**No Response Timeout Cleanup:**
- Problem: If Fusion crashes or add-in dies, response files remain in `~/fusion_mcp_comm/` forever
- Files: `mcp-server/fusion360_mcp_server.py` (command cleanup at lines 56-59)
- Cause: Response files are only unlinked if read successfully. Crashed processes don't return responses.
- Improvement path: Implement cleanup of response files older than 60 seconds.

**Batch Command Stops on First Error:**
- Problem: When `batch()` encounters an error, it stops processing remaining commands (documented at line 84 but not validated)
- Files: `mcp-server/fusion360_mcp_server.py` (lines 70-86)
- Cause: Each command is executed sequentially without try/catch to continue on failure
- Improvement path: Add `stop_on_error` parameter. Allow batch to track which commands succeeded/failed and return detailed results.

**No Caching of Design State:**
- Problem: Every call to `get_design_info()` re-scans the entire design structure
- Files: `mcp-server/fusion360_mcp_server.py` (lines 323-326)
- Cause: No caching between calls
- Improvement path: Cache body/sketch count with invalidation on mutations (create, delete, extrude operations)

## Fragile Areas

**XZ Plane Z-Axis Negation Logic:**
- Files: `docs/SPATIAL_AWARENESS.md` (lines 45-87) and `docs/KNOWN_ISSUES.md` (lines 179-246)
- Why fragile: The coordinate system inversion is by design (verified by Autodesk engineering) but requires users to negate Y values when using XZ plane. This is non-intuitive and easy to get wrong.
- Safe modification: Encapsulate Z-negation in a helper function. Have the MCP server handle the negation internally rather than requiring Claude to do it.
- Test coverage: SKILL.md and SPATIAL_AWARENESS.md document it extensively, but there are no programmatic tests validating the negation.

**Component Index Brittleness:**
- Files: `docs/KNOWN_ISSUES.md` (lines 101-111) and `mcp-server/fusion360_mcp_server.py` (lines 391-399)
- Why fragile: Deleting components by index shifts indices of remaining components. If Claude deletes component 0, component 1 becomes component 0. Any stored indices become invalid.
- Safe modification: Always use component names, never indices. Implement `get_component_by_name()` to avoid index brittleness.
- Test coverage: No automated tests for component deletion scenarios.

**Auto-Join Without Verification:**
- Files: `docs/KNOWN_ISSUES.md` (lines 250-285) - this issue was JUST added and is a documented concern
- Why fragile: Claude may automatically join bodies without asking user to verify shape/position first. If geometry is wrong, it's baked into the model.
- Safe modification: Enforce explicit user approval before any `combine()` call. The SKILL.md guidance (Section 0) attempts to enforce this but there's no programmatic check.
- Test coverage: No API-level enforcement. Depends entirely on Claude following documented protocol.

**Selective Edge/Face Selection by Index:**
- Files: `mcp-server/fusion360_mcp_server.py` (lines 174-210, 216-236)
- Why fragile: The `fillet()`, `chamfer()`, `shell()`, and `draft()` tools accept edge/face indices, but these are fragile - adding a new edge can shift all indices.
- Safe modification: Allow face/edge selection by properties (e.g., "all vertical faces", "edges longer than 1cm"). Use topology hashing to preserve identity across operations.
- Test coverage: No tests for selective edge operations.

## Scaling Limits

**Command Queue Unbounded:**
- Current capacity: Limited only by disk space in `~/fusion_mcp_comm/`
- Limit: If 10,000+ commands pile up (due to slow Fusion or network lag), directory browser/OS may struggle with that many files
- Scaling path: Implement a queue in the add-in. Limit to N concurrent commands. Fail with "queue full" rather than creating infinite files.

**Sketch Complexity Not Validated:**
- Current capacity: Fusion 360 can handle 1000s of geometry entities per sketch
- Limit: Creating massive sketches with `batch()` may cause Fusion to hang or crash
- Scaling path: Add sketch complexity warnings. Suggest breaking into multiple sketches if geometry count exceeds threshold (e.g., >500 entities).

**Body Count Unbounded:**
- Current capacity: Fusion 360 typically handles 100s of bodies per design
- Limit: With `pattern_rectangular()` creating 10,000+ instances, the design becomes unmaneageable
- Scaling path: Warn user if pattern would create >1000 bodies. Suggest using native Fusion features (Body::combine) instead.

## Dependencies at Risk

**No Version Pinning in Python:**
- Risk: `mcp-server/fusion360_mcp_server.py` imports from `mcp.server.fastmcp` with no version specification
- Files: `mcp-server/fusion360_mcp_server.py` (line 30)
- Impact: MCP library updates could break compatibility. `fastmcp` API is young and unstable.
- Migration plan: Pin to `mcp==0.9.x` (or latest stable). Test against new versions before updating.

**Autodesk Fusion Python API Versioning:**
- Risk: Fusion 360 API changes between versions. Current code assumes Fusion 2024+
- Files: `fusion-addin/FusionMCP.py` imports `adsk.core` and `adsk.fusion` with no version check
- Impact: May fail silently on older Fusion 360 installations
- Migration plan: Add Fusion version detection on startup. Log warning if <2024 version detected.

## Missing Critical Features

**No Save Function:**
- Problem: Users can export files but cannot save the Fusion 360 design (.f3d file) programmatically
- Blocks: Any workflow requiring design persistence requires manual save (Ctrl+S)
- Impact: High friction for CI/CD pipelines or server-based automation

**No Undo Integration:**
- Problem: `undo()` function exists but cannot undo group actions (batch operations)
- Blocks: If batch fails partway through, user must undo multiple times individually
- Impact: Users cannot recover from partial batch failures easily

**No Layer/Component Organization:**
- Problem: No tools to create nested component hierarchies or layer-based filtering
- Blocks: Complex assemblies become hard to navigate without native Fusion layer support
- Impact: Large designs will be difficult to manage

**No Constraints or Parametric Features:**
- Problem: Cannot create parametric relationships (e.g., "hole diameter = 2x pad height")
- Blocks: Design intent cannot be captured. Changes require manual re-creation
- Impact: User cannot leverage Fusion's parametric capabilities through MCP

**No Sketch Constraints:**
- Problem: Cannot apply coincident, tangent, parallel, perpendicular constraints to sketch geometry
- Blocks: Sketches are under-constrained, leading to geometry that shifts unexpectedly
- Impact: Designs are fragile and not properly engineered

## Test Coverage Gaps

**No Batch Command Error Handling Tests:**
- What's not tested: Behavior when 5th command in batch fails - what happens to commands 6-10?
- Files: `mcp-server/fusion360_mcp_server.py` (lines 70-86)
- Risk: Silent partial failures. Batch returns success but only some commands executed.
- Priority: High

**No Coordinate System Verification Tests:**
- What's not tested: XZ plane negation rule is documented but no automated verification that negation works correctly
- Files: Extensive docs in `docs/KNOWN_ISSUES.md` and `docs/SPATIAL_AWARENESS.md` but no test suite
- Risk: Regression - if someone changes coordinate mapping, tests would catch it
- Priority: High

**No Component Deletion Index Shift Tests:**
- What's not tested: Deleting component 0 from a 3-component assembly, then checking indices
- Files: `mcp-server/fusion360_mcp_server.py` (lines 391-399)
- Risk: Index-based operations fail after deletion without clear error message
- Priority: Medium

**No File System Permission Tests:**
- What's not tested: MCP startup when `~/fusion_mcp_comm/` directory is read-only
- Files: `mcp-server/fusion360_mcp_server.py` (lines 35-36)
- Risk: Server appears to start but immediately fails on first command
- Priority: Medium

**No Integration Tests with Real Fusion 360:**
- What's not tested: Most of the codebase - requires Fusion running and add-in installed
- Files: All `fusion-addin/` and most `mcp-server/` code
- Risk: High - changes could break core functionality undetected
- Priority: High

**No Tool Interface Contract Tests:**
- What's not tested: Does the MCP server actually implement all documented tools? Are tool signatures correct?
- Files: Gap between `mcp-server/fusion360_mcp_server.py` and `fusion-addin/FusionMCP.py`
- Risk: Tools documented in TOOL_REFERENCE.md don't work
- Priority: High

---

*Concerns audit: 2026-03-13*
