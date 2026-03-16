# Phase 5: Parametric, Timeline, and Discoverability - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Add parametric design support (named user parameters with expressions), timeline navigation (view history, rollback, named markers), and AI discoverability (MCP resource endpoints, prompt templates, rich docstrings). This is the final v1 phase — after this, any AI model connecting via MCP should be able to discover and use the full tool set without external documentation.

</domain>

<decisions>
## Implementation Decisions

### Parametric parameters
- create_parameter accepts name + expression + unit (e.g., `create_parameter('width', '5', 'cm')`)
- Expressions can reference other parameters: `create_parameter('height', 'width * 2', 'cm')`
- set_parameter also accepts expressions (not just numeric values): `set_parameter('height', '2 * width')`
- Tool responses that return dimensions should show parameter linkage when driven by parameters: "distance: 5.0 (from 'height')"
- Consistent with Phase 2's separate-tools-per-type decision: create_parameter and set_parameter as distinct tools

### Timeline navigation
- get_timeline returns feature list with indices: index, feature type, name, status (healthy/error/suppressed)
- edit_at_timeline moves the timeline marker and warns about scope: "Features after position N are now suppressed. Use edit_at_timeline(-1) to return to end."
- Add a new create_marker tool for user-named timeline snapshots (e.g., `create_marker('before_fillets')`)
- Markers are stored in-memory by the add-in (not persistent across Fusion sessions)
- undo_to_marker rolls back to a named marker's timeline position
- This means TIME-03 requires create_marker as a supporting tool (not in original requirements but needed for markers to be meaningful)

### MCP resource organization
- Per-domain category resources: 'tools/sketch', 'tools/3d-features', 'tools/assembly', 'tools/utility', 'guides/coordinates', 'guides/workflows'
- Matches the handler module structure in the add-in
- Resource content lives in separate markdown files (in a resources/ or docs/ directory), loaded by MCP server at startup
- Not inline Python strings — easy to edit and version-control independently

### Coordinate system guide (DISC-02)
- Covers: all units in cm, the three planes (XY/XZ/YZ), XZ Y-axis inversion behavior
- Documents when correction applies (XZ construction plane sketches) vs when it doesn't (face sketches, 3D operations)
- Includes common mistakes with examples

### Workflow guides (DISC-03)
- Higher-level patterns with reasoning, not exact tool sequences
- E.g., "Enclosure pattern: sketch outer profile -> extrude -> shell (remove top face) -> fillet edges. Shell before fillet because..."
- Teaches AI WHY so it can adapt to variations

### Prompt templates (DISC-04)
- Core set for v1: box/enclosure, cylinder, gear (spur), simple hinge assembly
- Guided workflow with parameters: template takes dimensions as arguments, returns structured prompt with specific tool calls
- Templates reference specific tool names (not just intent): "Step 1: Use create_sketch(plane='XY')..."
- Each template produces a complete step-by-step guide the AI executes

### Rich docstrings (DISC-05)
- Every tool gets: 1-2 sentence description, typed parameter list with descriptions, 2-3 usage examples
- Model after create_sketch's current docstring (the best one in the codebase) applied to all 50+ tools
- This is a bulk update across the entire MCP server file

### Claude's Discretion
- Exact resource file directory structure (resources/ vs docs/)
- FastMCP resource/prompt API patterns and registration approach
- Marker storage implementation details in the add-in
- How to handle parameter deletion or renaming
- Exact workflow guide content for each pattern
- How deeply to document each tool's edge cases in docstrings

</decisions>

<specifics>
## Specific Ideas

- create_sketch's current docstring is the gold standard — it has description, typed Args section, and usage Examples. All 50+ tools should match this format.
- The parameter linkage in responses ("distance: 5.0 (from 'height')") follows the Phase 1 semantic labeling pattern — structured data + human-readable context for AI callers.
- Workflow guides should feel like a senior engineer explaining the approach, not a script to blindly follow.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `send_fusion_command()`: all new handlers (parameter, timeline, marker) use the same file-IPC pattern
- `handlers/__init__.py` HANDLER_MAP: register new handlers alongside existing ones
- `@mcp.tool()` decorator pattern: all new tools follow this
- `create_sketch` docstring format: template for DISC-05 bulk docstring update

### Established Patterns
- Handler signature: `handler(design, rootComp, params) -> {"success": True/False, ...}`
- MCP tool pattern: `@mcp.tool()` function calling `send_fusion_command(tool_name, params)`
- No existing MCP resources or prompts — this is greenfield for DISC-01 through DISC-04
- No existing UserParameter or timeline usage in the codebase — greenfield for PARAM and TIME requirements

### Integration Points
- `fusion-addin/handlers/`: new handler modules for parameter and timeline operations
- `mcp-server/fusion360_mcp_server.py`: new @mcp.tool() definitions + @mcp.resource() + @mcp.prompt() registrations
- New `mcp-server/resources/` directory for markdown resource content files
- All 50+ existing @mcp.tool() functions need docstring updates for DISC-05

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-parametric-timeline-and-discoverability*
*Context gathered: 2026-03-15*
