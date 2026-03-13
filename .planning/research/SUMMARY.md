# Project Research Summary

**Project:** ClaudeFusion360MCP
**Domain:** Fusion 360 MCP Server — AI-driven CAD automation via Model Context Protocol
**Researched:** 2026-03-13
**Confidence:** HIGH

## Executive Summary

ClaudeFusion360MCP is a Model Context Protocol server that bridges Claude (and other MCP-compatible AI clients) to Autodesk Fusion 360's Python API. The architecture is fundamentally a two-process system: an MCP server running in system Python handles tool registration and protocol communication, while a Fusion 360 add-in running in Fusion's embedded Python (3.12.4) executes CAD operations. Communication between them uses file-system IPC with JSON payloads — a proven pattern used by other Fusion MCP projects that works within the constraint that Fusion's embedded Python cannot easily host an HTTP server. The recommended approach is to keep this architecture and scale it cleanly: refactor the add-in's monolithic if/elif dispatcher into domain-grouped handler modules with dict-based dispatch, then systematically implement the 30 declared-but-missing tool handlers before expanding to new capabilities.

The project is currently in a deceptive state: 39 MCP tools are defined but only 9 have working add-in handlers, and several of those 9 have bugs (fillet ignores edge selection, revolve hardcodes Y-axis, error handling swallows exceptions silently). The highest-priority work is not building new features — it is closing the 30-tool gap and fixing the broken foundation. Every tool the user discovers and calls that returns "Unknown tool" destroys trust. The research strongly supports a "fix before expand" approach organized by the dependency graph: infrastructure and error handling first, then sketch primitives, then 3D features, then assembly tools, then parametric and discoverability features.

The most critical risk is a threading violation baked into the current architecture: Fusion API calls are being made from a background thread, which can crash Fusion silently. This is the single most dangerous defect and must be fixed in Phase 1 using Fusion's CustomEvent pattern before any additional handlers are added. Additional confirmed risks include XZ-plane Y-axis inversion (a documented Autodesk design decision), face/edge index instability after geometry operations, and profile index non-determinism in multi-region sketches. All of these have clear mitigation strategies documented in the research and must be addressed as foundational infrastructure before handler expansion.

## Key Findings

### Recommended Stack

The project's existing stack choices are correct and should be kept. The MCP server uses `mcp` 1.26.0 (official SDK with bundled FastMCP) in system Python 3.10+; the add-in uses Fusion 360's embedded Python 3.12.4 with no installable packages. The two runtimes are strictly isolated — the add-in cannot import `mcp`, `pydantic`, or any third-party library; it can only use `adsk.*` and Python stdlib. This constraint is absolute and shapes every architectural decision.

**Core technologies:**
- Python 3.10+ (MCP server): MCP protocol implementation and tool definitions — required minimum for `mcp` package
- Python 3.12.4 embedded (Fusion add-in): all CAD API calls — ships with Fusion, not configurable
- `mcp` 1.26.0 SDK with bundled FastMCP: tool, resource, and prompt registration — do NOT switch to standalone `fastmcp` 3.x
- File-system IPC with JSON: command/response transport — proven approach, no network stack needed
- `pydantic` 2.x: parameter validation in MCP server side only — already a transitive dependency of `mcp`
- `adsk.core` + `adsk.fusion`: the entire Fusion 360 API surface — no alternative exists

### Expected Features

The project's current 39-tool MCP surface is aspirational but incomplete. The feature gap analysis reveals three tiers of work needed before expanding further.

**Must have (table stakes — close the declared-but-broken gap):**
- All 30 missing add-in handlers for already-declared MCP tools (draw_line, draw_arc, chamfer, shell, patterns, mirror, components, joints, export, etc.) — users discover these and get "Unknown tool" errors
- Fix fillet edge parameter (currently ignored), extrude profile_index/taper_angle (ignored), revolve axis (hardcoded Y), create_sketch offset (ignored)
- Fix all bare `except: pass` blocks — silent failure is worse than visible errors
- `get_body_info` with edge/face enumeration — required for selective operations on geometry

