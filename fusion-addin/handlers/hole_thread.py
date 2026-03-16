import adsk.core
import adsk.fusion

import os
import sys
_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.bodies import get_body
from helpers.selection import resolve_faces


def hole(design, rootComp, params):
    """Create a hole feature (simple, counterbore, or countersink) with auto sketch point positioning."""
    diameter = params['diameter']
    depth = params.get('depth')
    hole_type = params.get('hole_type', 'simple')
    x = params.get('x', 0)
    y = params.get('y', 0)

    # Get target body
    body = get_body(rootComp, params.get('body_index'))

    # Determine target face for hole placement
    if 'face' in params:
        target_face = resolve_faces(body, [params['face']])[0]
    else:
        # Default to top face (last planar face, heuristic)
        target_face = body.faces.item(body.faces.count - 1)

    # Auto-create sketch on target face with a sketch point at (x, y)
    sketch = rootComp.sketches.add(target_face)
    pt = sketch.sketchPoints.add(adsk.core.Point3D.create(x, y, 0))

    ptColl = adsk.core.ObjectCollection.create()
    ptColl.add(pt)

    # Create hole input based on type
    holes = rootComp.features.holeFeatures
    diameter_val = adsk.core.ValueInput.createByReal(diameter)

    if hole_type == 'simple':
        hole_input = holes.createSimpleInput(diameter_val)
    elif hole_type == 'counterbore':
        cb_diameter = params.get('counterbore_diameter')
        cb_depth = params.get('counterbore_depth')
        if cb_diameter is None or cb_depth is None:
            return {
                "success": False,
                "error": "counterbore_diameter and counterbore_depth are required for counterbore hole type"
            }
        cb_diameter_val = adsk.core.ValueInput.createByReal(cb_diameter)
        cb_depth_val = adsk.core.ValueInput.createByReal(cb_depth)
        hole_input = holes.createCounterboreInput(diameter_val, cb_diameter_val, cb_depth_val)
    elif hole_type == 'countersink':
        cs_diameter = params.get('countersink_diameter')
        if cs_diameter is None:
            return {
                "success": False,
                "error": "countersink_diameter is required for countersink hole type"
            }
        cs_diameter_val = adsk.core.ValueInput.createByReal(cs_diameter)
        cs_angle = params.get('countersink_angle', 82)
        cs_angle_val = adsk.core.ValueInput.createByString(f"{cs_angle} deg")
        hole_input = holes.createCountersinkInput(diameter_val, cs_diameter_val, cs_angle_val)
    else:
        return {
            "success": False,
            "error": f"Unknown hole_type '{hole_type}'. Use 'simple', 'counterbore', or 'countersink'."
        }

    # Set position by sketch points
    hole_input.setPositionBySketchPoints(ptColl)

    # Set extent
    if depth is not None:
        hole_input.setDistanceExtent(adsk.core.ValueInput.createByReal(depth))
    else:
        hole_input.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)

    feat = holes.add(hole_input)
    return {"success": True, "feature_name": feat.name, "hole_type": hole_type}


def thread(design, rootComp, params):
    """Apply threads to a cylindrical face using ThreadDataQuery for valid specifications."""
    if 'face' not in params:
        return {"success": False, "error": "face parameter is required. Use get_body_info() to find cylindrical face indices."}

    # Get body and resolve face
    body = get_body(rootComp, params.get('body_index'))
    target_face = resolve_faces(body, [params['face']])[0]

    thread_type = params.get('thread_type', 'ISO Metric profile')
    designation = params.get('designation', 'M6x1.0')
    thread_class = params.get('thread_class', '6g')
    is_internal = params.get('is_internal', False)
    full_length = params.get('full_length', True)

    try:
        threadFeats = rootComp.features.threadFeatures
        threadInfo = threadFeats.createThreadInfo(is_internal, thread_type, designation, thread_class)

        faces_collection = adsk.core.ObjectCollection.create()
        faces_collection.add(target_face)

        threadInput = threadFeats.createInput(faces_collection, threadInfo)
        threadInput.isFullLength = full_length

        if not full_length and 'length' in params:
            threadInput.threadLength = adsk.core.ValueInput.createByReal(params['length'])

        feat = threadFeats.add(threadInput)
        return {
            "success": True,
            "feature_name": feat.name,
            "thread_type": thread_type,
            "designation": designation
        }
    except Exception as e:
        error_msg = str(e)
        if 'cylindrical' in error_msg.lower() or 'invalid' in error_msg.lower():
            return {
                "success": False,
                "error": f"Thread can only be applied to cylindrical faces. Use get_body_info() to identify cylindrical faces. Detail: {error_msg}"
            }
        raise
