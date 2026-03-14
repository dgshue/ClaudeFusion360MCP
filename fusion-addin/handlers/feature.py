import adsk.core
import adsk.fusion
import math

import os
import sys
_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.bodies import get_body
from helpers.selection import resolve_edges


def extrude(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles in sketch. Draw geometry before extruding."}

    profile_index = params.get('profile_index', 0)
    if profile_index < 0 or profile_index >= sketch.profiles.count:
        return {
            "success": False,
            "error": f"Profile index {profile_index} out of range. Sketch has {sketch.profiles.count} profiles (0-{sketch.profiles.count - 1})."
        }
    profile = sketch.profiles.item(profile_index)

    extrudes = rootComp.features.extrudeFeatures
    ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(params['distance']))

    taper_angle = params.get('taper_angle', 0)
    if taper_angle != 0:
        ext_input.taperAngle = adsk.core.ValueInput.createByReal(math.radians(taper_angle))

    ext_feature = extrudes.add(ext_input)
    return {"success": True, "feature_name": ext_feature.name}


def revolve(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches"}
    sketch = rootComp.sketches.item(rootComp.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles in sketch. Draw geometry before revolving."}

    profile_index = params.get('profile_index', sketch.profiles.count - 1)
    profile = sketch.profiles.item(profile_index)

    axis_name = params.get('axis', 'Y').upper()
    axis_map = {
        'X': rootComp.xConstructionAxis,
        'Y': rootComp.yConstructionAxis,
        'Z': rootComp.zConstructionAxis
    }
    axis = axis_map.get(axis_name, rootComp.yConstructionAxis)

    revolves = rootComp.features.revolveFeatures
    rev_input = revolves.createInput(profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    angle = math.radians(params.get('angle', 360))
    rev_input.setAngleExtent(False, adsk.core.ValueInput.createByReal(angle))
    rev_feature = revolves.add(rev_input)
    return {"success": True, "feature_name": rev_feature.name}


def fillet(design, rootComp, params):
    try:
        body = get_body(rootComp, params.get('body_index'))
    except ValueError as e:
        return {"success": False, "error": str(e)}

    edge_selectors = params.get('edges', None)
    edges = adsk.core.ObjectCollection.create()

    if edge_selectors is not None:
        try:
            resolved = resolve_edges(body, edge_selectors)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        for edge in resolved:
            edges.add(edge)
    else:
        for edge in body.edges:
            edges.add(edge)

    fillets = rootComp.features.filletFeatures
    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(edges, adsk.core.ValueInput.createByReal(params['radius']), True)
    fillet_feat = fillets.add(fillet_input)
    return {"success": True, "feature_name": fillet_feat.name}


def chamfer(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    body = rootComp.bRepBodies.item(body_index)

    edge_indices = params.get('edges', None)
    edges = adsk.core.ObjectCollection.create()

    if edge_indices is not None:
        for idx in edge_indices:
            if isinstance(idx, int):
                if idx < 0 or idx >= body.edges.count:
                    return {
                        "success": False,
                        "error": f"Edge index {idx} out of range. Body has {body.edges.count} edges (0-{body.edges.count - 1})."
                    }
                edges.add(body.edges.item(idx))
    else:
        for edge in body.edges:
            edges.add(edge)

    chamfers = rootComp.features.chamferFeatures
    chamfer_input = chamfers.createInput(edges, True)
    distance = params.get('distance', params.get('size', 0.1))
    chamfer_input.setToEqualDistance(adsk.core.ValueInput.createByReal(distance))
    chamfer_feat = chamfers.add(chamfer_input)
    return {"success": True, "feature_name": chamfer_feat.name}


def shell(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    body = rootComp.bRepBodies.item(body_index)
    thickness = params['thickness']

    faces_to_remove = adsk.core.ObjectCollection.create()
    face_indices = params.get('faces_to_remove', [])
    for idx in face_indices:
        if isinstance(idx, int):
            if idx < 0 or idx >= body.faces.count:
                return {
                    "success": False,
                    "error": f"Face index {idx} out of range. Body has {body.faces.count} faces (0-{body.faces.count - 1})."
                }
            faces_to_remove.add(body.faces.item(idx))

    shell_feats = rootComp.features.shellFeatures
    shell_input = shell_feats.createInput(faces_to_remove, False)
    shell_input.insideThickness = adsk.core.ValueInput.createByReal(thickness)
    shell_feat = shell_feats.add(shell_input)
    return {"success": True, "feature_name": shell_feat.name}


def draft(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    body = rootComp.bRepBodies.item(body_index)

    angle = params.get('angle', 5)
    face_indices = params.get('faces', [])

    faces = adsk.core.ObjectCollection.create()
    for idx in face_indices:
        if isinstance(idx, int):
            if idx < 0 or idx >= body.faces.count:
                return {
                    "success": False,
                    "error": f"Face index {idx} out of range. Body has {body.faces.count} faces (0-{body.faces.count - 1})."
                }
            faces.add(body.faces.item(idx))

    plane = params.get('pull_direction', 'Z')
    plane_map = {
        'X': rootComp.xConstructionPlane,
        'Y': rootComp.yConstructionPlane,
        'Z': rootComp.zConstructionPlane
    }
    pull_plane = plane_map.get(plane.upper(), rootComp.zConstructionPlane)

    draft_feats = rootComp.features.draftFeatures
    draft_input = draft_feats.createInput(
        faces,
        pull_plane,
        adsk.core.ValueInput.createByString(f"{angle} deg"),
        False
    )
    draft_feat = draft_feats.add(draft_input)
    return {"success": True, "feature_name": draft_feat.name}


def pattern_rectangular(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    body = rootComp.bRepBodies.item(body_index)

    entities = adsk.core.ObjectCollection.create()
    entities.add(body)

    x_axis = rootComp.xConstructionAxis
    y_axis = rootComp.yConstructionAxis

    x_count = adsk.core.ValueInput.createByString(str(params.get('x_count', 2)))
    x_spacing = adsk.core.ValueInput.createByReal(params.get('x_spacing', 1))

    rect_patterns = rootComp.features.rectangularPatternFeatures
    pattern_input = rect_patterns.createInput(
        entities, x_axis, x_count, x_spacing,
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType
    )

    y_count = params.get('y_count', 1)
    if y_count > 1:
        qty_y = adsk.core.ValueInput.createByString(str(y_count))
        dist_y = adsk.core.ValueInput.createByReal(params.get('y_spacing', 1))
        pattern_input.setDirectionTwo(y_axis, qty_y, dist_y)

    pattern = rect_patterns.add(pattern_input)
    return {"success": True, "feature_name": pattern.name}


def pattern_circular(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    body = rootComp.bRepBodies.item(body_index)

    entities = adsk.core.ObjectCollection.create()
    entities.add(body)

    axis_name = params.get('axis', 'Z').upper()
    axis_map = {
        'X': rootComp.xConstructionAxis,
        'Y': rootComp.yConstructionAxis,
        'Z': rootComp.zConstructionAxis
    }
    axis = axis_map.get(axis_name, rootComp.zConstructionAxis)

    count = params.get('count', 4)
    angle = params.get('angle', 360)

    circ_patterns = rootComp.features.circularPatternFeatures
    pattern_input = circ_patterns.createInput(entities, axis)
    pattern_input.quantity = adsk.core.ValueInput.createByString(str(count))
    pattern_input.totalAngle = adsk.core.ValueInput.createByString(f"{angle} deg")
    pattern_input.isSymmetric = params.get('symmetric', False)

    pattern = circ_patterns.add(pattern_input)
    return {"success": True, "feature_name": pattern.name}


def mirror(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies. Create geometry first."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    body = rootComp.bRepBodies.item(body_index)

    entities = adsk.core.ObjectCollection.create()
    entities.add(body)

    plane_name = params.get('plane', 'YZ').upper()
    plane_map = {
        'XY': rootComp.xYConstructionPlane,
        'XZ': rootComp.xZConstructionPlane,
        'YZ': rootComp.yZConstructionPlane
    }
    mirror_plane = plane_map.get(plane_name, rootComp.yZConstructionPlane)

    mirror_feats = rootComp.features.mirrorFeatures
    mirror_input = mirror_feats.createInput(entities, mirror_plane)
    mirror_feat = mirror_feats.add(mirror_input)
    return {"success": True, "feature_name": mirror_feat.name}


def combine(design, rootComp, params):
    target_index = params.get('target_body', 0)
    if target_index >= rootComp.bRepBodies.count:
        return {
            "success": False,
            "error": f"Target body index {target_index} out of range. Design has {rootComp.bRepBodies.count} bodies (0-{rootComp.bRepBodies.count - 1})."
        }
    target_body = rootComp.bRepBodies.item(target_index)

    tool_indices = params.get('tool_bodies', [])
    tools = adsk.core.ObjectCollection.create()
    for idx in tool_indices:
        if idx >= rootComp.bRepBodies.count:
            return {
                "success": False,
                "error": f"Tool body index {idx} out of range. Design has {rootComp.bRepBodies.count} bodies (0-{rootComp.bRepBodies.count - 1})."
            }
        tools.add(rootComp.bRepBodies.item(idx))

    op_map = {
        'cut': adsk.fusion.FeatureOperations.CutFeatureOperation,
        'join': adsk.fusion.FeatureOperations.JoinFeatureOperation,
        'intersect': adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }

    combine_feats = rootComp.features.combineFeatures
    combine_input = combine_feats.createInput(target_body, tools)
    combine_input.operation = op_map.get(params.get('operation', 'join'))
    combine_input.isKeepToolBodies = params.get('keep_tools', False)
    combine_feat = combine_feats.add(combine_input)
    return {"success": True, "feature_name": combine_feat.name}
