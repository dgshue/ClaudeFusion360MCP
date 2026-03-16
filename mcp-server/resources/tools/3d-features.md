# 3D Features & Construction Tools Reference

All dimensions are in **cm** and angles in **degrees** unless noted otherwise.

## Basic Features

### extrude
Extrude the most recent sketch profile into a 3D body.
- `distance` (float): Extrusion distance (positive extends forward, negative extends backward)
- `profile_index` (int): Which profile if multiple exist in the sketch (default 0)
- `taper_angle` (float): Draft angle during extrusion in degrees (default 0)

### revolve
Revolve the most recent sketch profile around an axis to create rotational geometry.
- `angle` (float): Revolve angle in degrees (360 for full revolution)
- `axis` (str): Revolve axis - "X", "Y", or "Z" (default "Y")

## Advanced Features

### sweep
Sweep a sketch profile along a path curve to create pipes, channels, or curved extrusions.
- `profile_sketch_index` (int): Sketch containing the profile (default: second-to-last sketch)
- `profile_index` (int): Which profile in the sketch (default 0)
- `path_sketch_index` (int): Sketch containing the path curve (default: last sketch)
- `path_curve_index` (int): Which curve to use as path (default 0)
- `taper_angle` (float): Taper angle in degrees during sweep (default 0)
- `twist_angle` (float): Twist angle in degrees along sweep (default 0)
- `operation` (str): "new", "join", "cut", or "intersect" (default "new")

Profile and path must be in different sketches. Default behavior uses second-to-last sketch for profile, last sketch for path.

### loft
Loft between 2 or more sketch profiles to create smooth shape transitions.
- `sketch_indices` (list): List of sketch indices containing profiles (minimum 2, order matters)
- `profile_indices` (list): List of profile indices per sketch (default [0, 0, ...])
- `is_solid` (bool): Create solid body (True) or surface (False) (default True)
- `is_closed` (bool): Close the loft -- connect last section to first (default False)
- `operation` (str): "new", "join", "cut", or "intersect" (default "new")

Each profile must be in a different sketch on a different plane. Use `construction_plane()` to create offset planes for multi-section lofts.

### fillet
Add rounded edges (fillets) to a body.
- `radius` (float): Fillet radius
- `edges` (list): List of edge indices (optional -- if omitted, fillets all edges)
- `body_index` (int): Which body (default: most recent)

Use `get_body_info()` to see available edge indices.

### chamfer
Add beveled edges (chamfers) to a body.
- `distance` (float): Chamfer distance
- `edges` (list): List of edge indices (optional -- if omitted, chamfers all edges)
- `body_index` (int): Which body (default: most recent)

Use `get_body_info()` to see available edge indices.

### shell
Create a hollow shell from a solid body.
- `thickness` (float): Wall thickness
- `faces_to_remove` (list): List of face indices to remove, creating openings (optional -- default: closed shell)
- `body_index` (int): Which body (default: most recent)

Use `get_body_info()` to see available face indices.

### draft
Apply draft angles to faces for injection molding.
- `angle` (float): Draft angle (typically 0.5-3 degrees; guideline: 1 degree per inch of depth)
- `faces` (list): List of face indices (optional -- if omitted, drafts all faces)
- `body_index` (int): Which body (default: most recent)
- `pull_x` (float): Pull direction X component (default 0)
- `pull_y` (float): Pull direction Y component (default 0)
- `pull_z` (float): Pull direction Z component (default 1)

## Patterns

### pattern_rectangular
Create a rectangular (linear) pattern of a body.
- `x_count` (int): Number of instances in X direction
- `x_spacing` (float): Spacing between instances in X
- `y_count` (int): Number of instances in Y direction (default 1)
- `y_spacing` (float): Spacing between instances in Y (default 0)
- `body_index` (int): Which body (default: most recent)

### pattern_circular
Create a circular (radial) pattern of a body.
- `count` (int): Number of instances
- `angle` (float): Total angle in degrees (default 360 for full circle)
- `axis` (str): Rotation axis - "X", "Y", or "Z" (default "Z")
- `body_index` (int): Which body (default: most recent)

