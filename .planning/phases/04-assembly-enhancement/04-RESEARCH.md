# Phase 4: Assembly Enhancement - Research

**Researched:** 2026-03-15
**Domain:** Fusion 360 Joint API (5 joint types) + Sketch-on-Face API
**Confidence:** HIGH

## Summary

Phase 4 adds 5 new mechanical joint types (rigid, cylindrical, pin-slot, planar, ball) and extends `create_sketch` to support face-based sketching. The Fusion 360 API has well-documented, mature support for all these joint types via `JointInput.setAs*JointMotion()` methods. The existing revolute/slider joint handler pattern in `handlers/joint.py` provides a direct template -- each new joint type follows the same geometry setup (point-based via `JointGeometry.createByPoint`) with different `setAs*` calls and limit properties.

The sketch-on-face feature is straightforward: `rootComp.sketches.add(brepFace)` already works (demonstrated in `handlers/hole_thread.py`). The main additions are extending the `create_sketch` MCP tool to accept `body_index` + `face` params and enhancing `get_sketch_info` to report face-local coordinate frame (origin, U/V directions) via `sketch.origin`, `sketch.xDirection`, `sketch.yDirection`.

The `set_joint_angle` and `set_joint_distance` handlers need relaxed type checking to accept multi-DOF joints (cylindrical, pin-slot) that have both rotation and translation capabilities.

**Primary recommendation:** Follow the existing revolute/slider pattern exactly. Each joint type gets a dedicated handler function in `joint.py` and a dedicated `@mcp.tool()` in the MCP server. Extend `create_sketch` handler (not a new tool) for face-based sketching.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Point-based geometry for all joint types (same as existing revolute/slider pattern)
- x, y, z coordinates + axis direction via axis_x, axis_y, axis_z params
- Rigid joints default position to (0,0,0) since position is usually irrelevant for fixed connections
- Ball joints omit axis parameter entirely (spherical rotation has no meaningful axis)
- Planar joints specify plane normal via axis (e.g., Z-axis normal = XY plane sliding)
- Pin-slot joints use single axis param defining slot direction; rotation perpendicular is implicit
- Extend existing create_sketch tool with optional body_index + face params (not a separate tool)
- If face is provided, sketch on that face instead of construction plane; plane param ignored
- Face selection via body_index (int) + face (semantic selector like 'top_face' or int index) -- reuses existing resolve_faces() helper
- No coordinate correction on face sketches -- use Fusion's native face-local coordinate system (correction only for XZ construction plane)
- get_sketch_info reports face origin point and U/V axis directions for face-based sketches so users can orient their geometry
- Flat params for all motion limits (consistent with existing revolute/slider pattern)
- Cylindrical: min_angle, max_angle, min_distance, max_distance
- Planar: all three DOF have optional limits (X slide, Y slide, rotation) -- unconstrained by default
- Pin-slot: min_angle, max_angle, min_distance, max_distance
- Extend existing set_joint_angle to work on any joint with rotation DOF (revolute, cylindrical, pin-slot)
- Extend existing set_joint_distance to work on any joint with translation DOF (slider, cylindrical, pin-slot)
- No new drive tools needed
- Separate tools per joint type: create_rigid_joint, create_cylindrical_joint, create_pin_slot_joint, create_planar_joint, create_ball_joint
- Include DOF summary in joint creation responses

