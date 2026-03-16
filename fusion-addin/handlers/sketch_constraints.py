import adsk.core
import adsk.fusion
import os
import sys

_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.sketch_entities import get_sketch_curve, get_sketch_point
from helpers.bodies import get_sketch


def constrain_horizontal(design, rootComp, params):
    """Constrain a sketch line to be horizontal."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    if curve_index is None:
        return {"success": False, "error": "curve_index is required"}

    try:
        curve = get_sketch_curve(sketch, curve_index)
        sketch.geometricConstraints.addHorizontal(curve)
        return {"success": True, "constraint_type": "horizontal"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_vertical(design, rootComp, params):
    """Constrain a sketch line to be vertical."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    if curve_index is None:
        return {"success": False, "error": "curve_index is required"}

    try:
        curve = get_sketch_curve(sketch, curve_index)
        sketch.geometricConstraints.addVertical(curve)
        return {"success": True, "constraint_type": "vertical"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_perpendicular(design, rootComp, params):
    """Constrain two sketch lines to be perpendicular."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    if curve_index is None or curve_index_2 is None:
        return {"success": False, "error": "curve_index and curve_index_2 are required"}

    try:
        curve1 = get_sketch_curve(sketch, curve_index)
        curve2 = get_sketch_curve(sketch, curve_index_2)
        sketch.geometricConstraints.addPerpendicular(curve1, curve2)
        return {"success": True, "constraint_type": "perpendicular"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_parallel(design, rootComp, params):
    """Constrain two sketch lines to be parallel."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    if curve_index is None or curve_index_2 is None:
        return {"success": False, "error": "curve_index and curve_index_2 are required"}

    try:
        curve1 = get_sketch_curve(sketch, curve_index)
        curve2 = get_sketch_curve(sketch, curve_index_2)
        sketch.geometricConstraints.addParallel(curve1, curve2)
        return {"success": True, "constraint_type": "parallel"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_tangent(design, rootComp, params):
    """Constrain two sketch curves to be tangent."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    if curve_index is None or curve_index_2 is None:
        return {"success": False, "error": "curve_index and curve_index_2 are required"}

    try:
        curve1 = get_sketch_curve(sketch, curve_index)
        curve2 = get_sketch_curve(sketch, curve_index_2)
        sketch.geometricConstraints.addTangent(curve1, curve2)
        return {"success": True, "constraint_type": "tangent"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_coincident(design, rootComp, params):
    """Constrain a sketch point to lie on a curve or coincide with another point."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    point_index = params.get("point_index")
    curve_index = params.get("curve_index")
    point_index_2 = params.get("point_index_2")

    if point_index is None:
        return {"success": False, "error": "point_index is required"}
    if curve_index is None and point_index_2 is None:
        return {"success": False, "error": "Either curve_index or point_index_2 is required"}

    try:
        point = get_sketch_point(sketch, point_index)
        if curve_index is not None:
            curve = get_sketch_curve(sketch, curve_index)
            sketch.geometricConstraints.addCoincident(point, curve)
        else:
            point2 = get_sketch_point(sketch, point_index_2)
            sketch.geometricConstraints.addCoincident(point, point2)
        return {"success": True, "constraint_type": "coincident"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_concentric(design, rootComp, params):
    """Constrain two circles or arcs to share the same center."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    if curve_index is None or curve_index_2 is None:
        return {"success": False, "error": "curve_index and curve_index_2 are required"}

    try:
        curve1 = get_sketch_curve(sketch, curve_index)
        curve2 = get_sketch_curve(sketch, curve_index_2)
        sketch.geometricConstraints.addConcentric(curve1, curve2)
        return {"success": True, "constraint_type": "concentric"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_equal(design, rootComp, params):
    """Constrain two sketch curves to have equal size."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    if curve_index is None or curve_index_2 is None:
        return {"success": False, "error": "curve_index and curve_index_2 are required"}

    try:
        curve1 = get_sketch_curve(sketch, curve_index)
        curve2 = get_sketch_curve(sketch, curve_index_2)
        sketch.geometricConstraints.addEqual(curve1, curve2)
        return {"success": True, "constraint_type": "equal"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def constrain_symmetric(design, rootComp, params):
    """Constrain two entities to be symmetric about a line."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    symmetry_curve_index = params.get("symmetry_curve_index")
    if symmetry_curve_index is None:
        return {"success": False, "error": "symmetry_curve_index is required"}

    curve_index = params.get("curve_index")
    curve_index_2 = params.get("curve_index_2")
    point_index = params.get("point_index")
    point_index_2 = params.get("point_index_2")

    try:
        sym_line = get_sketch_curve(sketch, symmetry_curve_index)

        # Try curve-based symmetry first
        if curve_index is not None and curve_index_2 is not None:
            entity1 = get_sketch_curve(sketch, curve_index)
            entity2 = get_sketch_curve(sketch, curve_index_2)
            sketch.geometricConstraints.addSymmetry(entity1, entity2, sym_line)
            return {"success": True, "constraint_type": "symmetric"}

        # Fall back to point-based symmetry
        if point_index is not None and point_index_2 is not None:
            entity1 = get_sketch_point(sketch, point_index)
            entity2 = get_sketch_point(sketch, point_index_2)
            sketch.geometricConstraints.addSymmetry(entity1, entity2, sym_line)
            return {"success": True, "constraint_type": "symmetric"}

        return {
            "success": False,
            "error": "Provide (curve_index + curve_index_2) or (point_index + point_index_2)"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
