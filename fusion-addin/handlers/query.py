import adsk.core
import adsk.fusion


def get_design_info(design, rootComp, params):
    return {
        "success": True,
        "design_name": design.parentDocument.name,
        "body_count": rootComp.bRepBodies.count,
        "sketch_count": rootComp.sketches.count,
        "component_count": rootComp.occurrences.count
    }


def get_body_info(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies in design. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    if body_index < 0 or body_index >= rootComp.bRepBodies.count:
        return {
            "success": False,
            "error": f"Body index {body_index} out of range. Design has {rootComp.bRepBodies.count} bodies (0-{rootComp.bRepBodies.count - 1})."
        }
    body = rootComp.bRepBodies.item(body_index)

    edges_info = []
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        edge_info = {
            "index": i,
            "length": round(edge.length, 4)
        }
        try:
            mp = edge.pointOnEdge
            edge_info["midpoint"] = {
                "x": round(mp.x, 4),
                "y": round(mp.y, 4),
                "z": round(mp.z, 4)
            }
        except Exception:
            pass
        edges_info.append(edge_info)

    faces_info = []
    for i in range(body.faces.count):
        face = body.faces.item(i)
        face_type = "unknown"
        try:
            geom = face.geometry
            if isinstance(geom, adsk.core.Plane):
                face_type = "planar"
            elif isinstance(geom, adsk.core.Cylinder):
                face_type = "cylindrical"
            elif isinstance(geom, adsk.core.Sphere):
                face_type = "spherical"
            elif isinstance(geom, adsk.core.Cone):
                face_type = "conical"
            elif isinstance(geom, adsk.core.Torus):
                face_type = "toroidal"
        except Exception:
            pass

        face_info = {
            "index": i,
            "type": face_type,
            "area": round(face.area, 4)
        }
        try:
            centroid = face.centroid
            face_info["centroid"] = {
                "x": round(centroid.x, 4),
                "y": round(centroid.y, 4),
                "z": round(centroid.z, 4)
            }
        except Exception:
            pass
        faces_info.append(face_info)

    bbox = body.boundingBox
    return {
        "success": True,
        "body_name": body.name,
        "edge_count": body.edges.count,
        "face_count": body.faces.count,
        "bounding_box": {
            "min": {"x": round(bbox.minPoint.x, 4), "y": round(bbox.minPoint.y, 4), "z": round(bbox.minPoint.z, 4)},
            "max": {"x": round(bbox.maxPoint.x, 4), "y": round(bbox.maxPoint.y, 4), "z": round(bbox.maxPoint.z, 4)}
        },
        "edges": edges_info,
        "faces": faces_info
    }


def measure(design, rootComp, params):
    measure_type = params.get('type', 'body')

    if measure_type == 'body':
        if rootComp.bRepBodies.count == 0:
            return {"success": False, "error": "No bodies in design."}

        body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
        body = rootComp.bRepBodies.item(body_index)

        props = body.physicalProperties
        bbox = body.boundingBox
        return {
            "success": True,
            "body_name": body.name,
            "volume": round(props.volume, 6),
            "area": round(props.area, 4),
            "bounding_box": {
                "min": {"x": round(bbox.minPoint.x, 4), "y": round(bbox.minPoint.y, 4), "z": round(bbox.minPoint.z, 4)},
                "max": {"x": round(bbox.maxPoint.x, 4), "y": round(bbox.maxPoint.y, 4), "z": round(bbox.maxPoint.z, 4)}
            },
            "center_of_mass": {
                "x": round(props.centerOfMass.x, 4),
                "y": round(props.centerOfMass.y, 4),
                "z": round(props.centerOfMass.z, 4)
            }
        }

    elif measure_type == 'edge':
        if rootComp.bRepBodies.count == 0:
            return {"success": False, "error": "No bodies in design."}
        body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
        body = rootComp.bRepBodies.item(body_index)
        edge_index = params.get('edge_index', 0)
        if edge_index >= body.edges.count:
            return {"success": False, "error": f"Edge index {edge_index} out of range. Body has {body.edges.count} edges."}
        edge = body.edges.item(edge_index)
        return {
            "success": True,
            "edge_index": edge_index,
            "length": round(edge.length, 4)
        }

    elif measure_type == 'face':
        if rootComp.bRepBodies.count == 0:
            return {"success": False, "error": "No bodies in design."}
        body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
        body = rootComp.bRepBodies.item(body_index)
        face_index = params.get('face_index', 0)
        if face_index >= body.faces.count:
            return {"success": False, "error": f"Face index {face_index} out of range. Body has {body.faces.count} faces."}
        face = body.faces.item(face_index)
        return {
            "success": True,
            "face_index": face_index,
            "area": round(face.area, 4)
        }

    return {"success": False, "error": f"Unknown measure type '{measure_type}'. Use 'body', 'edge', or 'face'."}