### Claude's Discretion
- Internal JointGeometry creation details and API mapping
- Exact DOF summary formatting in responses
- How to handle edge cases (joints between same component, invalid axis configurations)
- Face frame calculation method for get_sketch_info

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ASSM-01 | `create_rigid_joint` tool and handler for fixed connections | `setAsRigidJointMotion()` takes no params; simplest joint type. Template from existing revolute handler. |
| ASSM-02 | `create_cylindrical_joint` tool and handler for rotation + translation | `setAsCylindricalJointMotion(rotationAxis)` with `rotationLimits` + `slideLimits` properties on CylindricalJointMotion. |
| ASSM-03 | `create_pin_slot_joint` tool and handler for pin-in-slot motion | `setAsPinSlotJointMotion(rotationAxis, slideDirection)` with two axis params; `rotationLimits` + `slideLimits`. |
| ASSM-04 | `create_planar_joint` tool and handler for planar sliding | `setAsPlanarJointMotion(normalDirection)` with `primarySlideLimits`, `secondarySlideLimits`, `rotationLimits`. |
| ASSM-05 | `create_ball_joint` tool and handler for spherical rotation | `setAsBallJointMotion(pitchDirection, yawDirection)` with `pitchLimits`, `rollLimits`, `yawLimits`. No axis param per user decision. |
| ASSM-06 | `create_sketch_on_face` tool and handler for sketching on body faces | Extend `create_sketch` handler with `body_index` + `face` params using `rootComp.sketches.add(brepFace)`. Enhance `get_sketch_info` with face frame via `sketch.origin`, `sketch.xDirection`, `sketch.yDirection`. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| adsk.fusion | Fusion 360 API | Joint creation, sketch-on-face | Only API for Fusion 360 automation |
| adsk.core | Fusion 360 API | Point3D, Vector3D, ValueInput | Core geometry types |

### Key API Objects
| Object | Purpose | Properties/Methods Used |
|--------|---------|----------------------|
| JointInput | Configure joint before creation | `setAsRigidJointMotion()`, `setAsCylindricalJointMotion(axis)`, `setAsPinSlotJointMotion(rotAxis, slideDir)`, `setAsPlanarJointMotion(normalDir)`, `setAsBallJointMotion(pitchDir, yawDir)` |
| CylindricalJointMotion | Post-creation motion config | `rotationLimits`, `slideLimits`, `rotationValue`, `slideValue` |
| PinSlotJointMotion | Post-creation motion config | `rotationLimits`, `slideLimits`, `rotationValue`, `slideValue` |
| PlanarJointMotion | Post-creation motion config | `primarySlideLimits`, `secondarySlideLimits`, `rotationLimits`, `primarySlideValue`, `secondarySlideValue`, `rotationValue` |
| BallJointMotion | Post-creation motion config | `pitchLimits`, `rollLimits`, `yawLimits`, `pitchValue`, `rollValue`, `yawValue` |
| RigidJointMotion | No motion properties | `jointType` only |
| JointLimits | Limit configuration | `isMinimumValueEnabled`, `minimumValue`, `isMaximumValueEnabled`, `maximumValue`, `isRestValueEnabled`, `restValue` |
| JointTypes enum | Type checking | `RigidJointType(0)`, `CylindricalJointType(3)`, `PinSlotJointType(4)`, `PlanarJointType(5)`, `BallJointType(6)` |
| JointDirections enum | Axis specification | `XAxisJointDirection`, `YAxisJointDirection`, `ZAxisJointDirection`, `CustomJointDirection` |
| Sketch | Face frame info | `origin` (Point3D), `xDirection` (Vector3D), `yDirection` (Vector3D) |

## Architecture Patterns

### File Modifications Required

```
fusion-addin/
  handlers/
    joint.py             # ADD: 5 new handler functions
    sketch.py            # MODIFY: create_sketch to accept body_index + face
    sketch_query.py      # MODIFY: get_sketch_info to report face frame
    __init__.py          # ADD: imports + HANDLER_MAP entries for 5 new handlers
mcp-server/
  fusion360_mcp_server.py # ADD: 5 new @mcp.tool() definitions, update create_sketch signature
```

