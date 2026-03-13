# ClaudeFusion360MCP

## What This Is

A Model Context Protocol (MCP) server and Fusion 360 add-in that enables AI models to perform CAD operations in Autodesk Fusion 360. The system bridges AI agents (Claude, etc.) to Fusion 360's Python API via file-system IPC, allowing natural language-driven 3D modeling, sketching, and assembly operations. This is personal tooling for CAD automation with Claude.

## Core Value

Every MCP tool must actually work end-to-end — from tool call through add-in handler to Fusion 360 API execution — with no "Unknown tool" dead ends.

## Requirements

### Validated

- ✓ File-system IPC communication between MCP server and Fusion 360 add-in — existing
- ✓ Basic sketch creation (create_sketch, draw_circle, draw_rectangle) — existing
- ✓ Basic 3D operations (extrude, revolve, fillet) — existing
- ✓ Design info queries (get_design_info) — existing
- ✓ Batch command support — existing
- ✓ Fit view — existing

### Active

- [ ] Close the 30-tool gap: implement add-in handlers for all MCP server tools
- [ ] Full sketch API coverage (splines, constraints, dimensions, construction lines, text, offset curves)
- [ ] Complete 3D features (sweep, loft, hole, thread, rib, web, coil, emboss)
- [ ] Assembly & joints (components, rigid/revolute/slider/pin-slot joints, motion, interference)
- [ ] Rich tool descriptions with detailed docstrings, parameter docs, and usage examples
- [ ] MCP resource endpoints serving API reference docs, tutorials, and example workflows
- [ ] Higher-level workflow guides in skills (e.g., "how to create a finger joint", "design a gear")
- [ ] Tool reference skills documenting all available tools and their parameters
- [ ] Direct parallel between MCP tools and Fusion 360 API capabilities

### Out of Scope

- Manufacturing/CAM toolpaths — not needed for personal use
- Sheet metal & mesh operations — defer to future milestone
- T-splines — defer to future milestone
- Network-based communication — file IPC works fine, keep it simple
- Multi-user support — personal tooling only

## Context

- The MCP server currently defines 39 tools but the Fusion 360 add-in only implements 9 handlers
- 30 tools return "Unknown tool" errors when called
- The fillet handler ignores the `edges` parameter despite the MCP tool accepting it
- Several handlers have bare exception catching that swallows errors silently
- No version checking between server and add-in
- The project was the best available Fusion 360 MCP implementation found online
- Skills (fusion360-skill, fusion360-issues, fusion360-spatial) already exist but need alignment with expanded tool coverage
- Other AI models should be able to discover and use the tools through rich descriptions and resource endpoints

## Constraints

- **Simplicity**: Keep the architecture easy to understand and modify — no unnecessary abstractions
- **File IPC**: Keep the existing file-system communication approach
- **Fusion 360 API**: Limited to what Fusion 360's Python API (`adsk.core`, `adsk.fusion`) exposes
- **Units**: All dimensions in centimeters (Fusion 360 internal unit)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep file-system IPC | Works reliably, simple to debug, no added complexity | — Pending |
| Full sketch API coverage | Sketches are the foundation of all CAD work | — Pending |
| Tools + Resources for discoverability | Rich tool docstrings AND MCP resource endpoints for deeper reference | — Pending |
| Close existing gap before expanding | 30 broken tools need fixing before adding new ones | — Pending |
| Skip CAM/sheet metal/T-splines | Personal tooling scope — not needed now | — Pending |

---
*Last updated: 2026-03-13 after initialization*
