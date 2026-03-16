import adsk.core
import adsk.fusion

import os
import sys
_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)


def construction_plane(design, rootComp, params):
    """Create a construction (reference) plane for sketching or feature operations.

    Modes:
        offset - Create plane parallel to a base plane at a given distance
        angle  - Create plane rotated around an axis relative to a base plane
    """
    mode = params.get('mode', 'offset')

    plane_map = {
        'XY': rootComp.xYConstructionPlane,
        'XZ': rootComp.xZConstructionPlane,
        'YZ': rootComp.yZConstructionPlane,
    }

    planes = rootComp.constructionPlanes
    plane_input = planes.createInput()

    if mode == 'offset':
        plane_name = params.get('plane', 'XY').upper()
        base_plane = plane_map.get(plane_name)
        if base_plane is None:
            return {"success": False, "error": f"Unknown plane '{plane_name}'. Use XY, XZ, or YZ."}

        offset = params.get('offset', 1.0)
        offset_value = adsk.core.ValueInput.createByReal(offset)
        plane_input.setByOffset(base_plane, offset_value)

    elif mode == 'angle':
        plane_name = params.get('plane', 'XY').upper()
        base_plane = plane_map.get(plane_name)
        if base_plane is None:
            return {"success": False, "error": f"Unknown plane '{plane_name}'. Use XY, XZ, or YZ."}

        axis_name = params.get('axis', 'X').upper()
        axis_map = {
            'X': rootComp.xConstructionAxis,
            'Y': rootComp.yConstructionAxis,
            'Z': rootComp.zConstructionAxis,
        }
        axis = axis_map.get(axis_name)
        if axis is None:
            return {"success": False, "error": f"Unknown axis '{axis_name}'. Use X, Y, or Z."}

        angle = params.get('angle', 45.0)
        angle_value = adsk.core.ValueInput.createByString(f"{angle} deg")
        plane_input.setByAngle(axis, angle_value, base_plane)

    else:
        return {"success": False, "error": f"Unknown mode '{mode}'. Use 'offset' or 'angle'."}

    plane = planes.add(plane_input)
    return {"success": True, "name": plane.name}


def construction_axis(design, rootComp, params):
    """Create a construction (reference) axis for patterns, revolves, or other operations.

    Modes:
        two_points - Create axis between two 3D points
    """
    mode = params.get('mode', 'two_points')

    axes = rootComp.constructionAxes
    axis_input = axes.createInput()

    if mode == 'two_points':
        p1 = params.get('point1', {'x': 0, 'y': 0, 'z': 0})
        p2 = params.get('point2', {'x': 0, 'y': 0, 'z': 1.0})

        point1 = adsk.core.Point3D.create(
            float(p1.get('x', 0)),
            float(p1.get('y', 0)),
            float(p1.get('z', 0))
        )
        point2 = adsk.core.Point3D.create(
            float(p2.get('x', 0)),
            float(p2.get('y', 0)),
            float(p2.get('z', 1.0))
        )

        axis_input.setByTwoPoints(point1, point2)

    else:
        return {"success": False, "error": f"Unknown mode '{mode}'. Use 'two_points'."}

    axis = axes.add(axis_input)
    return {"success": True, "name": axis.name}


def construction_point(design, rootComp, params):
    """Create a construction (reference) point for positioning holes, patterns, or other features."""
    x = float(params.get('x', 0))
    y = float(params.get('y', 0))
    z = float(params.get('z', 0))

    point3d = adsk.core.Point3D.create(x, y, z)

    points = rootComp.constructionPoints
    point_input = points.createInput()
    point_input.setByPoint(point3d)

    point = points.add(point_input)
    return {"success": True, "name": point.name}