### Pattern 1: Joint Handler (follows existing revolute/slider template)
**What:** Each joint type is a separate handler function with identical structure
**When to use:** All 5 new joint handlers
**Example:**
```python
# Source: Fusion 360 API docs + existing handlers/joint.py pattern
def create_cylindrical_joint(design, rootComp, params):
    """Create a cylindrical (rotation + translation) joint between two components."""
    if rootComp.occurrences.count < 2:
        return {"success": False, "error": "Need at least 2 components..."}

    idx1 = params.get('component1_index', 0)
    idx2 = params.get('component2_index', 1)
    occ1 = get_occurrence(rootComp, index=idx1)
    occ2 = get_occurrence(rootComp, index=idx2)

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    point = adsk.core.Point3D.create(x, y, z)

    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)

    axis_direction = _get_axis_direction(params)
    joint_input.setAsCylindricalJointMotion(axis_direction)

    joint = joints.add(joint_input)

    # Set limits
    min_angle = params.get('min_angle')
    max_angle = params.get('max_angle')
    if min_angle is not None:
        joint.jointMotion.rotationLimits.isMinimumValueEnabled = True
        joint.jointMotion.rotationLimits.minimumValue = math.radians(min_angle)
    if max_angle is not None:
        joint.jointMotion.rotationLimits.isMaximumValueEnabled = True
        joint.jointMotion.rotationLimits.maximumValue = math.radians(max_angle)

    min_distance = params.get('min_distance')
    max_distance = params.get('max_distance')
    if min_distance is not None:
        joint.jointMotion.slideLimits.isMinimumValueEnabled = True
        joint.jointMotion.slideLimits.minimumValue = min_distance
    if max_distance is not None:
        joint.jointMotion.slideLimits.isMaximumValueEnabled = True
        joint.jointMotion.slideLimits.maximumValue = max_distance

    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "cylindrical",
        "dof": "rotation + translation",
        "limits": {
            "angle": [min_angle, max_angle],
            "distance": [min_distance, max_distance]
        }
    }
```

### Pattern 2: Rigid Joint (simplest -- no axis, no limits)
**What:** Fixed connection with no degrees of freedom
**Example:**
```python
def create_rigid_joint(design, rootComp, params):
    # Same geometry setup as above...
    joint_input.setAsRigidJointMotion()  # No parameters
    joint = joints.add(joint_input)
    return {
        "success": True,
        "joint_name": joint.name,
        "joint_index": rootComp.joints.count - 1,
        "type": "rigid",
        "dof": "none (fixed)"
    }
```

### Pattern 3: Ball Joint (no axis per user decision)
**What:** Spherical rotation, omits axis params
**Example:**
```python
def create_ball_joint(design, rootComp, params):
    # Geometry setup...
    # Use default Z for pitch, X for yaw (standard orientation)
    joint_input.setAsBallJointMotion(
        adsk.fusion.JointDirections.ZAxisJointDirection,
        adsk.fusion.JointDirections.XAxisJointDirection
    )
    joint = joints.add(joint_input)
    # Ball joint has pitch/roll/yaw limits (optional)
    # ... set limits if provided ...
```

### Pattern 4: Pin-Slot Joint (two axis params)
**What:** Rotation around one axis + sliding along another
**Key difference:** `setAsPinSlotJointMotion` takes TWO axis directions (rotation axis + slide direction)
**Example:**
```python
joint_input.setAsPinSlotJointMotion(
    _get_axis_direction(params),           # rotation axis
    _get_slide_direction(params)           # slide direction - derived from axis or separate params
)
```
**Note:** Per user decision, single axis param defines slot direction; rotation is perpendicular. Implementation needs to derive the rotation axis as perpendicular to the slot axis.

### Pattern 5: Sketch-on-Face Extension
**What:** Extend create_sketch to optionally create sketch on body face
**Example:**
```python
# In handlers/sketch.py create_sketch():
body_index = params.get('body_index')
face_param = params.get('face')

if face_param is not None:
    # Face-based sketch
    body = get_body(rootComp, body_index)
    target_face = resolve_faces(body, [face_param])[0]
    sketch = rootComp.sketches.add(target_face)
    sketch.attributes.add('FusionMCP', 'base_plane', 'face')
    return {"success": True, "sketch_name": sketch.name, "plane": "face"}
else:
    # Existing construction plane logic...
```

### Pattern 6: get_sketch_info Face Frame Reporting
**What:** When sketch is on a face, report origin + U/V directions
**Example:**
```python
# In sketch_query.py get_sketch_info():
# After existing logic, add face frame info
face_frame = None
try:
    origin = sketch.origin
    x_dir = sketch.xDirection
    y_dir = sketch.yDirection
    face_frame = {
        "origin": [round(origin.x, 4), round(origin.y, 4), round(origin.z, 4)],
        "x_direction": [round(x_dir.x, 4), round(x_dir.y, 4), round(x_dir.z, 4)],
        "y_direction": [round(y_dir.x, 4), round(y_dir.y, 4), round(y_dir.z, 4)]
    }
except Exception:
    pass
# Include in response if available
```

