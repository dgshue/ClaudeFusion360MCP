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
from helpers.sketch_entities import get_curve_index, find_point_index


def draw_spline(design, rootComp, params):
    """Draw a fitted spline through a collection of points."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    points = params.get('points', [])
    if len(points) < 2:
        return {"success": False, "error": "Spline requires at least 2 points"}

    points_collection = adsk.core.ObjectCollection.create()
    for pt in points:
        x, y = transform_to_sketch_coords(pt[0], pt[1], sketch)
        points_collection.add(adsk.core.Point3D.create(x, y, 0))

    spline = sketch.sketchCurves.sketchFittedSplines.add(points_collection)

    return {
        "success": True,
        "curve_index": get_curve_index(sketch, spline),
        "point_count": len(points)
    }


def draw_ellipse(design, rootComp, params):
    """Draw an ellipse defined by center, major radius, minor radius, and rotation angle."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    cx, cy = transform_to_sketch_coords(params['center_x'], params['center_y'], sketch)
    major_radius = params['major_radius']
    minor_radius = params['minor_radius']
    angle_deg = params.get('angle', 0)
    angle_rad = math.radians(angle_deg)

    center = adsk.core.Point3D.create(cx, cy, 0)

    # Major axis point along the angle direction
    major_x = cx + major_radius * math.cos(angle_rad)
    major_y = cy + major_radius * math.sin(angle_rad)
    major_axis_pt = adsk.core.Point3D.create(major_x, major_y, 0)

    # Minor axis point perpendicular to the angle direction
    minor_x = cx + minor_radius * math.cos(angle_rad + math.pi / 2)
    minor_y = cy + minor_radius * math.sin(angle_rad + math.pi / 2)
    minor_axis_pt = adsk.core.Point3D.create(minor_x, minor_y, 0)

    ellipse = sketch.sketchCurves.sketchEllipses.add(center, major_axis_pt, minor_axis_pt)

    rcx, rcy = transform_from_sketch_coords(cx, cy, sketch)
    return {
        "success": True,
        "curve_index": get_curve_index(sketch, ellipse),
        "center": [rcx, rcy],
        "major_radius": major_radius,
        "minor_radius": minor_radius
    }


def draw_slot(design, rootComp, params):
    """Draw a center-point slot with specified width."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    cx, cy = transform_to_sketch_coords(params['center_x'], params['center_y'], sketch)
    ex, ey = transform_to_sketch_coords(params['end_x'], params['end_y'], sketch)
    width = params['width']

    center_pt = adsk.core.Point3D.create(cx, cy, 0)
    end_pt = adsk.core.Point3D.create(ex, ey, 0)
    width_val = adsk.core.ValueInput.createByReal(width)

    slot_curves = sketch.sketchCurves.addCenterPointSlot(center_pt, end_pt, width_val)

    curve_indices = []
    for i in range(slot_curves.count):
        curve = slot_curves.item(i)
        curve_indices.append(get_curve_index(sketch, curve))

    return {
        "success": True,
        "curve_indices": curve_indices,
        "width": width
    }


def draw_point(design, rootComp, params):
    """Add a reference point to the active sketch."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    x, y = transform_to_sketch_coords(params['x'], params['y'], sketch)
    point = sketch.sketchPoints.add(adsk.core.Point3D.create(x, y, 0))

    return {
        "success": True,
        "point_index": find_point_index(sketch, point)
    }


def draw_text(design, rootComp, params):
    """Draw extrudable text in the active sketch."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    text_str = params['text']
    height = params['height']
    x = params.get('x', 0)
    y = params.get('y', 0)
    font = params.get('font', None)

    x, y = transform_to_sketch_coords(x, y, sketch)

    texts = sketch.sketchTexts
    input = texts.createInput2(text_str, height)

    corner1 = adsk.core.Point3D.create(x, y, 0)
    corner2 = adsk.core.Point3D.create(x + height * len(text_str) * 0.6, y + height, 0)

    input.setAsMultiLine(
        corner1, corner2,
        adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
        adsk.core.VerticalAlignments.BottomVerticalAlignment,
        0
    )

    if font is not None:
        input.fontName = font

    texts.add(input)

    return {
        "success": True,
        "text": text_str,
        "height": height
    }
