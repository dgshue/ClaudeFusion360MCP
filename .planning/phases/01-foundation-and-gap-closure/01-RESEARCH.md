# Phase 1: Foundation and Gap Closure - Research

**Researched:** 2026-03-13
**Domain:** Fusion 360 Python API (adsk.core, adsk.fusion), MCP server architecture, file-IPC threading
**Confidence:** HIGH

## Summary

Phase 1 transforms a half-working Fusion 360 MCP bridge (9 of 39 handlers implemented) into a fully functional system. The work divides into three domains: (1) infrastructure fixes -- CustomEvent threading, error handling, module restructuring, coordinate correction, semantic selection; (2) bug fixes to 5 existing handlers; and (3) implementing 30 missing handlers across sketch, feature, query, component, joint, utility, and I/O categories.

The critical infrastructure piece is the CustomEvent threading pattern. The current add-in calls Fusion API directly from a background thread, which is a threading violation that can cause silent crashes. Fusion 360's official pattern uses `app.registerCustomEvent()` + `app.fireCustomEvent()` to marshal work from a worker thread to the main thread via an event queue. This pattern is well-documented with official samples and must be the first thing implemented.

All 30 missing handlers have corresponding Fusion 360 API methods that are well-documented. The API surface needed (extrude features, shell, draft, patterns, mirrors, combine, joints, export manager, mesh bodies) is mature and stable. The coordinate correction for XZ plane sketches requires understanding that all sketches use a local X/Y coordinate system regardless of their 3D orientation -- on the XZ plane, the sketch Y axis maps to the negative world Z axis, requiring coordinate swapping and sign correction.