### Pattern 7: Relaxed set_joint_angle / set_joint_distance Type Checking
**What:** Allow multi-DOF joints to be driven
**Example:**
```python
# In set_joint_angle: accept revolute, cylindrical, pin-slot
ROTATION_JOINT_TYPES = {
    adsk.fusion.JointTypes.RevoluteJointType,
    adsk.fusion.JointTypes.CylindricalJointType,
    adsk.fusion.JointTypes.PinSlotJointType,
}
if joint.jointMotion.jointType not in ROTATION_JOINT_TYPES:
    return {"success": False, "error": "...not a joint with rotation DOF..."}

joint.jointMotion.rotationValue = math.radians(angle)

# In set_joint_distance: accept slider, cylindrical, pin-slot
TRANSLATION_JOINT_TYPES = {
    adsk.fusion.JointTypes.SliderJointType,
    adsk.fusion.JointTypes.CylindricalJointType,
    adsk.fusion.JointTypes.PinSlotJointType,
}
```

### Anti-Patterns to Avoid
- **Do NOT create a separate `create_sketch_on_face` tool** -- user decided to extend existing `create_sketch` with optional params
- **Do NOT apply coordinate correction to face-based sketches** -- only XZ construction plane gets Y-axis inversion
- **Do NOT use `CustomJointDirection` for standard axis-aligned joints** -- use `XAxisJointDirection`/`YAxisJointDirection`/`ZAxisJointDirection` from `_get_axis_direction()` helper
- **Do NOT add new drive tools** -- extend existing `set_joint_angle`/`set_joint_distance` to accept multi-DOF types

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Face selection | Custom face picker | `resolve_faces()` from `helpers/selection.py` | Already handles semantic selectors and index-based selection |
| Axis direction mapping | Custom axis logic | `_get_axis_direction()` from `handlers/joint.py` | Already maps axis_x/y/z to JointDirections enum |
| Body lookup | Manual index handling | `get_body()` from `helpers/bodies.py` | Already has range validation and error messages |
| Occurrence lookup | Manual component finding | `get_occurrence()` from `helpers/bodies.py` | Already handles index/name with error messages |
| Sketch coordinate frame | Manual matrix decomposition | `sketch.origin`, `sketch.xDirection`, `sketch.yDirection` | Native Fusion API properties, already computed |

## Common Pitfalls

### Pitfall 1: Pin-Slot Axis Mapping
**What goes wrong:** User provides single axis for slot direction, but `setAsPinSlotJointMotion` requires both rotation axis and slide direction as separate params.
**Why it happens:** Per user decision, the single axis param defines slot direction and rotation is implicit (perpendicular).
**How to avoid:** Derive the rotation axis as perpendicular to the slot direction. If slot is Z, rotation axis could be X or Y. A reasonable default: choose the first axis that differs from the slot direction.
**Warning signs:** Joint created with wrong DOF directions.

### Pitfall 2: Ball Joint API Requires Pitch/Yaw Directions
**What goes wrong:** User decision says "omit axis parameter" but `setAsBallJointMotion` requires `pitchDirection` and `yawDirection`.
**Why it happens:** Ball joints need internal reference directions even though the user-facing interface hides them.
**How to avoid:** Use sensible defaults internally: `ZAxisJointDirection` for pitch, `XAxisJointDirection` for yaw. These define the measurement frame, not motion constraints.
**Warning signs:** API error on joint creation.

### Pitfall 3: Planar Joint Has Three Limit Sets
**What goes wrong:** Using flat params like `min_distance`/`max_distance` is ambiguous for planar joints which have primary slide, secondary slide, and rotation.
**Why it happens:** Planar joints have 3 DOF while cylindrical/pin-slot have 2.
**How to avoid:** Use distinct param names: `min_primary_slide`, `max_primary_slide`, `min_secondary_slide`, `max_secondary_slide`, `min_angle`, `max_angle`. Per user decision, all unconstrained by default.
**Warning signs:** Limits applied to wrong DOF.

