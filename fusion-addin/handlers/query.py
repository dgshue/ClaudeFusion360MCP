import adsk.core
import adsk.fusion

import os
import sys
_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.bodies import get_body
from helpers.selection import label_edge, label_face
from helpers.param_annotation import annotate_value


def get_design_info(design, rootComp, params):
    active_sketch = None
    for i in range(rootComp.sketches.count):
        sk = rootComp.sketches.item(i)
        try:
            if sk.isActive:
                active_sketch = sk.name
                break
        except Exception:
            pass

    return {
        "success": True,
        "design_name": design.parentDocument.name,
        "body_count": rootComp.bRepBodies.count,
        "sketch_count": rootComp.sketches.count,
        "component_count": rootComp.occurrences.count,
        "active_sketch": active_sketch
    }


def get_body_info(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))

    edges_info = []
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        label = label_edge(edge, i, body)

        # Determine edge geometry type
        edge_type = "linear"
        try:
            geom = edge.geometry
            if isinstance(geom, adsk.core.Circle3D) or isinstance(geom, adsk.core.Arc3D):
                edge_type = "circular"
            elif isinstance(geom, adsk.core.Line3D):
                edge_type = "linear"
            elif isinstance(geom, adsk.core.Ellipse3D) or isinstance(geom, adsk.core.EllipticalArc3D):
                edge_type = "elliptical"
            elif isinstance(geom, adsk.core.NurbsCurve3D):
                edge_type = "nurbs"
        except Exception:
            pass

        edges_info.append({
            "index": i,
            "label": label,
            "length_cm": round(edge.length, 4),
            "type": edge_type
        })

    faces_info = []
    for i in range(body.faces.count):
        face = body.faces.item(i)
        label = label_face(face, i, body)

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

        faces_info.append({
            "index": i,
            "label": label,
            "area_cm2": round(face.area, 4),
            "type": face_type
        })

    bbox = body.boundingBox
    size_x = round(bbox.maxPoint.x - bbox.minPoint.x, 4)
    size_y = round(bbox.maxPoint.y - bbox.minPoint.y, 4)
    size_z = round(bbox.maxPoint.z - bbox.minPoint.z, 4)

    bounding_box = {
        "min": [round(bbox.minPoint.x, 4), round(bbox.minPoint.y, 4), round(bbox.minPoint.z, 4)],
        "max": [round(bbox.maxPoint.x, 4), round(bbox.maxPoint.y, 4), round(bbox.maxPoint.z, 4)]
    }

    # Annotate bounding box dimensions with parameter linkage
    try:
        bounding_box["size_x"] = annotate_value(design, size_x)
        bounding_box["size_y"] = annotate_value(design, size_y)
        bounding_box["size_z"] = annotate_value(design, size_z)
    except Exception:
        bounding_box["size_x"] = {"value": size_x, "unit": "cm"}
        bounding_box["size_y"] = {"value": size_y, "unit": "cm"}
        bounding_box["size_z"] = {"value": size_z, "unit": "cm"}

    return {
        "success": True,
        "body_name": body.name,
        "edge_count": body.edges.count,
        "face_count": body.faces.count,
        "edges": edges_info,
        "faces": faces_info,
        "bounding_box": bounding_box
    }


def measure(design, rootComp, params):
    measure_type = params.get('type', 'body')
    body = get_body(rootComp, params.get('body_index'))

    if measure_type == 'body':
        props = body.physicalProperties
        bbox = body.boundingBox
        size_x = round(bbox.maxPoint.x - bbox.minPoint.x, 4)
        size_y = round(bbox.maxPoint.y - bbox.minPoint.y, 4)
        size_z = round(bbox.maxPoint.z - bbox.minPoint.z, 4)

        result = {
            "success": True,
            "body_name": body.name,
            "volume_cm3": round(props.volume, 6),
            "surface_area_cm2": round(props.area, 4),
            "bounding_box": {
                "min": [round(bbox.minPoint.x, 4), round(bbox.minPoint.y, 4), round(bbox.minPoint.z, 4)],
                "max": [round(bbox.maxPoint.x, 4), round(bbox.maxPoint.y, 4), round(bbox.maxPoint.z, 4)],
                "size": [size_x, size_y, size_z]
            },
            "center_of_mass": {
                "x": round(props.centerOfMass.x, 4),
                "y": round(props.centerOfMass.y, 4),
                "z": round(props.centerOfMass.z, 4)
            }
        }
        # Annotate size dimensions with parameter linkage
        try:
            result["bounding_box"]["size_annotated"] = {
                "x": annotate_value(design, size_x),
                "y": annotate_value(design, size_y),
                "z": annotate_value(design, size_z),
            }
        except Exception:
            pass
        return result

    elif measure_type == 'edge':
        edge_index = params.get('edge_index', 0)
        if edge_index < 0 or edge_index >= body.edges.count:
            raise ValueError(
                f"Edge index {edge_index} out of range. Body has {body.edges.count} edges (0-{body.edges.count - 1}). "
                f"Use get_body_info() to see available edges."
            )
        edge = body.edges.item(edge_index)
        length = round(edge.length, 4)
        result = {
            "success": True,
            "edge_index": edge_index,
            "length_cm": length
        }
        try:
            result["length"] = annotate_value(design, length)
        except Exception:
            pass
        return result

    elif measure_type == 'face':
        face_index = params.get('face_index', 0)
        if face_index < 0 or face_index >= body.faces.count:
            raise ValueError(
                f"Face index {face_index} out of range. Body has {body.faces.count} faces (0-{body.faces.count - 1}). "
                f"Use get_body_info() to see available faces."
            )
        face = body.faces.item(face_index)
        area = round(face.area, 4)
        result = {
            "success": True,
            "face_index": face_index,
            "area_cm2": area
        }
        try:
            result["area"] = annotate_value(design, area, "cm2")
        except Exception:
            pass
        return result

    else:
        raise ValueError(f"Unknown measure type: {measure_type}. Use 'body', 'edge', or 'face'.")
