import adsk.core
import adsk.fusion


def create_component(design, rootComp, params):
    name = params.get('name', '')
    transform = adsk.core.Matrix3D.create()
    occ = rootComp.occurrences.addNewComponent(transform)
    if name:
        occ.component.name = name
    return {
        "success": True,
        "component_name": occ.component.name,
        "occurrence_index": rootComp.occurrences.count - 1
    }


def list_components(design, rootComp, params):
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
            comp_info["position"] = {
                "x": round(t.translation.x, 4),
                "y": round(t.translation.y, 4),
                "z": round(t.translation.z, 4)
            }
        except Exception:
            pass
        components.append(comp_info)

    return {
        "success": True,
        "component_count": rootComp.occurrences.count,
        "components": components
    }


def delete_component(design, rootComp, params):
    index = params.get('index', None)
    name = params.get('name', None)

    if index is not None:
        if index < 0 or index >= rootComp.occurrences.count:
            return {
                "success": False,
                "error": f"Component index {index} out of range. Design has {rootComp.occurrences.count} components (0-{rootComp.occurrences.count - 1})."
            }
        occ = rootComp.occurrences.item(index)
        comp_name = occ.component.name
        occ.deleteMe()
        return {"success": True, "deleted": comp_name}
    elif name is not None:
        for i in range(rootComp.occurrences.count):
            occ = rootComp.occurrences.item(i)
            if occ.component.name == name:
                occ.deleteMe()
                return {"success": True, "deleted": name}
        return {"success": False, "error": f"No component named '{name}' found."}
    else:
        return {"success": False, "error": "Provide 'index' or 'name' to identify the component to delete."}


def move_component(design, rootComp, params):
    index = params.get('index', 0)
    if index < 0 or index >= rootComp.occurrences.count:
        return {
            "success": False,
            "error": f"Component index {index} out of range. Design has {rootComp.occurrences.count} components."
        }
    occ = rootComp.occurrences.item(index)

    x = params.get('x', 0)
    y = params.get('y', 0)
    z = params.get('z', 0)

    transform = occ.transform
    translation = adsk.core.Vector3D.create(x, y, z)
    transform.translation = translation
    occ.transform = transform
    design.snapshots.add()

    return {"success": True, "component": occ.component.name, "position": {"x": x, "y": y, "z": z}}


def rotate_component(design, rootComp, params):
    index = params.get('index', 0)
    if index < 0 or index >= rootComp.occurrences.count:
        return {
            "success": False,
            "error": f"Component index {index} out of range. Design has {rootComp.occurrences.count} components."
        }
    occ = rootComp.occurrences.item(index)

    import math
    angle = math.radians(params.get('angle', 0))
    axis_name = params.get('axis', 'Z').upper()

    axis_map = {
        'X': adsk.core.Vector3D.create(1, 0, 0),
        'Y': adsk.core.Vector3D.create(0, 1, 0),
        'Z': adsk.core.Vector3D.create(0, 0, 1)
    }
    axis = axis_map.get(axis_name, adsk.core.Vector3D.create(0, 0, 1))
    origin = adsk.core.Point3D.create(0, 0, 0)

    transform = occ.transform
    transform.setToRotation(angle, axis, origin)
    occ.transform = transform
    design.snapshots.add()

    return {"success": True, "component": occ.component.name, "angle": params.get('angle', 0), "axis": axis_name}


def check_interference(design, rootComp, params):
    if rootComp.bRepBodies.count < 2:
        return {"success": False, "error": "Need at least 2 bodies to check interference."}

    body_indices = params.get('bodies', None)
    bodies = []
    if body_indices:
        for idx in body_indices:
            if idx >= rootComp.bRepBodies.count:
                return {"success": False, "error": f"Body index {idx} out of range."}
            bodies.append(rootComp.bRepBodies.item(idx))
    else:
        for i in range(rootComp.bRepBodies.count):
            bodies.append(rootComp.bRepBodies.item(i))

    interferences = []
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            bb1 = bodies[i].boundingBox
            bb2 = bodies[j].boundingBox
            overlaps = (
                bb1.minPoint.x <= bb2.maxPoint.x and bb1.maxPoint.x >= bb2.minPoint.x and
                bb1.minPoint.y <= bb2.maxPoint.y and bb1.maxPoint.y >= bb2.minPoint.y and
                bb1.minPoint.z <= bb2.maxPoint.z and bb1.maxPoint.z >= bb2.minPoint.z
            )
            if overlaps:
                interferences.append({
                    "body1": bodies[i].name,
                    "body2": bodies[j].name,
                    "type": "bounding_box_overlap"
                })

    return {
        "success": True,
        "interference_count": len(interferences),
        "interferences": interferences
    }