### Pitfall 4: Planar Joint Drive Values
**What goes wrong:** `set_joint_distance` can't drive planar joints because they have `primarySlideValue` and `secondarySlideValue`, not a single `slideValue`.
**Why it happens:** Planar joints have 2 translation DOF accessed differently from single-DOF joints.
**How to avoid:** Planar joints are NOT included in the `set_joint_distance` type set. They have rotation (driveable by `set_joint_angle` after checking `PlanarJointType`) but their slide values need separate handling if needed. Per user decision, no new drive tools are needed, so planar slide driving may be out of scope for this phase.
**Warning signs:** Runtime error accessing `.slideValue` on PlanarJointMotion (it has `.primarySlideValue` and `.secondarySlideValue` instead).

### Pitfall 5: Face-Based Sketch Coordinate Correction
**What goes wrong:** Applying XZ plane Y-axis inversion to face-based sketches.
**Why it happens:** Existing `transform_to_sketch_coords` checks for XZ base_plane attribute and inverts Y.
**How to avoid:** Store `'face'` as the base_plane attribute value. The coordinate helper already only corrects when base_plane is `'XZ'`, so face sketches will pass through unmodified.
**Warning signs:** Mirrored geometry on face sketches.

### Pitfall 6: Rigid Joint Default Position
**What goes wrong:** Requiring x/y/z position for rigid joints when it's irrelevant.
**Why it happens:** All other joints use position for the joint origin point.
**How to avoid:** Default x/y/z to (0,0,0) for rigid joints. The MCP tool should document that position is optional for rigid connections.

## Code Examples

### Complete Joint Motion Type Map
```python
# Source: Fusion 360 API official docs
# All JointTypes enum values:
# adsk.fusion.JointTypes.RigidJointType       = 0
# adsk.fusion.JointTypes.RevoluteJointType     = 1
# adsk.fusion.JointTypes.SliderJointType       = 2
# adsk.fusion.JointTypes.CylindricalJointType  = 3
# adsk.fusion.JointTypes.PinSlotJointType      = 4
# adsk.fusion.JointTypes.PlanarJointType       = 5
# adsk.fusion.JointTypes.BallJointType         = 6
```

### JointInput Setup Methods
```python
# Source: Fusion 360 API official docs
# Rigid: no params
joint_input.setAsRigidJointMotion()

# Cylindrical: one axis (rotation axis = slide axis)
joint_input.setAsCylindricalJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)

# Pin-slot: two axes (rotation axis + slide direction)
joint_input.setAsPinSlotJointMotion(
    adsk.fusion.JointDirections.ZAxisJointDirection,  # rotation
    adsk.fusion.JointDirections.XAxisJointDirection   # slide
)

# Planar: one axis (normal direction)
joint_input.setAsPlanarJointMotion(adsk.fusion.JointDirections.YAxisJointDirection)

# Ball: two directions (pitch + yaw measurement frames)
joint_input.setAsBallJointMotion(
    adsk.fusion.JointDirections.ZAxisJointDirection,  # pitch
    adsk.fusion.JointDirections.XAxisJointDirection   # yaw
)
```

### Sketch on Face (proven pattern from hole_thread.py)
```python
# Source: fusion-addin/handlers/hole_thread.py line 33
sketch = rootComp.sketches.add(target_face)  # BRepFace accepted directly
```