**Should have (differentiated capabilities):**
- `create_parameter` / `set_parameter` using UserParameters API — enables true parametric workflows, the killer feature competitors lack
- MCP Resource endpoints serving API docs and workflow guides — improves AI self-teaching and correct tool use
- `draw_spline`, `draw_ellipse`, `draw_slot`, `offset_curves`, `draw_text` — sketch completeness
- `sweep`, `loft`, `hole`, `thread`, `construction_plane` — advanced 3D modeling operations
- `capture_screenshot` — visual feedback without switching to Fusion UI

**Defer (v2+):**
- Sketch constraints and dimensions — AI can place geometry precisely by coordinates; constraints are only needed for parametric iteration
- Timeline manipulation (`get_timeline`, `edit_at_timeline`) — powerful but complex
- Sheet metal, T-spline/form, CAM, FEA, rendering — explicitly out of scope per PROJECT.md

### Architecture Approach

The recommended architecture keeps the current two-process file-IPC model but restructures the add-in's internal organization for scale. The MCP server side is already well-structured (one decorated function per tool); the scaling problem is in the add-in's monolithic dispatcher. The solution is domain-grouped handler modules (`sketch_handlers.py`, `feature_handlers.py`, `assembly_handlers.py`, `query_handlers.py`, `utility_handlers.py`) each exporting a `HANDLERS` dict, merged into a single `TOOL_REGISTRY` at startup. The router becomes a trivial dict lookup. Fusion's CustomEvent pattern must wrap all API calls to fix the threading violation.

The MCP protocol's three primitives should all be used: Tools for callable operations (60-80 target), Resources for reference documentation and workflow guides (10-15), and Prompts for workflow templates (5-10). This three-layer discoverability model is what differentiates a high-quality MCP server from a simple tool collection.

**Major components:**
1. MCP Server — Tool Layer: Tool signatures, docstrings, Pydantic validation, IPC forwarding
2. MCP Server — Resource/Prompt Layer: API reference docs, coordinate guides, workflow templates (server-side only, no IPC)
3. MCP Server — IPC Bridge: `send_fusion_command()` — serialize, write, poll, deserialize
4. Fusion Add-in — Command Router: `execute_command()` via TOOL_REGISTRY dict lookup, CustomEvent-dispatched to main thread
5. Fusion Add-in — Domain Handler Modules: sketch, feature, assembly, query, utility — each isolated from the others

### Critical Pitfalls

1. **Threading violation (Fusion API from worker thread)** — The current monitor thread calls Fusion API directly, which can silently crash Fusion. Fix: use `app.registerCustomEvent()` so the worker thread fires events and a main-thread handler executes API calls. This is the highest-severity defect and must be fixed before any new handlers are added.

2. **Bare exception swallowing (`except: pass`)** — At least 4 locations in FusionMCP.py silently swallow errors, making the MCP server time out with "Is Fusion running?" instead of showing the real error. Fix: replace all with `except Exception as e:` and write error response files with `str(e)` and `traceback.format_exc()`.

3. **Face/edge index instability after geometry operations** — Edge and face indices shift after any geometry-modifying operation (fillet, chamfer, shell, extrude, boolean). Storing an index from `get_body_info()` and using it later operates on the wrong face. Fix: build semantic face selection helpers (`find_face_by_position("top")`) that identify faces by geometric properties rather than indices; always re-query before selective operations.

4. **XZ plane Y-axis inversion** — Sketch Y on the XZ plane maps to World -Z (confirmed by Autodesk engineering as intentional). This has already caused multiple documented errors. Fix: encapsulate the negation in the add-in's sketch handlers; tools accept world coordinates and internally apply the transformation.

5. **Server-addin tool mismatch** — 30 of 39 declared MCP tools have no add-in handler. Fix: close the gap entirely in Phase 1, or implement a startup handshake where the add-in declares its supported tool list and the MCP server only registers those.

## Implications for Roadmap

Based on the combined research, the dependency structure is clear and non-negotiable: infrastructure must precede handlers, sketch tools precede 3D features, 3D features precede assembly tools, and discoverability features come last. The following phase structure reflects both the feature dependency graph from FEATURES.md and the build order validated by ARCHITECTURE.md and PITFALLS.md.

### Phase 1: Foundation and Infrastructure

