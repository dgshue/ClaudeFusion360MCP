import adsk.core
import adsk.fusion
import math


def create_sketch(design, rootComp, params):
    plane_name = params.get('plane', 'XY')
    plane_map = {
        'XY': rootComp.xYConstructionPlane,
        'XZ': rootComp.xZConstructionPlane,
        'YZ': rootComp.yZConstructionPlane
    }
    plane = plane_map.get(plane_name)
    if not plane:
        return {"success": False, "error": f"Invalid plane '{plane_name}'. Use 'XY', 'XZ', or 'YZ'."}

    offset = params.get('offset', None)
    if offset is not None and offset != 0:
        planes = rootComp.constructionPlanes
        plane_input = planes.createInput()
        offset_val = adsk.core.ValueInput.createByReal(offset)
        plane_input.setByOffset(plane, offset_val)
        plane = planes.add(plane_input)

    sketch = rootComp.sketches.add(plane)
    return {"success": True, "sketch_name": sketch.name, "plane": plane_name}


def draw_line(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches - call create_sketch first"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    p1 = adsk.core.Point3D.create(params['x1'], params['y1'], 0)
    p2 = adsk.core.Point3D.create(params['x2'], params['y2'], 0)
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)
    return {"success": True, "line_length": line.length}


def draw_circle(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches - call create_sketch first"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    center = adsk.core.Point3D.create(params['center_x'], params['center_y'], 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, params['radius'])
    return {"success": True}


def draw_rectangle(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches - call create_sketch first"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    p1 = adsk.core.Point3D.create(params['x1'], params['y1'], 0)
    p2 = adsk.core.Point3D.create(params['x2'], params['y2'], 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
    return {"success": True}


def draw_arc(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches - call create_sketch first"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)

    center_x = params.get('center_x', 0)
    center_y = params.get('center_y', 0)
    radius = params.get('radius', 1)
    start_angle = math.radians(params.get('start_angle', 0))
    end_angle = math.radians(params.get('end_angle', 180))

    center = adsk.core.Point3D.create(center_x, center_y, 0)
    sweep_angle = end_angle - start_angle

    start_point = adsk.core.Point3D.create(
        center_x + radius * math.cos(start_angle),
        center_y + radius * math.sin(start_angle),
        0
    )

    arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
        center, start_point, sweep_angle
    )
    return {"success": True, "arc_length": arc.length}


def draw_polygon(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches - call create_sketch first"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)

    sides = params.get('sides', 6)
    center_x = params.get('center_x', 0)
    center_y = params.get('center_y', 0)
    radius = params.get('radius', 1)

    if sides < 3:
        return {"success": False, "error": "Polygon must have at least 3 sides"}

    points = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides - math.pi / 2  # start from top
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append(adsk.core.Point3D.create(x, y, 0))

    lines = sketch.sketchCurves.sketchLines
    for i in range(sides):
        lines.addByTwoPoints(points[i], points[(i + 1) % sides])

    return {"success": True, "sides": sides}


def finish_sketch(design, rootComp, params):
    return {"success": True, "message": "Sketch finished"}
