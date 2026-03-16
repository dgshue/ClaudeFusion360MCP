# Fusion 360 MCP Reference v0.5.0

**MCP Version**: 0.5.0  
**Last Updated**: March 2025

---

## Table of Contents

1. [Coordinate System](#coordinate-system)
2. [Tool Reference](#tool-reference)
3. [Manufacturing Guidelines](#manufacturing-guidelines)
4. [Error Handling](#error-handling)
5. [Version History](#version-history)

---

## Coordinate System

### Axes
| Axis | Direction | Usage |
|------|-----------|-------|
| X | Right (+) / Left (-) | Width |
| Y | Toward (+) / Away (-) | Depth |
| Z | Up (+) / Down (-) | Height |

### Planes
| Plane | Horizontal | Vertical | Extrusion |
|-------|------------|----------|-----------|
| XY | X | Y | +/-Z |
| XZ | X | Z | +/-Y |
| YZ | Y | Z | +/-X |

### Sketch-to-World Mapping
| Sketch Plane | Sketch X  >  | Sketch Y  >  | Extrude +  >  |
|--------------|------------|------------|-------------|
| XY | World X | World Y | World +Z |
| XZ | World X | World Z | World +Y |
| YZ | World Y | World Z | World +X |

---

## Tool Reference

### Sketch Tools

#### create_sketch
```
create_sketch(plane: str, offset: float = 0)  >  dict
```
Create sketch on construction plane.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| plane | string | Yes | - | "XY", "XZ", or "YZ" |
| offset | float | No | 0 | Offset from origin (cm) |

**Example**:
```python
create_sketch(plane="XY")           # At origin
create_sketch(plane="XY", offset=5) # 5cm above origin
```

#### finish_sketch
```
finish_sketch()  >  dict
```
Exit sketch editing mode.

#### draw_rectangle
```
draw_rectangle(x1: float, y1: float, x2: float, y2: float)  >  dict
```
Draw rectangle by two corners (cm).

#### draw_circle
```
draw_circle(center_x: float, center_y: float, radius: float)  >  dict
```
Draw circle by center and radius (cm).

#### draw_line
```
draw_line(x1: float, y1: float, x2: float, y2: float)  >  dict
```
Draw line segment (cm).

#### draw_arc
```
draw_arc(center_x: float, center_y: float, 
         start_x: float, start_y: float, 
         end_x: float, end_y: float)  >  dict
```
Draw arc by center and endpoints (cm).

#### draw_polygon
```
draw_polygon(center_x: float, center_y: float, 
             radius: float, sides: int = 6)  >  dict
```
Draw regular polygon (cm).

---

### Feature Tools

#### extrude
```
extrude(distance: float, profile_index: int = 0, taper_angle: float = 0,
        operation: str = "new_body")  >  dict
```
Extrude sketch profile.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| distance | float | Yes | - | Extrusion distance (cm) |
| profile_index | int | No | 0 | Which profile to extrude |
| taper_angle | float | No | 0 | Draft angle during extrusion ( deg) |
| operation | string | No | "new_body" | Boolean operation: `new_body`, `join`, `cut`, `intersect` |

#### revolve
```
revolve(angle: float)  >  dict
```
Revolve profile around Y-axis (degrees).

#### fillet
```
fillet(radius: float, edges: list = None, body_index: int = None)  >  dict
```
Apply fillets to edges.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| radius | float | Yes | - | Fillet radius (cm) |
| edges | list | No | None | Edge indices (None = all) |
| body_index | int | No | Last | Which body |

#### chamfer
```
chamfer(distance: float, edges: list = None, body_index: int = None)  >  dict
```
Apply chamfers to edges.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| distance | float | Yes | - | Chamfer distance (cm) |
| edges | list | No | None | Edge indices (None = all) |
| body_index | int | No | Last | Which body |

#### shell * NEW
```
shell(thickness: float, faces_to_remove: list = None, body_index: int = None)  >  dict
```
Create hollow shell from solid.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| thickness | float | Yes | - | Wall thickness (cm) |
| faces_to_remove | list | No | None | Face indices to open |
| body_index | int | No | Last | Which body |

#### draft * NEW
```
draft(angle: float, faces: list = None, body_index: int = None,
      pull_x: float = 0, pull_y: float = 0, pull_z: float = 1)  >  dict
```
Apply draft angles for molding.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| angle | float | Yes | - | Draft angle (degrees) |
| faces | list | No | None | Face indices (None = all) |
| body_index | int | No | Last | Which body |
| pull_x/y/z | float | No | 0,0,1 | Pull direction |

#### pattern_rectangular * NEW
```
pattern_rectangular(x_count: int, x_spacing: float,
                    y_count: int = 1, y_spacing: float = 0,
                    body_index: int = None)  >  dict
```
Create linear pattern.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| x_count | int | Yes | - | Instances in X |
| x_spacing | float | Yes | - | Spacing in X (cm) |
| y_count | int | No | 1 | Instances in Y |
| y_spacing | float | No | 0 | Spacing in Y (cm) |
| body_index | int | No | Last | Which body |

#### pattern_circular * NEW
```
pattern_circular(count: int, angle: float = 360, 
                 axis: str = "Z", body_index: int = None)  >  dict
```
Create radial pattern.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| count | int | Yes | - | Number of instances |
| angle | float | No | 360 | Total angle (degrees) |
| axis | string | No | "Z" | Rotation axis |
| body_index | int | No | Last | Which body |

#### mirror * NEW
```
mirror(plane: str = "YZ", body_index: int = None)  >  dict
```
Mirror geometry.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| plane | string | No | "YZ" | Mirror plane |
| body_index | int | No | Last | Which body |

---

### Thread & Hole Tools

#### thread
```
thread(face: int, body_index: int = None, thread_type: str = None,
       designation: str = None, thread_class: str = None,
       is_internal: bool = False, full_length: bool = True,
       length: float = None, modeled: bool = False)
```
Apply threads to a cylindrical face. Auto-recommends thread spec from face diameter if no designation provided.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| face | int/str | Yes | - | Face index or `"auto"` to find first cylindrical face |
| body_index | int | No | Last | Which body |
| thread_type | string | No | Auto | Thread standard (e.g. "ISO Metric profile", "ANSI Unified Screw Threads") |
| designation | string | No | Auto | Thread size (e.g. "M24x3", "3/4-10 UNC") |
| thread_class | string | No | Auto | Tolerance class (e.g. "6g", "6H", "3B") |
| is_internal | bool | No | False | True for internal threads (holes), False for external |
| full_length | bool | No | True | Thread the full face length |
| length | float | No | - | Thread length in cm (when full_length=False) |
| modeled | bool | No | False | Create physical thread geometry (for 3D printing). Default is cosmetic only |

**Examples:**
```python
thread(face=2)                                     # Auto-detect from face diameter
thread(face=0, is_internal=True)                   # Auto internal thread on a hole
thread(face="auto", is_internal=True, modeled=True) # Physical threads for 3D printing
thread(face=1, thread_type="ANSI Unified Screw Threads",
       designation="3/4-10 UNC", thread_class="3B", is_internal=True)
```

**Note:** `modeled=True` creates physical thread geometry visible in STL/3MF exports. Cosmetic threads (default) only display visually in Fusion 360 but do not affect the mesh.

#### query_threads
```
query_threads(mode: str = "recommend", face: int = None,
              is_internal: bool = None, thread_type: str = None,
              size: str = None, designation: str = None)
```
Query available thread specifications. Use before `thread()` to discover valid options.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| mode | string | No | "recommend" | Query mode: `recommend`, `types`, `sizes`, `designations`, `classes` |
| face | int/str | No | None | Face index or `"auto"` (for recommend mode) |
| is_internal | bool | No | None | Filter by internal/external |
| thread_type | string | No | None | Filter by thread standard |
| size | string | No | None | Thread size (e.g. "6.0" not "M6") |
| designation | string | No | None | Thread designation |

**Examples:**
```python
query_threads(mode="recommend", face="auto")       # Best thread for a face
query_threads(mode="types")                         # List all thread standards
query_threads(mode="sizes", thread_type="ISO Metric profile")  # Available sizes
```

#### hole
```
hole(x: float, y: float, diameter: float, depth: float,
     tip_angle: float = 118, body_index: int = None)
```
Create a hole at a point on a planar face.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| x | float | Yes | - | X position (cm) |
| y | float | Yes | - | Y position (cm) |
| diameter | float | Yes | - | Hole diameter (cm) |
| depth | float | Yes | - | Hole depth (cm) |
| tip_angle | float | No | 118 | Drill point angle (degrees) |
| body_index | int | No | Last | Which body |

---

### Component Tools

#### create_component
```
create_component(name: str = None)  >  dict
```
Convert body to component.

#### list_components
```
list_components()  >  dict
```
Get all components with positions and bounding boxes.

#### delete_component
```
delete_component(name: str = None, index: int = None)  >  dict
```
Remove component by name or index.

#### check_interference
```
check_interference()  >  dict
```
Detect bounding box collisions.

#### move_component * NEW
```
move_component(x: float = 0, y: float = 0, z: float = 0,
               index: int = None, name: str = None, 
               absolute: bool = True)  >  dict
```
Position component.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| x, y, z | float | No | 0 | Position (cm) |
| index | int | No | None | Component index |
| name | string | No | None | Component name |
| absolute | bool | No | True | True=position, False=offset |

#### rotate_component * NEW
```
rotate_component(angle: float, axis: str = "Z",
                 index: int = None, name: str = None,
                 origin_x: float = 0, origin_y: float = 0, 
                 origin_z: float = 0)  >  dict
```
Rotate component.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| angle | float | Yes | - | Rotation angle (degrees) |
| axis | string | No | "Z" | Rotation axis |
| index | int | No | None | Component index |
| name | string | No | None | Component name |
| origin_x/y/z | float | No | 0 | Rotation origin (cm) |

---

### Joint Tools

#### create_revolute_joint
```
create_revolute_joint(component1_index: int = None,
                      component2_index: int = None,
                      x: float = 0, y: float = 0, z: float = 0,
                      axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                      min_angle: float = None, max_angle: float = None,
                      flip: bool = False)  >  dict
```
Create hinge joint.

#### create_slider_joint
```
create_slider_joint(component1_index: int = None,
                    component2_index: int = None,
                    x: float = 0, y: float = 0, z: float = 0,
                    axis_x: float = 1, axis_y: float = 0, axis_z: float = 0,
                    min_distance: float = None, max_distance: float = None)  >  dict
```
Create sliding joint.

#### set_joint_angle
```
set_joint_angle(angle: float, joint_index: int = None)  >  dict
```
Animate revolute joint (degrees).

#### set_joint_distance
```
set_joint_distance(distance: float, joint_index: int = None)  >  dict
```
Animate slider joint (cm).

---

### Inspection Tools

#### get_body_info * NEW
```
get_body_info(body_index: int = None)  >  dict
```
Get edge and face information.

**Returns**:
```json
{
  "body_name": "Body1",
  "edge_count": 12,
  "face_count": 6,
  "edges": [
    {"index": 0, "length": 10.0, "start": {...}, "end": {...}},
    ...
  ],
  "faces": [
    {"index": 0, "area": 100.0, "centroid": {...}},
    ...
  ]
}
```

#### measure * NEW
```
measure(type: str = "body", body_index: int = None,
        edge_index: int = None, face_index: int = None)  >  dict
```
Measure geometry.

| type | Returns |
|------|---------|
| "body" | volume, surface_area, bounding_box |
| "edge" | length |
| "face" | area |

#### get_design_info
```
get_design_info()  >  dict
```
Get design statistics.

#### fit_view
```
fit_view()  >  dict
```
Zoom to fit all geometry.

---

### Export/Import Tools

#### export_stl / export_step / export_3mf
```
export_stl(filepath: str)  >  dict
export_step(filepath: str)  >  dict
export_3mf(filepath: str)  >  dict
```
Export design to file. STL uses high mesh refinement for accurate thread geometry.

#### import_mesh
```
import_mesh(filepath: str, unit: str = "mm")  >  dict
```
Import mesh file. Units: "mm", "cm", "in".

#### batch
```
batch(commands: list)  >  dict
```
Execute multiple commands.

**Example**:
```python
batch([
    {"name": "create_sketch", "params": {"plane": "XY"}},
    {"name": "draw_rectangle", "params": {"x1": -5, "y1": -5, "x2": 5, "y2": 5}},
    {"name": "finish_sketch", "params": {}},
    {"name": "extrude", "params": {"distance": 2}}
])
```

---

## Manufacturing Guidelines

### 3D Printing (FDM)

| Feature | Minimum | Recommended |
|---------|---------|-------------|
| Wall thickness | 0.08cm | 0.12cm |
| Hole compensation | +0.02cm | +0.04cm |
| Overhang angle | 45 deg | 35 deg |
| Bridge length | 1cm | 0.5cm |

### 3D Printing (SLA)

| Feature | Minimum |
|---------|---------|
| Wall thickness | 0.06cm |
| Feature size | 0.03cm |
| Drain holes | 0.2-0.3cm |

### CNC Machining

| Feature | Guideline |
|---------|-----------|
| Internal corner radius | >= tool radius |
| Wall thickness | >= 0.08cm |
| Hole depth | <= 4x diameter |

### Injection Molding

| Feature | Specification |
|---------|---------------|
| Wall thickness | 0.15-0.25cm |
| Draft angle | 1 deg per inch minimum |
| Rib thickness | 50-60% of wall |
| Internal fillet | >= 50% wall thickness |

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No active sketch" | Missing create_sketch | Call create_sketch() first |
| "Sketch is not closed" | Open profile | Ensure lines connect |
| "Extrusion failed" | No valid profile | Check sketch geometry |
| "Fillet radius too large" | Radius > geometry | Reduce radius |
| "Component name exists" | Duplicate name | Use unique name |
| "Invalid component index" | Index out of range | Check list_components |

---

## Version History

| Version | MCP | Date | Changes |
|---------|-----|------|---------|
| 0.5.0 | 0.5.0 | Mar 2025 | Added thread, query_threads, hole tools. Extrude now supports operation param (join/cut/intersect). Thread supports modeled geometry for 3D printing. STL export uses high refinement. Add-in hot-reload via importlib. |
| 0.4.0 | 0.4.0 | Dec 2024 | Added move/rotate_component, shell, draft, patterns, mirror, get_body_info, measure. Enhanced create_sketch, extrude, fillet, chamfer. |
| 0.3.0 | 0.3.0 | Dec 2024 | Added batch, draw_polygon, chamfer |
| 0.2.0 | 0.2.0 | Dec 2024 | Added joints, components |
| 0.1.0 | 0.1.0 | Earlier | Initial release |

---

*Fusion 360 MCP Reference v0.5.0*

---

## Utility Operations (v7.2)

### undo

Undo recent operations in Fusion 360.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| count | int | 1 | Number of operations to undo |

**Returns:**
```json
{
  "success": true,
  "undone_count": 5,
  "requested_count": 5
}
```

**Example:**
```python
undo()         # Undo 1 operation
undo(count=10) # Undo up to 10 operations
```

---

### delete_body

Delete a body by index.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| body_index | int | most recent | Index of body to delete |

**Returns:**
```json
{
  "success": true,
  "deleted_body": "Body5",
  "deleted_index": 3,
  "remaining_bodies": 4
}
```

**Example:**
```python
delete_body()              # Delete most recent body
delete_body(body_index=2)  # Delete specific body
```

**Note:** Deleting a body shifts indices of all bodies after it!

---

### delete_sketch

Delete a sketch by index.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| sketch_index | int | most recent | Index of sketch to delete |

**Returns:**
```json
{
  "success": true,
  "deleted_sketch": "Sketch3",
  "deleted_index": 2,
  "remaining_sketches": 4
}
```

**Example:**
```python
delete_sketch()                # Delete most recent sketch
delete_sketch(sketch_index=0)  # Delete first sketch
```
