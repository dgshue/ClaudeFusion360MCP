# Phase 2: Sketch Completeness - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete sketch toolkit enabling complex profiles for advanced 3D features. Adds new sketch primitives (spline, ellipse, slot, point, text, offset curves), geometric constraints (9 types), parametric dimensions (3 types), construction geometry toggle, geometry projection, SVG import, and a sketch query tool. All tools follow existing patterns from Phase 1 (coordinate correction, error handling, semantic labeling).

</domain>

<decisions>
## Implementation Decisions

### Sketch entity referencing
- Index-based referencing for both curves and points (consistent with Phase 1 edge/face selection)
- Every draw command returns the index of the created entity (curve_index and point indices for endpoints)
- Existing Phase 1 draw tools (draw_line, draw_circle, draw_rectangle, draw_arc, draw_polygon) must be updated to also return entity indices
- Constraints and dimensions reference entities by numeric index
- Support point_index in addition to curve_index for constraints that need point references (coincident, symmetric)

### Two-entity constraint parameters
- Use two separate parameters: curve_index and curve_index_2 (not an array)
- Explicit positional meaning preserved for asymmetric constraints

### Dimension values
- Dimension value is required at creation time (not optional/auto-measured)
- Parametric intent: dimensions drive geometry, not document current state

### Tool granularity — separate tools per type
- Constraints: separate tools per constraint type (9 tools), not a single add_constraint
- Dimensions: separate tools per dimension type (3 tools), not a single add_dimension
- Primitives: individual tools per primitive (9 tools), consistent with existing draw_line, draw_circle pattern

### Tool naming convention
- Constraint tools: constrain_horizontal, constrain_vertical, constrain_perpendicular, constrain_parallel, constrain_tangent, constrain_coincident, constrain_concentric, constrain_equal, constrain_symmetric
- Dimension tools: dimension_distance, dimension_radial, dimension_angular
- Primitive tools: draw_spline, draw_ellipse, draw_slot, draw_point, draw_text, offset_curves, set_construction, project_geometry, import_svg

### SVG import
- Use Fusion 360's native sketch.importSVG() API (not server-side parsing)
- Accept file path only (not inline SVG content), consistent with import_mesh pattern
- Import at native SVG dimensions with optional scale parameter

### Sketch query tool (get_sketch_info)
- New query tool listing all curves, points, constraints, and dimensions in the active sketch
- Curves labeled with semantic descriptions: "Curve 0 (line, horizontal, 5cm)", "Curve 3 (arc, radius 2cm, 90deg)"
- Consistent with Phase 1's get_body_info semantic labeling pattern
- Reports overall sketch constraint status (fully constrained, under-constrained, over-constrained)
- Reports per-curve constraint state

### Claude's Discretion
- Exact semantic label vocabulary for sketch curves
- Internal sketch entity helper implementation details
- How to handle degenerate cases (zero-length lines, overlapping constraints)
- Spline fitting algorithm parameters
- Text font handling and available fonts

</decisions>

<specifics>
## Specific Ideas

- Draw command returns should mirror get_body_info's approach: both structured data and semantic labels that AI callers can use directly
- get_sketch_info should be the "go-to" tool for understanding sketch state before adding constraints/dimensions — like how get_body_info is used before fillet/chamfer

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `helpers/coordinates.py`: transform_to_sketch_coords() and transform_from_sketch_coords() — ALL new sketch handlers must use these
- `helpers/bodies.py`: get_sketch() — validates and returns active sketch by index
- `helpers/selection.py`: resolve_edges(), label_edge() — pattern to replicate for sketch curves
- `helpers/errors.py`: wrap_handler() — all new handlers auto-wrapped with error context
- `handlers/sketch.py`: existing draw_line, draw_arc, draw_polygon handlers — template for new primitives

### Established Patterns
- Handler signature: `def handler(design, rootComp, params)` returning `{"success": True/False, ...}`
- MCP tool pattern: `@mcp.tool()` function calling `send_fusion_command(tool_name, params)`
- Registration: add to HANDLER_MAP in handlers/__init__.py
- Coordinate correction applied on both input and output for XZ plane sketches
- Batch support: all tools work within batch() — stops on first error

### Integration Points
- `handlers/__init__.py`: HANDLER_MAP dict — register all new handlers
- `mcp-server/fusion360_mcp_server.py`: add @mcp.tool() definitions for each new tool
- `handlers/sketch.py`: add new primitive handlers (may need to split file given ~20 new handlers)
- New `helpers/sketch_entities.py`: curve/point indexing and semantic labeling utilities

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-sketch-completeness*
*Context gathered: 2026-03-13*