**Rationale:** Five critical defects (threading violation, bare exceptions, tool mismatch, face index instability, XZ coordinate inversion) undermine every subsequent feature. Building new handlers on the current broken foundation guarantees those handlers inherit the same defects. This phase has no new user-visible features — it is entirely stabilization and restructuring, but it is what makes all later phases viable.

**Delivers:** A reliable, debuggable add-in that correctly handles all 39 declared tools or clearly reports "not yet implemented"; threading-safe API execution; correct coordinate handling for all sketch planes; semantic face/edge selection foundation.

**Addresses:**
- Restructure add-in into domain handler modules with dict-based dispatch
- Implement CustomEvent pattern to fix threading violation
- Replace all bare `except: pass` with proper error propagation
- Build coordinate transformation layer (XZ plane inversion)
- Build face/edge semantic selection helpers
- Close the 30-tool gap: implement all missing handlers for already-declared MCP tools (as stubs that return correct errors, or full implementations where straightforward)
- Fix bugs in existing 9 handlers (fillet edges, extrude profile_index/taper_angle, revolve axis, create_sketch offset)

**Avoids:** Threading crash (Pitfall 1), silent error swallowing (Pitfall 5), Unknown tool errors (Pitfall 6), XZ inversion bugs (Pitfall 4), file path traversal (security)

### Phase 2: Sketch Completeness

**Rationale:** Sketches are the prerequisite for all 3D features. Users cannot create sweep paths, loft profiles, or complex geometry without a complete sketch toolkit. This phase builds the sketch layer to a point where advanced 3D operations become possible.

**Delivers:** Full sketch primitive set; constraint and dimension support; construction geometry tools; SVG import; project geometry.

**Addresses:** `draw_spline`, `draw_ellipse`, `draw_slot`, `draw_point`, `offset_curves`, `draw_text`, `set_construction`, `project_geometry`, `import_svg`; `add_dimension` (distance, diameter, angular); geometric constraints (horizontal, vertical, perpendicular, parallel, tangent, coincident, concentric, equal, symmetric)

**Avoids:** Profile index non-determinism (Pitfall 3) — implement profile selection by area/centroid before this phase ships

### Phase 3: 3D Feature Expansion

**Rationale:** With a complete sketch layer, the full range of 3D modeling operations becomes available. Sweep, loft, hole, and thread are high-demand features; construction planes are required infrastructure for lofts.

**Delivers:** Sweep, loft, hole, thread, construction planes/axes/points; rib, web, coil; split body/face; scale; move feature.

**Addresses:** All Tier 3 features from FEATURES.md; construction geometry infrastructure; advanced feature handlers

**Avoids:** Pattern count validation (warn if >100 instances); timeline grouping for batch operations (implement undo transaction groups)

### Phase 4: Assembly Tools

**Rationale:** Assembly operations depend on having solid bodies to work with (produced by Phases 1-3). Components, joints, and motion require the most complex Fusion API usage and the active component context fix (currently hardcoded to rootComp).

**Delivers:** Full component management (create, list, delete, move, rotate); all joint types (revolute, slider, cylindrical, pin-slot, planar, ball, rigid); joint motion driving; interference checking.

**Addresses:** Fix hardcoded `rootComp` — resolve active component context; all assembly-layer features from FEATURES.md

**Avoids:** Component context pitfall (Pitfall — hardcoded rootComp breaks nested component operations)

### Phase 5: Parametric and Discoverability

**Rationale:** With a complete, stable tool set, the highest-value differentiators become viable: parametric design via UserParameters, visual feedback via screenshot capture, and the MCP Resource/Prompt layer that enables AI self-teaching.

**Delivers:** `create_parameter` / `set_parameter` via UserParameters API; `capture_screenshot`; `section_analysis`; `mass_properties`; MCP Resources (tool reference per domain, coordinate system guide, workflow guides); MCP Prompts (common shapes, assembly patterns, workflow sequences); `set_appearance`.

**Addresses:** Differentiator features from FEATURES.md; all three MCP primitive types fully utilized; AI discoverability layer complete

**Avoids:** Dynamic tool registration anti-pattern — write each resource and prompt with hand-crafted content

### Phase Ordering Rationale