### Sketch Coordinate Frame Properties
```python
# Source: Fusion 360 API docs - Sketch object properties
origin = sketch.origin        # Point3D in model space
x_dir = sketch.xDirection     # Vector3D - U direction of sketch
y_dir = sketch.yDirection     # Vector3D - V direction of sketch
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single revolute/slider type check in set_joint_angle/distance | Accept set of joint types with rotation/translation DOF | Phase 4 | Enables driving multi-DOF joints |
| create_sketch only accepts construction planes | create_sketch accepts face OR plane | Phase 4 | Enables in-context modeling on body faces |

## Open Questions

1. **Planar joint drive values**
   - What we know: Planar joints have `primarySlideValue` and `secondarySlideValue` (two translation DOF), not a single `slideValue`
   - What's unclear: Should `set_joint_distance` attempt to drive planar joints? If so, which axis?
   - Recommendation: Exclude planar joints from `set_joint_distance` per user decision of "no new drive tools." Include planar in `set_joint_angle` (it has `rotationValue`). Document this limitation.

2. **Pin-slot rotation axis derivation**
   - What we know: User provides single axis param for slot direction. API requires separate rotation axis.
   - What's unclear: Which perpendicular axis to choose when multiple are available.
   - Recommendation: If slot is along Z, use X for rotation. If slot is along X, use Z. If slot is along Y, use Z. Use the first non-matching standard axis. This gives predictable behavior.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual UAT in Fusion 360 (no automated test infrastructure) |
| Config file | none |
| Quick run command | Manual: create components, apply joints, verify motion |
| Full suite command | Manual: end-to-end assembly workflow test |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ASSM-01 | Rigid joint between 2 components | manual | N/A - test in Fusion 360 UI | N/A |
| ASSM-02 | Cylindrical joint with rotation + translation | manual | N/A - test in Fusion 360 UI | N/A |
| ASSM-03 | Pin-slot joint with pin + slot motion | manual | N/A - test in Fusion 360 UI | N/A |
| ASSM-04 | Planar joint with 2D sliding + rotation | manual | N/A - test in Fusion 360 UI | N/A |
| ASSM-05 | Ball joint with spherical rotation | manual | N/A - test in Fusion 360 UI | N/A |
| ASSM-06 | Sketch on body face, get_sketch_info reports frame | manual | N/A - test in Fusion 360 UI | N/A |

### Sampling Rate
- **Per task commit:** Manual spot-check: create joint, verify in Fusion 360
- **Per wave merge:** Run full assembly workflow (create components, joints, drive motion)
- **Phase gate:** Build multi-component hinge assembly using all joint types

### Wave 0 Gaps
None -- this project uses manual testing in Fusion 360 (Fusion API cannot be unit tested outside the application).

## Sources

### Primary (HIGH confidence)
- [Fusion 360 API - CylindricalJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CylindricalJointMotion.htm) - all properties verified
- [Fusion 360 API - PlanarJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PlanarJointMotion.htm) - 3 DOF properties verified
- [Fusion 360 API - PinSlotJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PinSlotJointMotion.htm) - rotation + slide properties verified
- [Fusion 360 API - BallJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BallJointMotion.htm) - pitch/roll/yaw properties verified
- [Fusion 360 API - JointTypes enum](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointTypes.htm) - all 8 values verified
- [Fusion 360 API - JointInput.setAsRigidJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointInput_setAsRigidJointMotion.htm) - no params, returns bool
- [Fusion 360 API - JointInput.setAsCylindricalJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointInput_setAsCylindricalJointMotion.htm) - rotationAxis param
- [Fusion 360 API - JointInput.setAsPinSlotJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointInput_setAsPinSlotJointMotion.htm) - rotationAxis + slideDirection
- [Fusion 360 API - JointInput.setAsPlanarJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointInput_setAsPlanarJointMotion.htm) - normalDirection param
- [Fusion 360 API - JointInput.setAsBallJointMotion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointInput_setAsBallJointMotion.htm) - pitchDirection + yawDirection
- [Fusion 360 API - Joint Object](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Joint.htm) - all setAs* methods listed
- [Fusion 360 API - Sketches.add](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketches_add.htm) - accepts "construction plane or planar face"
- [Fusion 360 API - Sketch.origin/xDirection/yDirection](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_origin.htm) - face frame properties
- Existing codebase: `handlers/joint.py`, `handlers/hole_thread.py` (line 33), `helpers/selection.py` - proven patterns

### Secondary (MEDIUM confidence)
- [CylindricalJointMotion API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CylindricalJointMotionSample_Sample.htm) - working code sample
- [PlanarJointMotion API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PlanarJointMotionSample_Sample.htm) - working code sample
- [PinSlotJointMotion API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PinSlotJointMotionSample_Sample.htm) - working code sample

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All API methods verified against official Autodesk documentation with exact signatures
- Architecture: HIGH - Follows proven existing patterns (revolute/slider handlers, hole_thread face sketching)
- Pitfalls: HIGH - Planar 3-DOF and pin-slot dual-axis documented from official API properties lists

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable Fusion 360 API, slow-moving)
