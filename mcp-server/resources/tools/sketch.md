# Sketch Tools Reference

All coordinates and dimensions are in **cm** (Fusion 360 internal unit).

## Sketch Lifecycle

### create_sketch
Create a new sketch and enter edit mode.
- `plane` (str): Construction plane - "XY", "XZ", or "YZ" (default "XY"). Ignored if face is provided.
- `offset` (float): Offset distance from plane in cm (default 0). Only for construction planes.
- `body_index` (int): Body to sketch on (0 = first body). Required with face.
- `face` (str): Face selector - semantic name ("top_face", "bottom_face") or integer index.

Use `get_body_info()` to see available faces when sketching on a body.

### finish_sketch
Exit sketch editing mode. Call this after completing all sketch geometry, constraints, and dimensions.

No parameters.

## Basic Drawing

### draw_line
Draw a straight line in the active sketch.
- `x1` (float): Start X
- `y1` (float): Start Y
- `x2` (float): End X
- `y2` (float): End Y

### draw_circle
Draw a circle in the active sketch.
- `center_x` (float): Center X
- `center_y` (float): Center Y
- `radius` (float): Circle radius

### draw_rectangle
Draw a rectangle from two opposite corner points in the active sketch.
- `x1` (float): First corner X
- `y1` (float): First corner Y
- `x2` (float): Opposite corner X
- `y2` (float): Opposite corner Y

Creates a four-line rectangle. The resulting profile can be extruded, revolved, or used for other operations.

### draw_arc
Draw an arc defined by center point, start point, and end point.
- `center_x` (float): Center X
- `center_y` (float): Center Y
- `start_x` (float): Start point X
- `start_y` (float): Start point Y
- `end_x` (float): End point X
- `end_y` (float): End point Y

### draw_polygon
Draw a regular polygon in the active sketch. Default is hexagon.
- `center_x` (float): Center X
- `center_y` (float): Center Y
- `radius` (float): Circumscribed radius
- `sides` (int): Number of sides (default 6)

## Primitives

### draw_spline
Draw a fitted spline through a collection of points.
- `points` (list): List of [x, y] coordinate pairs (minimum 2 points)

### draw_ellipse
Draw an ellipse in the active sketch.
- `center_x` (float): Center X
- `center_y` (float): Center Y
- `major_radius` (float): Semi-major axis length
- `minor_radius` (float): Semi-minor axis length
- `angle` (float): Rotation angle of major axis in degrees (default 0)

### draw_slot
Draw a center-point slot (rounded rectangle) in the active sketch.
- `center_x` (float): Slot center X
- `center_y` (float): Slot center Y
- `end_x` (float): End point X (defines slot length and direction)
- `end_y` (float): End point Y
- `width` (float): Slot width (perpendicular to length direction)

### draw_point
Add a reference/construction point to the active sketch.
- `x` (float): Point X
- `y` (float): Point Y

### draw_text
Draw text in the active sketch. Text profiles can be extruded for embossing/engraving.
- `text` (str): The text string to draw
- `height` (float): Text height in cm
- `x` (float): Text position X (default 0)
- `y` (float): Text position Y (default 0)
- `font` (str): Font name (optional, uses system default)

## Operations

### offset_curves
Create offset curves parallel to existing sketch geometry at a uniform distance.
- `curve_index` (int): Index of a curve to offset (connected curves are included automatically)
- `distance` (float): Offset distance in cm
- `direction_x` (float): X component of offset direction (default 0)
- `direction_y` (float): Y component of offset direction (default 1)

Use `get_sketch_info()` to see available curve indices.

### project_geometry
Project body edges or faces onto the active sketch plane.
- `body_index` (int): Which body to project from (default 0)
- `edge_index` (int): Specific edge index to project (optional)
- `face_index` (int): Specific face index to project (optional)

If neither edge_index nor face_index is provided, projects all edges. Use `get_body_info()` to see available edge/face indices.

### import_svg
Import an SVG file into the active sketch. Uses Fusion 360's native SVG import.
- `file_path` (str): Full path to the SVG file
- `x` (float): X position for import origin (default 0)
- `y` (float): Y position for import origin (default 0)
- `scale` (float): Scale factor (default 1.0 = native SVG dimensions)

### set_construction
Toggle a sketch curve between regular and construction geometry. Construction geometry is used as reference but not included in profiles.
- `curve_index` (int): Index of the curve to toggle
- `is_construction` (bool): True to make construction, False to make regular (default True)

## Constraints

### constrain_horizontal
Constrain a sketch line to be horizontal.
- `curve_index` (int): Index of the line to constrain

### constrain_vertical
Constrain a sketch line to be vertical.
- `curve_index` (int): Index of the line to constrain

### constrain_perpendicular
Constrain two sketch lines to be perpendicular (90 degrees).
- `curve_index` (int): First line index
- `curve_index_2` (int): Second line index

### constrain_parallel
Constrain two sketch lines to be parallel.
- `curve_index` (int): First line index
- `curve_index_2` (int): Second line index

### constrain_tangent
Constrain two sketch curves to be tangent at their nearest endpoints.
- `curve_index` (int): First curve index (line, arc, circle, or spline)
- `curve_index_2` (int): Second curve index

### constrain_coincident
Constrain a sketch point to lie on a curve or coincide with another point.
- `point_index` (int): The point to constrain
- `curve_index` (int): Target curve (optional)
- `point_index_2` (int): Target point (optional)

Provide either `curve_index` or `point_index_2`, not both.

### constrain_concentric
Constrain two circles or arcs to share the same center point.
- `curve_index` (int): First circle/arc index
- `curve_index_2` (int): Second circle/arc index

### constrain_equal
Constrain two sketch curves to have equal size (lines: same length, circles: same radius).
- `curve_index` (int): First curve index
- `curve_index_2` (int): Second curve index (must be same type as first)

### constrain_symmetric
Constrain two entities to be symmetric about a line.
- `symmetry_curve_index` (int): The line of symmetry
- `curve_index` (int): First curve (optional)
- `curve_index_2` (int): Second curve (optional)
- `point_index` (int): First point (optional)
- `point_index_2` (int): Second point (optional)

Provide either (curve_index + curve_index_2) or (point_index + point_index_2).

## Dimensions

### dimension_distance
Add a distance dimension to constrain length between two points or along a curve.
- `value` (float): Dimension value in cm (required -- dimensions drive geometry)
- `curve_index` (int): Line to dimension (optional)
- `point_index` (int): First point (optional)
- `point_index_2` (int): Second point (optional)

Provide either `curve_index` or (`point_index` + `point_index_2`).

### dimension_radial
Add a diameter or radius dimension to a circle or arc.
- `curve_index` (int): Index of the circle or arc to dimension
- `value` (float): Dimension value in cm (diameter or radius depending on type)
- `type` (str): "diameter" or "radius" (default "diameter")

### dimension_angular
Add an angular dimension between two sketch lines.
- `curve_index` (int): First line index
- `curve_index_2` (int): Second line index
- `value` (float): Angle value in degrees

## Query

### get_sketch_info
Get detailed information about the active sketch including all curves, points, constraints, and dimensions.

No parameters. Returns curves with semantic labels, points with coordinates, geometric constraints, parametric dimensions, and overall constraint status.

Use this to understand sketch state before applying constraints, dimensions, or other operations.
