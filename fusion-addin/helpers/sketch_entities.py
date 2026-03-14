import adsk.core
import adsk.fusion
import math
import os
import sys

_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)


def get_sketch_curve(sketch, curve_index):
    """Get a SketchCurve by index from the sketch's curve collection.

    Args:
        sketch: The Sketch object
        curve_index: Integer index into sketch.sketchCurves

    Returns:
        SketchCurve object

    Raises:
        ValueError: If index is out of range
    """
    if curve_index < 0 or curve_index >= sketch.sketchCurves.count:
        raise ValueError(
            f"Curve index {curve_index} out of range. "
            f"Sketch has {sketch.sketchCurves.count} curves (0-{sketch.sketchCurves.count - 1}). "
            f"Use get_sketch_info() to see available curves."
        )
    return sketch.sketchCurves.item(curve_index)


def get_sketch_point(sketch, point_index):
    """Get a SketchPoint by index from the sketch's point collection.

    Note: index 0 is typically the origin point.

    Args:
        sketch: The Sketch object
        point_index: Integer index into sketch.sketchPoints

    Returns:
        SketchPoint object

    Raises:
        ValueError: If index is out of range
    """
    if point_index < 0 or point_index >= sketch.sketchPoints.count:
        raise ValueError(
            f"Point index {point_index} out of range. "
            f"Sketch has {sketch.sketchPoints.count} points (0-{sketch.sketchPoints.count - 1}). "
            f"Use get_sketch_info() to see available points."
        )
    return sketch.sketchPoints.item(point_index)


def get_curve_index(sketch, curve):
    """Find the index of a SketchCurve in the sketch's curve collection.

    Iterates sketch.sketchCurves comparing object references.

    Args:
        sketch: The Sketch object
        curve: The SketchCurve to find

    Returns:
        Integer index, or -1 if not found
    """
    for i in range(sketch.sketchCurves.count):
        if sketch.sketchCurves.item(i) == curve:
            return i
    return -1


def find_point_index(sketch, sketch_point):
    """Find the index of a SketchPoint in the sketch's point collection.

    Iterates sketch.sketchPoints comparing object references.

    Args:
        sketch: The Sketch object
        sketch_point: The SketchPoint to find

    Returns:
        Integer index, or -1 if not found
    """
    for i in range(sketch.sketchPoints.count):
        if sketch.sketchPoints.item(i) == sketch_point:
            return i
    return -1


def label_curve(curve, index):
    """Generate a semantic label string for a sketch curve.

    Uses isinstance checks to determine curve type and includes
    relevant dimensions. Appends ' construction' if the curve
    is construction geometry.

    Args:
        curve: The SketchCurve object
        index: The curve's integer index

    Returns:
        String label like "Curve 0 (line, horizontal, 5.00cm)"
    """
    suffix = ""
    if curve.isConstruction:
        suffix = " construction"

    if isinstance(curve, adsk.fusion.SketchLine):
        length = round(curve.length, 2)
        start = curve.startSketchPoint.geometry
        end = curve.endSketchPoint.geometry
        dx = abs(end.x - start.x)
        dy = abs(end.y - start.y)
        if dy < 0.001:
            orientation = "horizontal"
        elif dx < 0.001:
            orientation = "vertical"
        else:
            orientation = "diagonal"
        return f"Curve {index} (line, {orientation}, {length}cm){suffix}"

    if isinstance(curve, adsk.fusion.SketchCircle):
        r = round(curve.radius, 2)
        return f"Curve {index} (circle, radius {r}cm){suffix}"

    if isinstance(curve, adsk.fusion.SketchArc):
        r = round(curve.radius, 2)
        sweep = round(math.degrees(curve.sweepAngle), 2)
        return f"Curve {index} (arc, radius {r}cm, {sweep}deg){suffix}"

    if isinstance(curve, adsk.fusion.SketchEllipse):
        major = round(curve.majorAxisRadius, 2)
        minor = round(curve.minorAxisRadius, 2)
        return f"Curve {index} (ellipse, {major}x{minor}cm){suffix}"

    if isinstance(curve, adsk.fusion.SketchFittedSpline):
        n = curve.fitPoints.count
        return f"Curve {index} (spline, {n} points){suffix}"

    # Fallback for unknown curve types
    classname = type(curve).__name__
    return f"Curve {index} ({classname}){suffix}"
