import adsk.core
import adsk.fusion
import math
import os
import sys

_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.sketch_entities import get_sketch_curve, get_sketch_point
from helpers.bodies import get_sketch


def dimension_distance(design, rootComp, params):
    """Add a distance dimension between two points or along a curve."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    value = params.get("value")
    if value is None:
        return {"success": False, "error": "value is required (dimension must drive geometry)"}

    curve_index = params.get("curve_index")
    point_index = params.get("point_index")
    point_index_2 = params.get("point_index_2")

    try:
        if curve_index is not None:
            # Dimension along a curve using its start and end points
            curve = get_sketch_curve(sketch, curve_index)
            pt1 = curve.startSketchPoint
            pt2 = curve.endSketchPoint
        elif point_index is not None and point_index_2 is not None:
            # Dimension between two points
            pt1 = get_sketch_point(sketch, point_index)
            pt2 = get_sketch_point(sketch, point_index_2)
        else:
            return {
                "success": False,
                "error": "Provide curve_index OR (point_index + point_index_2)"
            }

        # Auto-calculate text position: midpoint + 1cm offset
        g1 = pt1.geometry
        g2 = pt2.geometry
        mid_x = (g1.x + g2.x) / 2.0
        mid_y = (g1.y + g2.y) / 2.0

        # Offset perpendicular to the line between points
        dx = g2.x - g1.x
        dy = g2.y - g1.y
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0.001:
            # Perpendicular offset (rotate 90 degrees)
            offset_x = -dy / length
            offset_y = dx / length
        else:
            offset_x = 0.0
            offset_y = 1.0

        text_pt = adsk.core.Point3D.create(mid_x + offset_x, mid_y + offset_y, 0)

        orientation = adsk.fusion.DimensionOrientations.AlignedDimensionOrientation
        dim = sketch.sketchDimensions.addDistanceDimension(
            pt1, pt2, orientation, text_pt
        )
        dim.parameter.value = value

        return {
            "success": True,
            "dimension_type": "distance",
            "value": value,
            "parameter_name": dim.parameter.name
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dimension_radial(design, rootComp, params):
    """Add a diameter or radius dimension to a circle or arc."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    value = params.get("value")
    dim_type = params.get("type", "diameter")

    if curve_index is None:
        return {"success": False, "error": "curve_index is required"}
    if value is None:
        return {"success": False, "error": "value is required (dimension must drive geometry)"}

    try:
        curve = get_sketch_curve(sketch, curve_index)

        # Auto-calculate text position: center + radius + 1cm offset
        if isinstance(curve, adsk.fusion.SketchCircle):
            center = curve.centerSketchPoint.geometry
            r = curve.radius
        elif isinstance(curve, adsk.fusion.SketchArc):
            center = curve.centerSketchPoint.geometry
            r = curve.radius
        else:
            return {"success": False, "error": "Curve must be a circle or arc for radial dimension"}

        text_pt = adsk.core.Point3D.create(center.x + r + 1.0, center.y, 0)

        if dim_type == "radius":
            dim = sketch.sketchDimensions.addRadialDimension(curve, text_pt)
        else:
            dim = sketch.sketchDimensions.addDiameterDimension(curve, text_pt)

        dim.parameter.value = value

        return {
            "success": True,
            "dimension_type": dim_type,
            "value": value,
            "parameter_name": dim.parameter.name
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dimension_angular(design, rootComp, params):
    """Add an angular dimension between two sketch lines."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    value = params.get("value")

    if curve_index is None or curve_index_2 is None:
        return {"success": False, "error": "curve_index and curve_index_2 are required"}
    if value is None:
        return {"success": False, "error": "value is required (angle in degrees)"}

    try:
        curve1 = get_sketch_curve(sketch, curve_index)
        curve2 = get_sketch_curve(sketch, curve_index_2)

        # Auto-calculate text position: midpoint of both curves' midpoints + 1cm offset
        g1s = curve1.startSketchPoint.geometry
        g1e = curve1.endSketchPoint.geometry
        g2s = curve2.startSketchPoint.geometry
        g2e = curve2.endSketchPoint.geometry

        mid_x = (g1s.x + g1e.x + g2s.x + g2e.x) / 4.0
        mid_y = (g1s.y + g1e.y + g2s.y + g2e.y) / 4.0
        text_pt = adsk.core.Point3D.create(mid_x + 1.0, mid_y + 1.0, 0)

        dim = sketch.sketchDimensions.addAngularDimension(curve1, curve2, text_pt)
        dim.parameter.value = math.radians(value)

        return {
            "success": True,
            "dimension_type": "angular",
            "value": value,
            "parameter_name": dim.parameter.name
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