- Phase 1 must be first because the threading violation can silently corrupt geometry and mask bugs in every subsequent handler. Building on a broken foundation wastes all later effort.
- Phase 2 (sketches) must precede Phase 3 (3D features) because sweep and loft require path/profile sketches that don't exist without a complete sketch toolkit.
- Phase 3 (3D features) must precede Phase 4 (assemblies) because assembly operations need solid bodies to work with, and joint workflows require fully-formed components.
- Phase 5 (parametric and discoverability) comes last because MCP Resources should document the final, stable tool inventory — writing them before the tool set is stable wastes effort.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 1:** CustomEvent threading pattern — requires careful implementation against official Autodesk samples; test thoroughly before building other handlers on top of it
- **Phase 3:** Loft and sweep with guide rails — complex API surface; Autodesk samples exist but parameterization for AI-driven use requires careful design
- **Phase 4:** Joint types (cylindrical, pin-slot, planar, ball) — less commonly documented than revolute/slider; verify API behavior against Fusion samples before committing to implementation

Phases with standard patterns (lower research need):

- **Phase 2:** Sketch primitives are well-documented in Autodesk API reference with consistent patterns across all curve types
- **Phase 5:** UserParameters API is straightforward; MCP Resource/Prompt patterns are well-documented in FastMCP docs

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technology choices verified against official sources; two-runtime constraint is well-understood |
| Features | HIGH | Feature gap identified via direct code analysis; Fusion 360 API coverage verified against official docs |
| Architecture | HIGH | Patterns sourced from Autodesk official docs, Block engineering blog, and working reference implementations |
| Pitfalls | HIGH | Threading violation confirmed by official Autodesk docs; XZ inversion confirmed by Autodesk engineering; other pitfalls verified by direct code review of FusionMCP.py |

**Overall confidence:** HIGH

### Gaps to Address

- **Batch error boundaries:** How to handle partial batch failures cleanly (return per-command results vs. fail entire batch) needs a design decision before Phase 1 ships
- **Active component context resolution:** The correct Fusion API pattern for resolving the active edit context (vs. always using rootComp) needs verification against Autodesk docs during Phase 4 planning
- **Profile selection heuristics:** The best strategy for AI-friendly profile selection in multi-region sketches (by area, by position, by sketch order) needs empirical testing during Phase 2
- **CustomEvent response handoff:** The exact threading pattern for the worker thread to receive results from the main-thread CustomEvent handler needs prototype validation before Phase 1 commits to it

## Sources

### Primary (HIGH confidence)

- [Autodesk Fusion 360 API Reference](http://autodeskfusion360.github.io/) — full API surface, feature types, sketch objects
- [Autodesk: Working in a Separate Thread](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Threading_UM.htm) — CustomEvent threading requirements
- [Autodesk: Custom Event Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomEventSample_Sample.htm) — reference implementation
- [Autodesk Forum: XZ Plane Inversion](https://forums.autodesk.com/t5/fusion-support-forum/sketch-on-xz-plane-shows-z-positive-downwards-left-handed-coord/td-p/11675127) — confirmed by Autodesk engineering
- [mcp on PyPI v1.26.0](https://pypi.org/project/mcp/) — SDK version and bundled FastMCP
- [Block's Playbook for Designing MCP Servers](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers) — tool consolidation and count guidelines
- Project codebase: `fusion-addin/FusionMCP.py`, `mcp-server/fusion360_mcp_server.py` — direct code review
- Project docs: `docs/KNOWN_ISSUES.md`, `docs/SPATIAL_AWARENESS.md` — empirically verified error cases

### Secondary (MEDIUM confidence)

- [AuraFriday Fusion-360-MCP-Server](https://github.com/AuraFriday/Fusion-360-MCP-Server) — reference architecture for file-IPC approach
- [Autodesk Forum: How Profiles in Sketch are Indexed](https://forums.autodesk.com/t5/fusion-360-api-and-scripts/how-profiles-in-sketch-are-index/td-p/11895478) — profile index non-determinism
- [FastMCP Resources Documentation](https://gofastmcp.com/servers/resources) — @mcp.resource patterns
- [FastMCP Prompts Documentation](https://gofastmcp.com/servers/prompts) — @mcp.prompt patterns

### Tertiary (MEDIUM-LOW confidence)

- [9 MCP Servers for CAD](https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai/) — market landscape survey

---
*Research completed: 2026-03-13*
*Ready for roadmap: yes*
