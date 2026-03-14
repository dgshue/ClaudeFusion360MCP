import adsk.core
import adsk.fusion
import math
import os
import sys

_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.coordinates import transform_to_sketch_coords, transform_from_sketch_coords
from helpers.bodies import get_sketch
from helpers.sketch_entities import get_curve_index, find_point_index, get_sketch_curve


def create_sketch(design, rootComp, params):
    plane_name = params.get('plane', 'XY')
    plane_map = {
        'XY': rootComp.xYConstructionPlane,
        'XZ': rootComp.xZConstructionPlane,
        'YZ': rootComp.yZConstructionPlane
    }
    base_plane = plane_map.get(plane_name)
    if not base_plane:
        return {"success": False, "error": f"Invalid plane '{plane_name}'. Use 'XY', 'XZ', or 'YZ'."}

    plane = base_plane
    offset = params.get('offset', 0)
    if offset != 0:
        planes = rootComp.constructionPlanes
        plane_input = planes.createInput()
        offset_val = adsk.core.ValueInput.createByReal(offset)
        plane_input.setByOffset(base_plane, offset_val)
        plane = planes.add(plane_input)

    sketch = rootComp.sketches.add(plane)
    # Store base plane name in sketch attributes so coordinate correction
    # can detect XZ plane even on offset construction planes
    sketch.attributes.add('FusionMCP', 'base_plane', plane_name)
    return {"success": True, "sketch_name": sketch.name, "plane": plane_name}


def draw_line(design, rootComp, params):
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    x1, y1 = transform_to_sketch_coords(params['x1'], params['y1'], sketch)
    x2, y2 = transform_to_sketch_coords(params['x2'], params['y2'], sketch)
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)

    rx1, ry1 = transform_from_sketch_coords(p1.x, p1.y, sketch)
    rx2, ry2 = transform_from_sketch_coords(p2.x, p2.y, sketch)
    return {
        "success": True,
        "line_length": line.length,
        "start": [rx1, ry1],
        "end": [rx2, ry2],
        "curve_index": get_curve_index(sketch, line),
        "start_point_index": find_point_index(sketch, line.startSketchPoint),
        "end_point_index": find_point_index(sketch, line.endSketchPoint)
    }


def draw_circle(design, rootComp, params):
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    cx, cy = transform_to_sketch_coords(params['center_x'], params['center_y'], sketch)
    center = adsk.core.Point3D.create(cx, cy, 0)
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, params['radius'])

    rcx, rcy = transform_from_sketch_coords(center.x, center.y, sketch)
    return {
        "success": True,
        "center": [rcx, rcy],
        "radius": params['radius'],
        "curve_index": get_curve_index(sketch, circle)
    }


def draw_rectangle(design, rootComp, params):
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    x1, y1 = transform_to_sketch_coords(params['x1'], params['y1'], sketch)
    x2, y2 = transform_to_sketch_coords(params['x2'], params['y2'], sketch)
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    rect_lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)

    curve_indices = []
    point_indices = []
    seen_points = set()
    for i in range(rect_lines.count):
        line = rect_lines.item(i)
        curve_indices.append(get_curve_index(sketch, line))
        for pt in [line.startSketchPoint, line.endSketchPoint]:
            pi = find_point_index(sketch, pt)
            if pi not in seen_points:
                seen_points.add(pi)
                point_indices.append(pi)

    rx1, ry1 = transform_from_sketch_coords(p1.x, p1.y, sketch)
    rx2, ry2 = transform_from_sketch_coords(p2.x, p2.y, sketch)
    return {
        "success": True,
        "corner1": [rx1, ry1],
        "corner2": [rx2, ry2],
        "curve_indices": curve_indices,
        "point_indices": point_indices
    }


def draw_arc(design, rootComp, params):
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # MCP server sends center_x, center_y, start_x, start_y, end_x, end_y
    center_x, center_y = transform_to_sketch_coords(
        params['center_x'], params['center_y'], sketch
    )
    start_x, start_y = transform_to_sketch_coords(
        params['start_x'], params['start_y'], sketch
    )
    end_x, end_y = transform_to_sketch_coords(
        params['end_x'], params['end_y'], sketch
    )

    center = adsk.core.Point3D.create(center_x, center_y, 0)
    start_point = adsk.core.Point3D.create(start_x, start_y, 0)

    # Compute sweep angle from center-to-start and center-to-end vectors
    dx_start = start_x - center_x
    dy_start = start_y - center_y
    dx_end = end_x - center_x
    dy_end = end_y - center_y

    angle_start = math.atan2(dy_start, dx_start)
    angle_end = math.atan2(dy_end, dx_end)
    sweep_angle = angle_end - angle_start
    # Ensure positive sweep (counterclockwise)
    if sweep_angle <= 0:
        sweep_angle += 2 * math.pi

    arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
        center, start_point, sweep_angle
    )

    rcx, rcy = transform_from_sketch_coords(center_x, center_y, sketch)
    rsx, rsy = transform_from_sketch_coords(start_x, start_y, sketch)
    return {
        "success": True,
        "arc_length": arc.length,
        "center": [rcx, rcy],
        "start": [rsx, rsy],
        "curve_index": get_curve_index(sketch, arc),
        "start_point_index": find_point_index(sketch, arc.startSketchPoint),
        "end_point_index": find_point_index(sketch, arc.endSketchPoint)
    }


def draw_polygon(design, rootComp, params):
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    sides = params.get('sides', 6)
    if sides < 3:
        return {"success": False, "error": "Polygon must have at least 3 sides"}

    cx, cy = transform_to_sketch_coords(
        params['center_x'], params['center_y'], sketch
    )
    radius = params['radius']

    points = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        points.append(adsk.core.Point3D.create(px, py, 0))

    lines = sketch.sketchCurves.sketchLines
    curve_indices = []
    for i in range(sides):
        line = lines.addByTwoPoints(points[i], points[(i + 1) % sides])
        curve_indices.append(get_curve_index(sketch, line))

    rcx, rcy = transform_from_sketch_coords(cx, cy, sketch)
    return {
        "success": True,
        "sides": sides,
        "center": [rcx, rcy],
        "curve_indices": curve_indices
    }


def set_construction(design, rootComp, params):
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    curve = get_sketch_curve(sketch, params['curve_index'])
    is_construction = params.get('is_construction', True)
    curve.isConstruction = is_construction
    return {
        "success": True,
        "curve_index": params['curve_index'],
        "is_construction": curve.isConstruction
    }


def finish_sketch(design, rootComp, params):
    return {"success": True, "message": "Sketch finished"}
