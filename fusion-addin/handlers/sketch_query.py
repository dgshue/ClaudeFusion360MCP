import adsk.core
import adsk.fusion

import os
import sys
_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.sketch_entities import label_curve
from helpers.bodies import get_sketch
from helpers.coordinates import transform_from_sketch_coords


def get_sketch_info(design, rootComp, params):
    """Get detailed information about the active sketch including all curves,
    points, constraints, dimensions, and constraint status."""

    sketch = get_sketch(rootComp)

    # Sketch metadata
    sketch_name = sketch.name
    plane = "unknown"
    try:
        attr = sketch.attributes.itemByName('FusionMCP', 'base_plane')
        if attr and attr.value:
            plane = attr.value
    except Exception:
        pass

    # 1. Curves
    curves = []
    fully_constrained_count = 0
    non_construction_count = 0
    for i in range(sketch.sketchCurves.count):
        curve = sketch.sketchCurves.item(i)
        is_construction = curve.isConstruction
        is_fully_constrained = curve.isFullyConstrained

        if not is_construction:
            non_construction_count += 1
            if is_fully_constrained:
                fully_constrained_count += 1

        curves.append({
            "index": i,
            "label": label_curve(curve, i),
            "is_construction": is_construction,
            "is_fully_constrained": is_fully_constrained,
            "type": type(curve).__name__
        })

    # 2. Points
    points = []
    for i in range(sketch.sketchPoints.count):
        pt = sketch.sketchPoints.item(i)
        geom = pt.geometry
        wx, wy = transform_from_sketch_coords(geom.x, geom.y, sketch)
        label = "origin" if i == 0 else f"point {i}"
        points.append({
            "index": i,
            "x": round(wx, 4),
            "y": round(wy, 4),
            "is_origin": i == 0,
            "label": label
        })

    # 3. Constraints
    constraints = []
    for i in range(sketch.geometricConstraints.count):
        try:
            constraint = sketch.geometricConstraints.item(i)
            class_name = type(constraint).__name__
            # Extract constraint type word from class name
            # e.g., "HorizontalConstraint" -> "horizontal"
            constraint_type = class_name
            if class_name.endswith("Constraint"):
                constraint_type = class_name[:-len("Constraint")]
            constraint_type = constraint_type[0].lower() + constraint_type[1:]

            constraints.append({
                "index": i,
                "type": constraint_type,
                "class": class_name
            })
        except Exception:
            constraints.append({
                "index": i,
                "type": "unknown",
                "class": "unknown"
            })

    # 4. Dimensions
    dimensions = []
    for i in range(sketch.sketchDimensions.count):
        try:
            dim = sketch.sketchDimensions.item(i)
            class_name = type(dim).__name__
            dim_value = None
            param_name = None
            try:
                dim_value = dim.parameter.value
                param_name = dim.parameter.name
            except Exception:
                pass

            dimensions.append({
                "index": i,
                "type": class_name,
                "value": dim_value,
                "parameter_name": param_name
            })
        except Exception:
            dimensions.append({
                "index": i,
                "type": "unknown",
                "value": None,
                "parameter_name": None
            })

    # 5. Constraint status
    if non_construction_count == 0:
        constraint_status = "no geometry"
    elif fully_constrained_count == non_construction_count:
        constraint_status = "fully constrained"
    else:
        constraint_status = "under-constrained"

    return {
        "success": True,
        "sketch_name": sketch_name,
        "plane": plane,
        "curves": curves,
        "points": points,
        "constraints": constraints,
        "dimensions": dimensions,
        "summary": {
            "curve_count": sketch.sketchCurves.count,
            "point_count": sketch.sketchPoints.count,
            "constraint_count": sketch.geometricConstraints.count,
            "dimension_count": sketch.sketchDimensions.count,
            "fully_constrained_curves": fully_constrained_count,
            "constraint_status": constraint_status
        }
    }
