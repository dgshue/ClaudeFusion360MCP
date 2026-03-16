# ClaudeFusion360MCP

## What This Is

A Model Context Protocol (MCP) server and Fusion 360 add-in that enables AI models to perform comprehensive CAD operations in Autodesk Fusion 360. The system bridges AI agents (Claude, etc.) to Fusion 360's Python API via file-system IPC, providing 79 tools covering sketching, 3D features, assemblies, parametric design, and timeline navigation. AI models can self-discover all capabilities through MCP resource endpoints, prompt templates, and rich docstrings.

## Core Value

Every MCP tool must actually work end-to-end — from tool call through add-in handler to Fusion 360 API execution — with no "Unknown tool" dead ends.

## Requirements

### Validated

- ✓ File-system IPC communication between MCP server and Fusion 360 add-in — v1.0
- ✓ CustomEvent threading pattern — all Fusion API calls on main thread — v1.0
- ✓ Dict-based dispatch with domain handler modules (sketch, feature, assembly, query, utility, parametric, timeline) — v1.0
- ✓ Coordinate transformation layer for XZ plane Y-axis inversion — v1.0
- ✓ Face/edge semantic selection by position/properties — v1.0
- ✓ Complete sketch toolkit: 14 draw tools, 9 constraints, 3 dimensions, SVG import — v1.0
- ✓ Full 3D features: extrude, revolve, fillet, chamfer, shell, draft, patterns, mirror, combine, sweep, loft, hole, thread — v1.0
- ✓ Construction geometry: offset/angled planes, reference axes, reference points — v1.0
- ✓ Assembly: 7 joint types, face-based sketching, component management, interference detection — v1.0
- ✓ Parametric design: named user parameters with expression support — v1.0
- ✓ Timeline navigation: history view, rollback editing, named markers — v1.0
- ✓ Export/import: STL, STEP, 3MF export; mesh import — v1.0
- ✓ AI discoverability: 6 MCP resource endpoints, 4 prompt templates, 79 enriched tool docstrings — v1.0

### Active

- [ ] capture_screenshot for visual feedback
- [ ] set_appearance for materials/colors
- [ ] section_analysis for cross-section views
- [ ] mass_properties for center of mass and moments of inertia
- [ ] create_named_selection for reusable edge/face selections

### Out of Scope

- CAM/toolpath generation — massive API surface (280+ classes); use dedicated CAM software
- Sheet metal features — specialized domain with complex rules; defer to future milestone
- T-spline/form editing — different modeling paradigm; rarely needed for functional parts
- Mesh editing operations — use dedicated mesh tools; import meshes as-is
- Simulation/FEA — separate domain; use Fusion's built-in simulation
- Rendering — not part of modeling workflow; use Fusion's render workspace
- Multi-document management — adds state complexity; user manages documents
- Arbitrary Python execution — security risk; expose specific, tested operations
- Network-based communication — file IPC works reliably; keep it simple

## Context

- Shipped v1.0 with 6,846 lines of Python across 79 MCP tools
- Tech stack: Python MCP server (system Python 3.10+) + Fusion 360 add-in (embedded Python 3.12.4) connected via file-system IPC
- All tools tested through MCP protocol and verified against Fusion 360 API
- This is NOT our own repo — will need to fork and repoint remote at some point
- Skills (fusion360-skill, fusion360-issues, fusion360-spatial) exist and are aligned with the full tool set

## Constraints

- **Simplicity**: Keep the architecture easy to understand and modify — no unnecessary abstractions
- **File IPC**: Keep the existing file-system communication approach
- **Fusion 360 API**: Limited to what Fusion 360's Python API (`adsk.core`, `adsk.fusion`) exposes
- **Units**: All dimensions in centimeters (Fusion 360 internal unit)
- **Two-runtime isolation**: MCP server (system Python 3.10+) and add-in (embedded Python 3.12.4) cannot share libraries

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep file-system IPC | Works reliably, simple to debug, no added complexity | ✓ Good |
| CustomEvent threading pattern | Fix threading violation before adding handlers | ✓ Good — zero crashes in extended sessions |
| Dict dispatch + handler modules | Scale add-in from 9 to 79 handlers cleanly | ✓ Good — clean separation by domain |
| Full sketch API coverage | Sketches are the foundation of all CAD work | ✓ Good — enables sweep paths, loft profiles, complex geometry |
| Tools + Resources for discoverability | Rich tool docstrings AND MCP resource endpoints for deeper reference | ✓ Good — AI models can self-discover |
| Close existing gap before expanding | 30 broken tools need fixing before adding new ones | ✓ Good — stable foundation first |
| Skip CAM/sheet metal/T-splines | Personal tooling scope — not needed now | — Pending |
| Timeline in v1 | Undo/rollback is essential for iterative design workflow | ✓ Good — markers enable checkpointing |

---
*Last updated: 2026-03-16 after v1.0 milestone*
