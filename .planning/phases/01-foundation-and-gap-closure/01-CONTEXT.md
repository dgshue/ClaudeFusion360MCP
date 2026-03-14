# Phase 1: Foundation and Gap Closure - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the broken foundation (threading violations, error swallowing, coordinate bugs) and implement all 30 missing add-in handlers so every currently-declared MCP tool executes without errors. No new tools are added — only handlers for tools already defined in the MCP server.

</domain>

<decisions>
## Implementation Decisions

### Error reporting style
- Verbose error messages with hints: include what went wrong, why, and a suggested fix
- Include call context in errors: tool name and parameters that caused the failure
- Always wrap Fusion API exceptions into user-friendly messages — never expose raw Python tracebacks or adsk error codes
- Batch operations stop on first error and return partial results from successful commands

### Edge/face selection UX
- Support both semantic descriptions AND numeric indices for selecting edges and faces
- Position-based semantic selectors: top_face, bottom_face, left_edge, longest_edge, smallest_face, etc.
- When a semantic selector matches multiple items, apply the operation to all matches (don't error)
- get_body_info auto-labels edges and faces with semantic names alongside indices (e.g., "Face 0 (top, planar, 25cm²)")

### Coordinate behavior
- Silently correct XZ plane Y-axis inversion so user input matches world-space intuition
- Coordinate correction applies to sketch operations on XZ plane only — 3D operations (move_component, rotate_component) use standard Fusion coordinates
- Tool responses that return coordinates are also corrected to world-space for input/output consistency
- All units are centimeters, always — no unit conversion parameters (import_mesh is the one exception with its existing unit param)

### MCP client compatibility
- MCP server must work with both Claude Code and Claude Desktop — not just one client
- Ensure transport configuration supports both stdio (Claude Code) and SSE/streamable HTTP if needed

### Claude's Discretion
- Threading implementation details (CustomEvent pattern mechanics)
- Handler module organization structure (dict dispatch layout)
- Specific semantic selector vocabulary beyond the examples given
- Error message wording and hint content

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `send_fusion_command()` in MCP server: established file-IPC pattern, 50ms polling, 45s timeout — all handlers use this
- FastMCP framework (`mcp.server.fastmcp`): all tools use `@mcp.tool()` decorator pattern
- COMM_DIR (`~/fusion_mcp_comm`): shared communication directory already works

### Established Patterns
- MCP server tool pattern: `@mcp.tool()` function that calls `send_fusion_command(tool_name, params)`
- Add-in handler pattern: function taking `(design, rootComp, params)` returning `{"success": True/False, ...}`
- If-elif dispatch in `execute_command()` — will be replaced with dict dispatch per INFRA-03

### Integration Points
- `execute_command()` in FusionMCP.py: central dispatch — all new handlers register here
- `monitor_commands()` thread: needs CustomEvent rewrite for INFRA-01
- 9 existing handlers: create_sketch, draw_circle, draw_rectangle, extrude, revolve, fillet, finish_sketch, fit_view, get_design_info

</code_context>

<specifics>
## Specific Ideas

- Error messages should feel like a helpful colleague: "fillet(radius=0.5, edges=[3,7]) failed: Edge 7 does not exist. Body has 6 edges (0-5). Use get_body_info() to see available edges."
- get_body_info output should be immediately useful for selection: "Face 0 (top, planar, 25cm²), Edge 3 (top-front, 5cm)" so AI callers can use either index or semantic name
- Coordinate correction should be invisible — user draws on XZ plane and coordinates "just work" as expected in world space

</specifics>

<deferred>
## Deferred Ideas

- Smart unit interpretation (detect if user means cm or mm from context) — future phase
- MCP client compatibility is in-scope for Phase 1 (captured as a decision above)

</deferred>

---

*Phase: 01-foundation-and-gap-closure*
*Context gathered: 2026-03-13*
