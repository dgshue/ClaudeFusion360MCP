import adsk.core
import adsk.fusion
import os
import sys

_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.coordinates import transform_to_sketch_coords
from helpers.bodies import get_sketch, get_body
from helpers.sketch_entities import get_sketch_curve, get_curve_index


def offset_curves(design, rootComp, params):
    """Create offset curves parallel to existing sketch geometry."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    try:
        source_curve = get_sketch_curve(sketch, params['curve_index'])
    except ValueError as e:
        return {"success": False, "error": str(e)}

    distance = params['distance']
    dir_x = params.get('direction_x', 0)
    dir_y = params.get('direction_y', 1)

    # Find connected curves for the offset operation
    curves = sketch.findConnectedCurves(source_curve)

    # Compute direction point from source curve midpoint + direction offset
    eval_result = source_curve.geometry.evaluator
    _, start_param, end_param = eval_result.getParameterExtents()
    mid_param = (start_param + end_param) / 2
    _, mid_point = eval_result.getPointAtParameter(mid_param)

    dir_point = adsk.core.Point3D.create(
        mid_point.x + dir_x,
        mid_point.y + dir_y,
        0
    )

    curves_before = sketch.sketchCurves.count
    sketch.offset(curves, dir_point, distance)
    curves_after = sketch.sketchCurves.count

    return {
        "success": True,
        "offset_count": curves_after - curves_before
    }


def project_geometry(design, rootComp, params):
    """Project body edges or faces onto the active sketch plane."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    body_index = params.get('body_index', 0)
    edge_index = params.get('edge_index', None)
    face_index = params.get('face_index', None)

    try:
        body = get_body(rootComp, body_index)
    except (ValueError, IndexError) as e:
        return {"success": False, "error": str(e)}

    projected_count = 0

    if edge_index is not None:
        if edge_index < 0 or edge_index >= body.edges.count:
            return {"success": False, "error": f"Edge index {edge_index} out of range (0-{body.edges.count - 1})"}
        sketch.project(body.edges.item(edge_index))
        projected_count = 1
    elif face_index is not None:
        if face_index < 0 or face_index >= body.faces.count:
            return {"success": False, "error": f"Face index {face_index} out of range (0-{body.faces.count - 1})"}
        sketch.project(body.faces.item(face_index))
        projected_count = 1
    else:
        # Project all edges
        for i in range(body.edges.count):
            sketch.project(body.edges.item(i))
            projected_count += 1

    return {
        "success": True,
        "projected_count": projected_count
    }


def import_svg(design, rootComp, params):
    """Import an SVG file into the active sketch."""
    try:
        sketch = get_sketch(rootComp)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    file_path = params['file_path']
    x = params.get('x', 0)
    y = params.get('y', 0)
    scale = params.get('scale', 1.0)

    if not os.path.isfile(file_path):
        return {"success": False, "error": f"SVG file not found: {file_path}"}

    x, y = transform_to_sketch_coords(x, y, sketch)

    sketch.importSVG(file_path, x, y, scale)

    return {
        "success": True,
        "file_path": file_path,
        "scale": scale
    }