**Primary recommendation:** Implement CustomEvent threading and dict dispatch first (INFRA-01, INFRA-03), then layer error handling (INFRA-02) and coordinate correction (INFRA-04) as cross-cutting concerns, then implement handlers in domain batches (sketch, feature, query, component, joint, utility, I/O).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Error reporting style: Verbose error messages with hints -- include what went wrong, why, and a suggested fix. Include call context in errors: tool name and parameters that caused the failure. Always wrap Fusion API exceptions into user-friendly messages -- never expose raw Python tracebacks or adsk error codes. Batch operations stop on first error and return partial results from successful commands.
- Edge/face selection UX: Support both semantic descriptions AND numeric indices for selecting edges and faces. Position-based semantic selectors: top_face, bottom_face, left_edge, longest_edge, smallest_face, etc. When a semantic selector matches multiple items, apply the operation to all matches (don't error). get_body_info auto-labels edges and faces with semantic names alongside indices (e.g., "Face 0 (top, planar, 25cm2)").
- Coordinate behavior: Silently correct XZ plane Y-axis inversion so user input matches world-space intuition. Coordinate correction applies to sketch operations on XZ plane only -- 3D operations (move_component, rotate_component) use standard Fusion coordinates. Tool responses that return coordinates are also corrected to world-space for input/output consistency. All units are centimeters, always -- no unit conversion parameters (import_mesh is the one exception with its existing unit param).

### Claude's Discretion
- Threading implementation details (CustomEvent pattern mechanics)
- Handler module organization structure (dict dispatch layout)
- Specific semantic selector vocabulary beyond the examples given
- Error message wording and hint content

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | CustomEvent threading pattern for main-thread API calls | CustomEvent sample code verified from official Autodesk docs; complete pattern documented below |
| INFRA-02 | Replace bare except:pass with proper error propagation | Cross-cutting concern; wrap all handler exceptions with tool name + params context |
| INFRA-03 | Dict-based dispatch with domain handler modules | Python dict dispatch pattern; module organization is Claude's discretion |
| INFRA-04 | Coordinate transformation for XZ plane Y-axis inversion | Sketch local coordinates always X/Y; XZ plane maps sketch-Y to -world-Z; needs swap+negate |
| INFRA-05 | Semantic face/edge selection helpers | BRepBody.faces/.edges iteration + bounding box analysis for position-based naming |
| FIX-01 | Fillet handler respects edges parameter | Current handler adds ALL edges; fix to filter by edge index list |
| FIX-02 | Extrude handler respects profile_index and taper_angle | Current handler ignores both params; add profile selection and setTaperAngle |
| FIX-03 | Revolve handler supports configurable axis | Current handler hardcodes yConstructionAxis; add axis parameter |
| FIX-04 | create_sketch handler respects offset parameter | Current handler ignores offset; use ConstructionPlanes.createInput().setByOffset() |
| FIX-05 | get_design_info returns component count | Add rootComp.allOccurrences.count or occurrences.count to response |
| SKTCH-01 | draw_line handler | sketchLines.addByTwoPoints(p1, p2) |
| SKTCH-02 | draw_arc handler | sketchArcs.addByThreePoints or addByCenterStartSweep |
| SKTCH-03 | draw_polygon handler | Draw N lines using trigonometry (no native polygon API) |
| FEAT-01 | chamfer handler | chamferFeatures.createInput() + addConstantDistanceEdgeSet() |
| FEAT-02 | shell handler | shellFeatures.createInput(facesToRemove, False) + insideThickness |
| FEAT-03 | draft handler | draftFeatures.createInput() with face collection and pull direction |
| FEAT-04 | pattern_rectangular handler | rectangularPatternFeatures.createInput() with axes, quantities, spacings |
| FEAT-05 | pattern_circular handler | circularPatternFeatures.createInput() with axis, count, angle |
| FEAT-06 | mirror handler | mirrorFeatures.createInput(entities, plane) |
| FEAT-07 | combine handler | combineFeatures.createInput(targetBody, tools) + operation type |
| QUERY-01 | get_body_info handler | Iterate body.edges and body.faces; compute lengths, areas, bounding boxes |
| QUERY-02 | measure handler | body.physicalProperties for volume/area; edge.length; face.area |
| COMP-01 | create_component handler | occurrences.addNewComponent(Matrix3D) or body-to-component conversion |
| COMP-02 | list_components handler | Iterate rootComp.occurrences with transform and bounding box data |
| COMP-03 | delete_component handler | occurrence.deleteMe() |
| COMP-04 | move_component handler | Set occurrence.transform with translation Matrix3D |
| COMP-05 | rotate_component handler | Set occurrence.transform with rotation Matrix3D |
| COMP-06 | check_interference handler | InterferenceInput + analyzeInterference() or bounding box check |
| JOINT-01 | create_revolute_joint handler | joints.createInput(geo0, geo1) + setAsRevoluteJointMotion() |
| JOINT-02 | create_slider_joint handler | joints.createInput(geo0, geo1) + setAsSliderJointMotion() |
| JOINT-03 | set_joint_angle handler | RevoluteJointMotion.rotationValue on existing joint |
| JOINT-04 | set_joint_distance handler | SliderJointMotion.slideValue on existing joint |
| UTIL-01 | undo handler | No direct API; use app.executeTextCommand("Commands.Undo") in a loop |
| UTIL-02 | delete_body handler | body.deleteMe() on BRepBody by index |
| UTIL-03 | delete_sketch handler | sketch.deleteMe() on Sketch by index |
| IO-01 | export_stl handler | exportManager.createSTLExportOptions(body/comp, filepath) + execute() |
| IO-02 | export_step handler | exportManager.createSTEPExportOptions(filepath) + execute() |
| IO-03 | export_3mf handler | exportManager.createSTLExportOptions with 3MF format, or create3MFExportOptions |
| IO-04 | import_mesh handler | meshBodies.add(filepath, units, baseFeature) within baseFeature edit context |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| adsk.core | Fusion 360 embedded | Application, events, geometry, custom events | Only option -- Fusion 360's built-in Python API |
| adsk.fusion | Fusion 360 embedded | Design features, sketches, bodies, joints, export | Only option -- Fusion 360's built-in Python API |
| mcp.server.fastmcp | Latest (pip) | MCP server framework with @mcp.tool() decorator | Already in use; FastMCP is the standard MCP Python SDK |
| Python 3.12.4 | Fusion embedded | Add-in runtime | Fusion 360's embedded interpreter; cannot change |
| Python 3.10+ | System | MCP server runtime | System Python; already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | Command/response serialization via file IPC | Every command exchange |
| threading | stdlib | Worker thread for file monitoring + CustomEvent firing | INFRA-01 threading pattern |
| math | stdlib | Trigonometry for polygon drawing, angle conversions | SKTCH-03, revolve angle calc |
| pathlib | stdlib | File path handling for IPC and exports | All file operations |
| traceback | stdlib | Exception formatting for error messages | INFRA-02 error handling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| File IPC | WebSocket/HTTP | More complex, no benefit for single-user local tool |
| Dict dispatch | Class-based command pattern | Over-engineered for simple function dispatch |
| Single file add-in | Python package with __init__.py | Fusion add-in loader expects single .py entry; modules must be imported carefully |

## Architecture Patterns

### Recommended Project Structure
```
fusion-addin/
  FusionMCP.py              # Entry point: run(), stop(), CustomEvent setup, monitor thread
  handlers/
    __init__.py              # Dict mapping tool_name -> handler_function
    sketch.py                # create_sketch, draw_line, draw_circle, draw_rectangle, draw_arc, draw_polygon, finish_sketch
    feature.py               # extrude, revolve, fillet, chamfer, shell, draft, pattern_*, mirror, combine
    query.py                 # get_design_info, get_body_info, measure
    component.py             # create_component, list_components, delete_component, move_component, rotate_component, check_interference
    joint.py                 # create_revolute_joint, create_slider_joint, set_joint_angle, set_joint_distance
    utility.py               # undo, delete_body, delete_sketch, fit_view
    io.py                    # export_stl, export_step, export_3mf, import_mesh
  helpers/
    __init__.py
    errors.py                # FusionMCPError class, wrap_handler(), format_error_with_hints()
    coordinates.py           # transform_input_coords(), transform_output_coords(), detect_xz_plane()
    selection.py             # resolve_edges(), resolve_faces(), semantic_selector_map, label_geometry()
    bodies.py                # get_body_by_index(), get_component_by_name_or_index()
mcp-server/
  fusion360_mcp_server.py    # Unchanged (MCP tool definitions, send_fusion_command)
```

### Pattern 1: CustomEvent Threading (INFRA-01)
**What:** Worker thread monitors for command files, fires a CustomEvent with command data as JSON, main-thread event handler executes the Fusion API call and writes the response.
**When to use:** Always -- this is the ONLY safe way to call Fusion API from a polling loop.
**Example:**
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomEventSample_Sample.htm
import adsk.core, adsk.fusion, threading, json, time
from pathlib import Path

COMM_DIR = Path.home() / "fusion_mcp_comm"
CUSTOM_EVENT_ID = 'FusionMCP_CommandEvent'

app = None
handlers = []
stop_flag = None
custom_event = None

class CommandEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            event_data = json.loads(args.additionalInfo)
            command = event_data['command']
            cmd_id = event_data['id']

            # Execute on main thread -- safe to call Fusion API here
            result = execute_command(command)

            # Write response
            resp_file = COMM_DIR / f"response_{cmd_id}.json"
            with open(resp_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            # Write error response
            resp_file = COMM_DIR / f"response_{event_data.get('id', 'unknown')}.json"
            with open(resp_file, 'w') as f:
                json.dump({"success": False, "error": str(e)}, f)

class MonitorThread(threading.Thread):
    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event
        self.daemon = True

    def run(self):
        while not self.stopped.wait(0.1):
            try:
                cmd_files = list(COMM_DIR.glob("command_*.json"))
                for cmd_file in cmd_files:
                    with open(cmd_file, 'r') as f:
                        command = json.load(f)
                    cmd_file.unlink()  # Remove command file immediately
                    # Fire custom event -- handler runs on main thread
                    app.fireCustomEvent(CUSTOM_EVENT_ID, json.dumps({
                        'command': command,
                        'id': command['id']
                    }))
            except:
                pass  # File system errors during polling are non-fatal

def run(context):
    global app, custom_event, stop_flag, handlers
    app = adsk.core.Application.get()
    COMM_DIR.mkdir(exist_ok=True)

    # Register custom event
    custom_event = app.registerCustomEvent(CUSTOM_EVENT_ID)
    handler = CommandEventHandler()
    custom_event.add(handler)
    handlers.append(handler)

    # Start monitor thread
    stop_flag = threading.Event()
    monitor = MonitorThread(stop_flag)
    monitor.start()

def stop(context):
    global stop_flag, custom_event
    stop_flag.set()
    if custom_event:
        custom_event.remove(handlers[0])
    app.unregisterCustomEvent(CUSTOM_EVENT_ID)
```

### Pattern 2: Dict-Based Dispatch (INFRA-03)
**What:** Replace if-elif chain with a dictionary mapping tool names to handler functions.
**When to use:** For routing incoming commands to handler functions.
**Example:**
```python
# handlers/__init__.py
from .sketch import create_sketch, draw_line, draw_circle, draw_rectangle, draw_arc, draw_polygon, finish_sketch
from .feature import extrude, revolve, fillet, chamfer, shell, draft, pattern_rectangular, pattern_circular, mirror, combine
# ... etc

HANDLER_MAP = {
    'create_sketch': create_sketch,
    'draw_line': draw_line,
    'draw_circle': draw_circle,
    # ... all 39 handlers
}

# In execute_command:
def execute_command(command):
    tool_name = command.get('name')
    params = command.get('params', {})
    handler = HANDLER_MAP.get(tool_name)
    if not handler:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    return handler(design, rootComp, params)
```

### Pattern 3: Error Wrapping (INFRA-02)
**What:** Every handler is wrapped to catch exceptions and produce verbose, contextual error messages.
**When to use:** All handlers, applied via decorator or wrapper in dispatch.
**Example:**
```python
def wrap_handler(tool_name, handler_fn, params):
    """Wrap handler execution with error context."""
    try:
        return handler_fn(design, rootComp, params)
    except Exception as e:
        error_msg = str(e)
        hint = generate_hint(tool_name, params, e)
        return {
            "success": False,
            "error": f"{tool_name}({format_params(params)}) failed: {error_msg}",
            "hint": hint
        }
```

### Pattern 4: Coordinate Correction (INFRA-04)
**What:** On XZ plane sketches, swap and negate Y coordinates so user-facing coordinates match world space.
**When to use:** Sketch operations (draw_line, draw_circle, etc.) when active sketch is on XZ plane.
**Example:**
```python
def transform_to_sketch_coords(x, y, sketch):
    """Transform world-intuitive coords to sketch-local coords for XZ plane."""
    # Sketches on XZ plane: sketch local X = world X, sketch local Y = -world Z
    # User provides (x, z_as_y) in world terms, we need sketch (x, -z)
    # The sketch transform handles the mapping, but the sign flip needs correction
    plane = detect_sketch_plane(sketch)
    if plane == 'XZ':
        return (x, -y)  # User's Y (which means world Z) maps to sketch -Y
    return (x, y)  # XY and YZ planes: no correction needed

def transform_from_sketch_coords(x, y, sketch):
    """Transform sketch-local coords back to world-intuitive coords for responses."""
    plane = detect_sketch_plane(sketch)
    if plane == 'XZ':
        return (x, -y)
    return (x, y)
```

### Anti-Patterns to Avoid
- **Calling Fusion API from worker thread:** Causes silent crashes, data corruption, or intermittent failures. ALL Fusion API calls must go through CustomEvent to main thread.
- **Bare except:pass:** Swallows errors silently. The current codebase has multiple instances (lines 26, 37, 53, 55-56 of FusionMCP.py). Every exception must be caught, formatted, and returned.
- **Hardcoded body/sketch selection (always last item):** Current handlers use `sketches.item(sketches.count - 1)`. This breaks when users work with multiple sketches/bodies. Add index parameters.
- **Ignoring tool parameters:** Current handlers for extrude, revolve, fillet, create_sketch ignore parameters declared in the MCP server. Every MCP parameter must be respected.
- **Raw exception messages:** Never return `str(e)` from adsk exceptions directly -- they contain cryptic error codes. Wrap with human-readable context.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| STL/STEP export | Custom mesh serialization | `design.exportManager.createSTLExportOptions()` / `createSTEPExportOptions()` | Export manager handles mesh refinement, units, multi-body correctly |
| Mesh import | Custom file parsing | `meshBodies.add(filepath, units, baseFeature)` | Handles STL/OBJ/3MF formats, multi-body files, unit conversion |
| Boolean operations | Manual geometry computation | `combineFeatures.createInput(target, tools)` with FeatureOperations enum | Fusion's kernel handles topology, edge cases, non-manifold detection |
| Interference detection | Manual bounding box math | `InterferenceInput` + `analyzeInterference()` | Handles exact geometry intersection, not just AABB |
| Matrix transformations | Manual 3x3/4x4 math | `adsk.core.Matrix3D` + `setToRotation()`, `translation` property | Handles rotation origin, axis specification, composition correctly |
| Pattern features | Loop + copy + transform | `rectangularPatternFeatures` / `circularPatternFeatures` | Maintains parametric history, handles compute order, associativity |

**Key insight:** The Fusion 360 API provides high-level feature operations for nearly everything needed. The add-in handlers should be thin wrappers that translate MCP parameters to API calls, not reimplementations of geometry operations.

## Common Pitfalls

### Pitfall 1: Threading Violation (Silent Crash)
**What goes wrong:** Fusion API calls from background thread cause random crashes, corrupted data, or operations that silently fail.
**Why it happens:** Fusion 360's API is not thread-safe. The COM-based architecture requires all API calls on the main thread.
**How to avoid:** Use CustomEvent pattern exclusively. Worker thread only reads files and fires events.
**Warning signs:** Intermittent failures, Fusion freezing, operations that work sometimes but not always.

### Pitfall 2: Event Handler Garbage Collection
**What goes wrong:** CustomEventHandler gets garbage collected and events stop firing.
**Why it happens:** Python GC collects the handler object if no strong reference exists.
**How to avoid:** Store handler references in a module-level list (`handlers.append(onThreadEvent)`). This is shown in the official sample.
**Warning signs:** Events work initially then stop after some time.

### Pitfall 3: Sketch Coordinate Confusion on XZ Plane
**What goes wrong:** Geometry appears at wrong positions or mirrored when sketching on XZ plane.
**Why it happens:** All sketches use local X/Y coordinates internally. On XZ plane, sketch-Y maps to negative world-Z. Users expect world-space coordinates.
**How to avoid:** Implement INFRA-04 coordinate correction layer that transforms coordinates before/after sketch operations. Detect plane via sketch transform analysis or by checking which construction plane was used.
**Warning signs:** Circles appearing at wrong height, rectangles mirrored.

### Pitfall 4: BaseFeature Requirement for Mesh Import
**What goes wrong:** `meshBodies.add()` fails with cryptic error in parametric designs.
**Why it happens:** In parametric mode, mesh bodies must be created inside a BaseFeature edit context.
**How to avoid:** Check design type. If parametric, create/edit a BaseFeature before calling meshBodies.add(), then finishEdit() after.
**Warning signs:** Import works in direct design mode but fails in parametric mode.

### Pitfall 5: Undo Has No Direct API
**What goes wrong:** Attempting to find an `app.undo()` method that doesn't exist.
**Why it happens:** Fusion 360 API does not expose a direct undo method.
**How to avoid:** Use `app.executeTextCommand("Commands.Undo")` -- this is an undocumented but widely-used approach. Note: each call undoes one operation. For count > 1, call in a loop.
**Warning signs:** Looking for undo in API docs and finding nothing.

### Pitfall 6: 3MF Export Not Directly in ExportManager
**What goes wrong:** Looking for `createThreeMFExportOptions()` method that may not exist.
**Why it happens:** 3MF export may use the STL export path with format option, or may require the 3D Print utility pathway.
**How to avoid:** Use `createSTLExportOptions()` and check if it supports 3MF format flag, or use the mesh export approach. If not available, export as STL and note the limitation.
**Warning signs:** API method not found errors.

### Pitfall 7: Component vs Occurrence Confusion
**What goes wrong:** Moving/rotating a component doesn't work, or affects wrong geometry.
**Why it happens:** In Fusion 360, a Component is a definition (template) and an Occurrence is an instance placed in the assembly. You transform occurrences, not components.
**How to avoid:** Always work with `rootComp.occurrences` for positioning. Use `occurrence.transform` to set position/rotation.
**Warning signs:** "Transform" property not found on Component object.

### Pitfall 8: Joint Geometry Point Creation
**What goes wrong:** Joint creation fails because geometry objects are not valid.
**Why it happens:** JointGeometry must reference actual topology (faces, edges, vertices) or use `createByPoint()`.
**How to avoid:** Use `JointGeometry.createByPoint(occurrence, point3D)` for simple positioning. This creates joint geometry at a specific point on a component.
**Warning signs:** "Invalid joint geometry" errors.

## Code Examples

Verified patterns from official sources:

### Shell Feature (FEAT-02)
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ShellFeatureSample_Sample.htm
def handle_shell(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))
    thickness = params['thickness']

    faces_to_remove = adsk.core.ObjectCollection.create()
    face_indices = params.get('faces_to_remove', [])
    # Support both indices and semantic selectors
    resolved = resolve_faces(body, face_indices)
    for face in resolved:
        faces_to_remove.add(face)

    shell_feats = rootComp.features.shellFeatures
    shell_input = shell_feats.createInput(faces_to_remove, False)
    shell_input.insideThickness = adsk.core.ValueInput.createByReal(thickness)
    shell_feat = shell_feats.add(shell_input)
    return {"success": True, "feature_name": shell_feat.name}
```

### Rectangular Pattern (FEAT-04)
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/RectangularPatternFeatureSample_Sample.htm
def handle_pattern_rectangular(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))
    entities = adsk.core.ObjectCollection.create()
    entities.add(body)

    x_axis = rootComp.xConstructionAxis
    y_axis = rootComp.yConstructionAxis

    qty_x = adsk.core.ValueInput.createByString(str(params['x_count']))
    dist_x = adsk.core.ValueInput.createByReal(params['x_spacing'])

    rect_patterns = rootComp.features.rectangularPatternFeatures
    pattern_input = rect_patterns.createInput(
        entities, x_axis, qty_x, dist_x,
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
    )

    if params.get('y_count', 1) > 1:
        qty_y = adsk.core.ValueInput.createByString(str(params['y_count']))
        dist_y = adsk.core.ValueInput.createByReal(params.get('y_spacing', 0))
        pattern_input.setDirectionTwo(y_axis, qty_y, dist_y)

    pattern = rect_patterns.add(pattern_input)
    return {"success": True, "feature_name": pattern.name}
```

### Combine / Boolean (FEAT-07)
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/combineFeatures_add_Sample.htm
def handle_combine(design, rootComp, params):
    target_body = rootComp.bRepBodies.item(params['target_body'])
    tools = adsk.core.ObjectCollection.create()
    for idx in params['tool_bodies']:
        tools.add(rootComp.bRepBodies.item(idx))

    op_map = {
        'cut': adsk.fusion.FeatureOperations.CutFeatureOperation,
        'join': adsk.fusion.FeatureOperations.JoinFeatureOperation,
        'intersect': adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }

    combine_feats = rootComp.features.combineFeatures
    combine_input = combine_feats.createInput(target_body, tools)
    combine_input.operation = op_map[params.get('operation', 'cut')]
    combine_input.isKeepToolBodies = params.get('keep_tools', False)
    combine = combine_feats.add(combine_input)
    return {"success": True, "feature_name": combine.name}
```

### Joint Creation (JOINT-01)
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointSample_Sample.htm
def handle_create_revolute_joint(design, rootComp, params):
    occ1 = get_occurrence(rootComp, params.get('component1_index'))
    occ2 = get_occurrence(rootComp, params.get('component2_index'))

    point = adsk.core.Point3D.create(params['x'], params['y'], params['z'])
    geo0 = adsk.fusion.JointGeometry.createByPoint(occ1, point)
    geo1 = adsk.fusion.JointGeometry.createByPoint(occ2, point)

    joints = rootComp.joints
    joint_input = joints.createInput(geo0, geo1)
    joint_input.setAsRevoluteJointMotion(
        adsk.fusion.JointDirections.ZAxisJointDirection  # or map from params axis
    )

    if params.get('min_angle') is not None or params.get('max_angle') is not None:
        # Set limits after creation
        pass  # limits are set on the joint motion object after add()

    joint = joints.add(joint_input)
    if params.get('flip', False):
        joint.isFlipped = True

    return {"success": True, "joint_name": joint.name}
```

### STL Export (IO-01)
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/STLExport_Sample.htm
def handle_export_stl(design, rootComp, params):
    filepath = params['filepath']
    export_mgr = design.exportManager
    stl_options = export_mgr.createSTLExportOptions(rootComp, filepath)
    stl_options.sendToPrintUtility = False
    stl_options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
    export_mgr.execute(stl_options)
    return {"success": True, "filepath": filepath}
```

### Mesh Import (IO-04)
```python
# Source: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/MeshBodies_add.htm
def handle_import_mesh(design, rootComp, params):
    filepath = params['filepath']
    unit_map = {
        'mm': adsk.fusion.MeshUnits.MillimeterMeshUnit,
        'cm': adsk.fusion.MeshUnits.CentimeterMeshUnit,
        'in': adsk.fusion.MeshUnits.InchMeshUnit,
    }
    units = unit_map.get(params.get('unit', 'mm'), adsk.fusion.MeshUnits.MillimeterMeshUnit)

    # Parametric designs require BaseFeature context
    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        base_feats = rootComp.features.baseFeatures
        base_feat = base_feats.add()
        base_feat.startEdit()
        meshes = rootComp.meshBodies.add(filepath, units, base_feat)
        base_feat.finishEdit()
    else:
        meshes = rootComp.meshBodies.add(filepath, units)

    return {"success": True, "mesh_count": meshes.count}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct API calls from thread | CustomEvent pattern | Long-standing best practice | Prevents all threading crashes |
| If-elif dispatch (9 handlers) | Dict dispatch (39+ handlers) | This phase | Scalable to 80+ handlers |
| Bare except:pass | Structured error wrapping | This phase | Actionable error messages for AI callers |
| Index-only face/edge selection | Semantic + index selection | This phase | AI callers can use "top_face" instead of guessing indices |
| Raw sketch coordinates | Coordinate correction layer | This phase | XZ plane sketches match world-space intuition |

**Deprecated/outdated:**
- Threading violation pattern (current code): Must be replaced immediately
- Bare exception handling: Security/reliability anti-pattern

## Open Questions

1. **3MF Export Method Availability**
   - What we know: STL and STEP export have explicit createXxxExportOptions() methods. 3MF may share the STL export path or have its own method.
   - What's unclear: Whether `create3MFExportOptions()` exists as a dedicated method or if 3MF is handled through the STL export options with a format flag.
   - Recommendation: Try `createSTLExportOptions()` first and check for 3MF format option. If unavailable, fall back to STL-only and document the limitation. Verify at implementation time.

2. **InterferenceInput API Availability**
   - What we know: Fusion UI has interference detection. The API has `InterferenceInput` class referenced in docs.
   - What's unclear: Exact method signatures for programmatic interference detection in current API version.
   - Recommendation: Implement bounding-box-based collision detection as the MCP tool description already says "bounding box collision detection". Can upgrade to exact interference later.

3. **Undo Reliability via executeTextCommand**
   - What we know: `app.executeTextCommand("Commands.Undo")` is the community-standard workaround. No official undo API exists.
   - What's unclear: Whether this works reliably when called from a CustomEvent handler on the main thread, and whether it interacts well with the command transaction system.
   - Recommendation: Implement and test. If unreliable, document as a known limitation.

4. **Sketch Plane Detection**
   - What we know: Need to detect which construction plane a sketch was created on to apply coordinate correction.
   - What's unclear: Best method -- check sketch.transform matrix, compare referencePlane, or store plane name during create_sketch and pass it through.
   - Recommendation: Store the plane name in the sketch's attributes or pass it via the command params chain. Checking the transform matrix is fragile.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual testing via MCP tool calls in Fusion 360 |
| Config file | None -- no automated unit test framework for Fusion add-in code |
| Quick run command | Call individual MCP tools via Claude/MCP client |
| Full suite command | Run batch of all 39 tools sequentially via batch() MCP tool |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | API calls execute on main thread without crashes | manual | Start add-in, run 10+ sequential tool calls | N/A |
| INFRA-02 | Error messages include tool name, params, hints | manual | Call fillet with invalid edge index, verify error format | N/A |
| INFRA-03 | Dict dispatch routes all 39 tools correctly | manual | Call each tool, verify no "Unknown tool" responses | N/A |
| INFRA-04 | XZ plane coordinates match world space | manual | create_sketch(XZ), draw_circle(0, 5, 1), verify circle at world Z=5 | N/A |
| INFRA-05 | Semantic selectors work alongside indices | manual | get_body_info() shows labels, fillet(edges=["top_edge"]) works | N/A |
| FIX-01 | Fillet selective edges | manual | Create box, fillet(edges=[0,1]) fillets only those 2 edges | N/A |
| FIX-02 | Extrude profile_index and taper_angle | manual | Draw 2 circles, extrude(profile_index=1, taper_angle=5) | N/A |
| FIX-03 | Revolve configurable axis | manual | revolve(angle=360, axis="X") uses X axis | N/A |
| FIX-04 | Offset sketch plane | manual | create_sketch(plane="XY", offset=5) creates sketch 5cm above origin | N/A |
| FIX-05 | Design info includes component count | manual | get_design_info() returns component_count field | N/A |
| SKTCH-01 | draw_line works | manual | draw_line(0,0,5,5) creates line in active sketch | N/A |
| SKTCH-02 | draw_arc works | manual | draw_arc(center/start/end) creates arc | N/A |
| SKTCH-03 | draw_polygon works | manual | draw_polygon(sides=6) creates hexagon | N/A |
| FEAT-01 through FEAT-07 | All feature handlers execute | manual | Create body, apply each feature operation | N/A |
| QUERY-01 | get_body_info returns edges/faces with labels | manual | Create box, get_body_info() returns indexed+labeled geometry | N/A |
| QUERY-02 | measure returns dimensions | manual | measure(type="body") returns volume, surface_area, bbox | N/A |
| COMP-01 through COMP-06 | Component operations work | manual | Create, list, move, rotate, delete components | N/A |
| JOINT-01 through JOINT-04 | Joint operations work | manual | Create joints, drive joint motion | N/A |
| UTIL-01 through UTIL-03 | Utility operations work | manual | Undo, delete_body, delete_sketch | N/A |
| IO-01 through IO-04 | Import/export work | manual | Export STL/STEP/3MF, import mesh file | N/A |

### Sampling Rate
- **Per task commit:** Run the specific tools modified/added in that task
- **Per wave merge:** Run batch() with all 39 tools in sequence
- **Phase gate:** All 39 tools return success or clear error (no "Unknown tool", no crashes)

### Wave 0 Gaps
- No automated test framework exists or is practical -- Fusion 360 add-ins can only be tested inside the running Fusion 360 application
- Manual test scripts (batch commands) can be created as JSON files for reproducible testing
- A `test_all_tools.json` batch command file would be valuable for regression testing

## Sources

### Primary (HIGH confidence)
- [Custom Event Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomEventSample_Sample.htm) - Complete CustomEvent threading pattern with Python code
- [Application.fireCustomEvent](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Application_fireCustomEvent.htm) - Official API reference for firing events from worker threads
- [Shell Feature API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ShellFeatureSample_Sample.htm) - Shell feature creation pattern
- [RectangularPattern Feature Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/RectangularPatternFeatureSample_Sample.htm) - Rectangular pattern creation
- [Mirror Feature Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/MirrorFeatureSample_Sample.htm) - Mirror feature creation
- [Joint API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/JointSample_Sample.htm) - Joint creation with JointGeometry
- [STL Export Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/STLExport_Sample.htm) - STL export via ExportManager
- [Export to Other Formats](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportToOtherFormats_Sample.htm) - STEP/IGES/SAT export
- [MeshBodies.add Method](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/MeshBodies_add.htm) - Mesh import for STL/OBJ/3MF
- [CombineFeatures.createInput](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CombineFeatures_createInput.htm) - Boolean operations
- [combineFeatures.add Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/combineFeatures_add_Sample.htm) - Combine feature execution

### Secondary (MEDIUM confidence)
- [Working in a Separate Thread](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-F9FD4A6D-C59F-4176-9003-CE04F7558CCC) - Threading guidance (page loaded as JS, content verified via search excerpts)
- [Autodesk Community: Undo via API](https://forums.autodesk.com/t5/fusion-360-api-and-scripts/undo-via-api/td-p/8636698) - executeTextCommand("Commands.Undo") approach
- [Autodesk Community: CustomEvent Threading](https://forums.autodesk.com/t5/fusion-api-and-scripts/custom-event-handler-and-threading/td-p/8087251) - Threading pattern discussion

### Tertiary (LOW confidence)
- 3MF export method: Not found in official samples; may share STL export path or have undocumented method. Needs implementation-time verification.
- InterferenceInput exact API: Referenced in API object model PDF but no Python sample found. Bounding box fallback is documented in MCP tool definition.
- Sketch plane detection method: Multiple approaches discussed in forums; no single canonical pattern. Storing plane name during create_sketch is safest approach.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Fusion 360 Python API is mature, well-documented, and unchanged for this domain
- Architecture: HIGH - CustomEvent pattern is the official recommended approach with complete samples
- Handler implementations: HIGH - Each handler maps to well-documented API methods with official samples
- Coordinate correction: MEDIUM - XZ plane inversion is well-known but correction approach varies; storing plane name is simplest
- Pitfalls: HIGH - Threading, GC, BaseFeature requirements are well-documented gotchas
- 3MF export: LOW - Exact API method not confirmed in official Python samples
- Undo via text command: MEDIUM - Community-standard but undocumented approach

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (Fusion 360 API is stable; 30-day validity)
