# Phase 4: Assembly Enhancement - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Add 5 new mechanical joint types (rigid, cylindrical, pin-slot, planar, ball) and extend create_sketch to support face-based sketching for in-context modeling of mating features. Existing revolute/slider joints and component tools from Phase 1 remain unchanged. Extend set_joint_angle/set_joint_distance to work with multi-DOF joints.

</domain>

<decisions>
## Implementation Decisions

### Joint geometry input
- Point-based geometry for all joint types (same as existing revolute/slider pattern)
- x, y, z coordinates + axis direction via axis_x, axis_y, axis_z params
- Rigid joints default position to (0,0,0) since position is usually irrelevant for fixed connections
- Ball joints omit axis parameter entirely (spherical rotation has no meaningful axis)
- Planar joints specify plane normal via axis (e.g., Z-axis normal = XY plane sliding)
- Pin-slot joints use single axis param defining slot direction; rotation perpendicular is implicit

### Sketch-on-face UX
- Extend existing create_sketch tool with optional body_index + face params (not a separate tool)
- If face is provided, sketch on that face instead of construction plane; plane param ignored
- Face selection via body_index (int) + face (semantic selector like 'top_face' or int index) — reuses existing resolve_faces() helper
- No coordinate correction on face sketches — use Fusion's native face-local coordinate system (correction only for XZ construction plane)
- get_sketch_info reports face origin point and U/V axis directions for face-based sketches so users can orient their geometry

### Multi-DOF joint limits
- Flat params for all motion limits (consistent with existing revolute/slider pattern)
- Cylindrical: min_angle, max_angle, min_distance, max_distance (combines revolute + slider limit sets)
- Planar: all three DOF have optional limits (X slide, Y slide, rotation) — unconstrained by default
- Pin-slot: min_angle, max_angle, min_distance, max_distance (rotation + slot slide)
- Extend existing set_joint_angle to work on any joint with rotation DOF (revolute, cylindrical, pin-slot)
- Extend existing set_joint_distance to work on any joint with translation DOF (slider, cylindrical, pin-slot)
- No new drive tools needed

### Joint tool naming
- Separate tools per joint type: create_rigid_joint, create_cylindrical_joint, create_pin_slot_joint, create_planar_joint, create_ball_joint
- Consistent with existing create_revolute_joint / create_slider_joint naming pattern and Phase 2 "separate tools per type" decision

### Joint response format
- Include DOF summary in joint creation responses (e.g., "type: cylindrical, DOF: rotation + translation, limits: angle [-90, 90], distance [0, 5]")
- Consistent with Phase 1's semantic labeling pattern for AI caller clarity

### Claude's Discretion
- Internal JointGeometry creation details and API mapping
- Exact DOF summary formatting in responses
- How to handle edge cases (joints between same component, invalid axis configurations)
- Face frame calculation method for get_sketch_info

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `handlers/joint.py`: existing revolute/slider handlers with `_get_axis_direction()` helper — template for new joint handlers
- `helpers/selection.py`: `resolve_faces()` with semantic selectors (top_face, bottom_face, etc.) — reuse for sketch-on-face
- `helpers/bodies.py`: `get_occurrence()`, `get_body()` — component/body lookup with error messages
- `handlers/hole_thread.py`: already demonstrates `rootComp.sketches.add(target_face)` for face-based sketching

### Established Patterns
- Handler signature: `handler(design, rootComp, params) → {"success": True/False, ...}`
- Registration: add to HANDLER_MAP in handlers/__init__.py
- MCP tool: `@mcp.tool()` function calling `send_fusion_command(tool_name, params)`
- Joint geometry: `JointGeometry.createByPoint(occurrence, point3d)` with axis direction
- Error messages include context and suggested fixes

### Integration Points
- `handlers/__init__.py`: HANDLER_MAP — register 5 new joint handlers
- `handlers/joint.py`: add new joint handlers alongside existing revolute/slider
- `handlers/sketch.py`: extend create_sketch to accept body_index + face params
- `handlers/query.py` or sketch handler: extend get_sketch_info for face frame reporting
- `mcp-server/fusion360_mcp_server.py`: add 5 new @mcp.tool() definitions, update create_sketch params
- `set_joint_angle` / `set_joint_distance`: relax revolute/slider type check to accept multi-DOF joints

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-assembly-enhancement*
*Context gathered: 2026-03-15*
