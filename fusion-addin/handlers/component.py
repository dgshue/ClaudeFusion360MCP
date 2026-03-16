import math

import adsk.core
import adsk.fusion

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from helpers.bodies import get_body, get_occurrence


def create_component(design, rootComp, params):
    """Convert a body into a new component, or create an empty component.

    If body_index is provided, moves that body into the new component.
    Otherwise creates an empty component.
    """
    body_index = params.get('body_index', None)
    name = params.get('name', '')

    transform = adsk.core.Matrix3D.create()
    occ = rootComp.occurrences.addNewComponent(transform)

    if name:
        occ.component.name = name

    if body_index is not None:
        body = get_body(rootComp, body_index)
        body.moveToComponent(occ)

    return {
        "success": True,
        "component_name": occ.component.name,
        "occurrence_index": rootComp.occurrences.count - 1
    }


def list_components(design, rootComp, params):
    """List all components with names, positions, and bounding boxes."""
    components = []
    for i in range(rootComp.occurrences.count):
        occ = rootComp.occurrences.item(i)
        comp_info = {
            "index": i,
            "name": occ.component.name,
            "is_visible": occ.isLightBulbOn,
            "body_count": occ.component.bRepBodies.count
        }

        try:
            t = occ.transform
            comp_info["position"] = [
                round(t.translation.x, 4),
                round(t.translation.y, 4),
                round(t.translation.z, 4)
            ]
        except Exception:
            comp_info["position"] = [0, 0, 0]

        try:
            bbox = occ.boundingBox
            comp_info["bounding_box"] = {
                "min": [
                    round(bbox.minPoint.x, 4),
                    round(bbox.minPoint.y, 4),
                    round(bbox.minPoint.z, 4)
                ],
                "max": [
                    round(bbox.maxPoint.x, 4),
                    round(bbox.maxPoint.y, 4),
                    round(bbox.maxPoint.z, 4)
                ]
            }
        except Exception:
            pass

        components.append(comp_info)

    return {
        "success": True,
        "component_count": len(components),
        "components": components
    }


def delete_component(design, rootComp, params):
    """Delete a component by name or index."""
    occ = get_occurrence(
        rootComp,
        index=params.get('index', None),
        name=params.get('name', None)
    )
    comp_name = occ.component.name
    occ.deleteMe()
    return {"success": True, "deleted": comp_name}


def move_component(design, rootComp, params):
    """Move a component to an absolute position or by a relative offset.

    Uses standard Fusion 360 coordinates (no XZ correction).
    """
    occ = get_occurrence(
        rootComp,
        index=params.get('index', None),
        name=params.get('name', None)
    )

    x = params.get('x', 0.0)
    y = params.get('y', 0.0)
    z = params.get('z', 0.0)
    absolute = params.get('absolute', True)

    if absolute:
        transform = occ.transform
        transform.translation = adsk.core.Vector3D.create(x, y, z)
        occ.transform = transform
    else:
        transform = occ.transform
        current = transform.translation
        transform.translation = adsk.core.Vector3D.create(
            current.x + x,
            current.y + y,
            current.z + z
        )
        occ.transform = transform

    final_pos = occ.transform.translation
    return {
        "success": True,
        "component": occ.component.name,
        "position": [
            round(final_pos.x, 4),
            round(final_pos.y, 4),
            round(final_pos.z, 4)
        ]
    }


def rotate_component(design, rootComp, params):
    """Rotate a component around a specified axis and origin.

    Uses standard Fusion 360 coordinates (no XZ correction).
    Composes rotation with existing transform to preserve position.
    """
    occ = get_occurrence(
        rootComp,
        index=params.get('index', None),
        name=params.get('name', None)
    )

    angle = math.radians(params.get('angle', 0))
    axis_name = params.get('axis', 'Z').upper()

    axis_map = {
        'X': adsk.core.Vector3D.create(1, 0, 0),
        'Y': adsk.core.Vector3D.create(0, 1, 0),
        'Z': adsk.core.Vector3D.create(0, 0, 1)
    }
    axis = axis_map.get(axis_name, adsk.core.Vector3D.create(0, 0, 1))
    origin = adsk.core.Point3D.create(
        params.get('origin_x', 0.0),
        params.get('origin_y', 0.0),
        params.get('origin_z', 0.0)
    )

    # Create a rotation-only matrix
    rotation_matrix = adsk.core.Matrix3D.create()
    rotation_matrix.setToRotation(angle, axis, origin)

    # Compose with current transform to preserve position
    current_transform = occ.transform
    current_transform.transformBy(rotation_matrix)
    occ.transform = current_transform

    return {
        "success": True,
        "component": occ.component.name,
        "angle": params.get('angle', 0),
        "axis": axis_name
    }


def check_interference(design, rootComp, params):
    """Detect bounding box collisions between all component pairs."""
    if rootComp.occurrences.count < 2:
        return {
            "success": True,
            "interference_count": 0,
            "interferences": [],
            "message": "Need at least 2 components to check interference."
        }

    occurrences = []
    for i in range(rootComp.occurrences.count):
        occurrences.append(rootComp.occurrences.item(i))

    interferences = []
    for i in range(len(occurrences)):
        for j in range(i + 1, len(occurrences)):
            try:
                bb1 = occurrences[i].boundingBox
                bb2 = occurrences[j].boundingBox

                overlaps = (
                    bb1.minPoint.x <= bb2.maxPoint.x and bb1.maxPoint.x >= bb2.minPoint.x and
                    bb1.minPoint.y <= bb2.maxPoint.y and bb1.maxPoint.y >= bb2.minPoint.y and
                    bb1.minPoint.z <= bb2.maxPoint.z and bb1.maxPoint.z >= bb2.minPoint.z
                )

                if overlaps:
                    # Calculate overlap volume
                    overlap_x = max(0, min(bb1.maxPoint.x, bb2.maxPoint.x) - max(bb1.minPoint.x, bb2.minPoint.x))
                    overlap_y = max(0, min(bb1.maxPoint.y, bb2.maxPoint.y) - max(bb1.minPoint.y, bb2.minPoint.y))
                    overlap_z = max(0, min(bb1.maxPoint.z, bb2.maxPoint.z) - max(bb1.minPoint.z, bb2.minPoint.z))
                    overlap_volume = round(overlap_x * overlap_y * overlap_z, 6)

                    interferences.append({
                        "component1": occurrences[i].component.name,
                        "component2": occurrences[j].component.name,
                        "overlap_volume": overlap_volume,
                        "type": "bounding_box_overlap"
                    })
            except Exception:
                pass

    return {
        "success": True,
        "interference_count": len(interferences),
        "interferences": interferences
    }