### mirror
Create a mirrored copy of a body.
- `plane` (str): Mirror plane - "XY", "XZ", or "YZ" (default "YZ" for left-right symmetry)
- `body_index` (int): Which body (default: most recent)

## Boolean Operations

### combine
Boolean operations: cut, join, or intersect bodies.
- `target_body` (int): Index of body to modify (0 = first body)
- `tool_bodies` (list): List of body indices to use as tools
- `operation` (str): "cut" (subtract), "join" (add), or "intersect" (default "cut")
- `keep_tools` (bool): If True, keep tool bodies after operation (default False)

Use `get_body_info()` to verify body indices before combining.

## Construction Geometry

### construction_plane
Create a construction (reference) plane for sketching or feature operations.
- `mode` (str): "offset" (parallel to base plane) or "angle" (rotated around axis) (default "offset")
- `plane` (str): Base plane - "XY", "XZ", or "YZ" (default "XY")
- `offset` (float): Distance from base plane in cm (used in offset mode, default 1.0)
- `axis` (str): Rotation axis for angle mode - "X", "Y", or "Z" (default "X")
- `angle` (float): Rotation angle in degrees (used in angle mode, default 45.0)

### construction_axis
Create a construction (reference) axis for patterns, revolves, or other operations.
- `mode` (str): Creation mode - "two_points" (default)
- `point1_x` (float): First point X (default 0)
- `point1_y` (float): First point Y (default 0)
- `point1_z` (float): First point Z (default 0)
- `point2_x` (float): Second point X (default 0)
- `point2_y` (float): Second point Y (default 0)
- `point2_z` (float): Second point Z (default 1.0)

### construction_point
Create a construction (reference) point for positioning holes, patterns, or other features.
- `x` (float): X coordinate (default 0)
- `y` (float): Y coordinate (default 0)
- `z` (float): Z coordinate (default 0)

## Manufacturing Features

### hole
Create a hole in a body face. Automatically creates a sketch point for positioning.
- `diameter` (float): Hole diameter
- `depth` (float): Hole depth (optional -- omit for through-all)
- `hole_type` (str): "simple", "counterbore", or "countersink" (default "simple")
- `x` (float): X position on face (default 0)
- `y` (float): Y position on face (default 0)
- `face` (int): Face index for hole placement (default: top face)
- `body_index` (int): Which body (default: most recent)
- `counterbore_diameter` (float): Required for counterbore type
- `counterbore_depth` (float): Required for counterbore type
- `countersink_diameter` (float): Required for countersink type
- `countersink_angle` (float): In degrees (default 82)

Use `get_body_info()` to find face indices.

### thread
Apply threads to a cylindrical face. The face must be cylindrical.
- `face` (int): Face index of the cylindrical face to thread
- `body_index` (int): Which body (default: most recent)
- `thread_type` (str): Thread standard (default "ISO Metric profile")
- `designation` (str): Thread size designation (default "M6x1.0"). Common: M3x0.5, M4x0.7, M5x0.8, M6x1.0, M8x1.25, M10x1.5, M12x1.75
- `thread_class` (str): Tolerance class (default "6g" for external, use "6H" for internal)
- `is_internal` (bool): True for internal threads (holes), False for external (default False)
- `full_length` (bool): Thread the full length of the face (default True)
- `length` (float): Thread length in cm (used when full_length is False)

## Parametric Design

### create_parameter
Create a named user parameter with an expression. Parameters can be referenced in other expressions.
- `name` (str): Parameter name (must be unique)
- `expression` (str): Value expression -- numeric ("5"), unit ("5 in"), or parameter reference ("width * 2")
- `unit` (str): Unit type (default "cm")
- `comment` (str): Optional description

### set_parameter
Update an existing parameter's expression. Triggers model regeneration.
- `name` (str): Parameter name (must exist -- use create_parameter first)
- `expression` (str): New expression value
