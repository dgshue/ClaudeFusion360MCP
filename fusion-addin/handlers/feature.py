import adsk.core
import adsk.fusion
import math

import os
import sys
_addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from helpers.bodies import get_body
from helpers.selection import resolve_edges, resolve_faces
from helpers.param_annotation import annotate_value, annotate_feature_dimensions


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
    result = {"success": True, "feature_name": ext_feature.name}
    try:
        dims = annotate_feature_dimensions(design, ext_feature)
        if dims:
            result["dimensions"] = dims
    except Exception:
        pass
    return result


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
    result = {"success": True, "feature_name": rev_feature.name}
    try:
        dims = annotate_feature_dimensions(design, rev_feature)
        if dims:
            result["dimensions"] = dims
    except Exception:
        pass
    return result


def fillet(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))

    edge_selectors = params.get('edges', None)
    edges = adsk.core.ObjectCollection.create()

    if edge_selectors is not None:
        resolved = resolve_edges(body, edge_selectors)
        for edge in resolved:
            edges.add(edge)
    else:
        for edge in body.edges:
            edges.add(edge)

    fillets = rootComp.features.filletFeatures
    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(edges, adsk.core.ValueInput.createByReal(params['radius']), True)
    fillet_feat = fillets.add(fillet_input)
    result = {"success": True, "feature_name": fillet_feat.name}
    try:
        result["radius"] = annotate_value(design, params['radius'])
    except Exception:
        pass
    return result


def chamfer(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))

    edge_selectors = params.get('edges', None)
    edges = adsk.core.ObjectCollection.create()

    if edge_selectors is not None:
        resolved = resolve_edges(body, edge_selectors)
        for edge in resolved:
            edges.add(edge)
    else:
        for edge in body.edges:
            edges.add(edge)

    distance = params.get('distance', params.get('size', 0.1))

    chamfers = rootComp.features.chamferFeatures
    try:
        # Newer Fusion API: createInput2
        chamfer_input = chamfers.createInput2()
        chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
            edges,
            adsk.core.ValueInput.createByReal(distance),
            True
        )
    except AttributeError:
        # Older Fusion API fallback: createInput
        chamfer_input = chamfers.createInput(edges, True)
        chamfer_input.setToEqualDistance(adsk.core.ValueInput.createByReal(distance))

    chamfer_feat = chamfers.add(chamfer_input)
    result = {"success": True, "feature_name": chamfer_feat.name}
    try:
        result["distance"] = annotate_value(design, distance)
    except Exception:
        pass
    return result


def shell(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))
    thickness = params['thickness']

    face_selectors = params.get('faces_to_remove', [])
    faces_collection = adsk.core.ObjectCollection.create()

    if face_selectors:
        resolved = resolve_faces(body, face_selectors)
        for face in resolved:
            faces_collection.add(face)

    shell_feats = rootComp.features.shellFeatures
    shell_input = shell_feats.createInput(faces_collection, False)
    shell_input.insideThickness = adsk.core.ValueInput.createByReal(thickness)
    shell_feat = shell_feats.add(shell_input)
    result = {"success": True, "feature_name": shell_feat.name}
    try:
        result["thickness"] = annotate_value(design, thickness)
    except Exception:
        pass
    return result


def draft(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))

    angle = params.get('angle', 5)
    face_selectors = params.get('faces', [])

    faces = adsk.core.ObjectCollection.create()
    if face_selectors:
        resolved = resolve_faces(body, face_selectors)
        for face in resolved:
            faces.add(face)

    # Determine pull direction plane
    # Support both explicit pull_x/y/z vector and simple pull_direction string
    pull_x = params.get('pull_x', None)
    pull_y = params.get('pull_y', None)
    pull_z = params.get('pull_z', None)

    if pull_x is not None or pull_y is not None or pull_z is not None:
        # Use explicit vector components to pick the closest construction plane
        px = pull_x or 0.0
        py = pull_y or 0.0
        pz = pull_z or 0.0
        # Pick the plane whose normal is most aligned with the pull vector
        abs_vals = [abs(px), abs(py), abs(pz)]
        max_idx = abs_vals.index(max(abs_vals))
        if max_idx == 0:
            pull_plane = rootComp.xConstructionPlane
        elif max_idx == 1:
            pull_plane = rootComp.yConstructionPlane
        else:
            pull_plane = rootComp.zConstructionPlane
    else:
        # Fall back to string-based pull direction
        plane_str = params.get('pull_direction', 'Z').upper()
        plane_map = {
            'X': rootComp.xConstructionPlane,
            'Y': rootComp.yConstructionPlane,
            'Z': rootComp.zConstructionPlane
        }
        pull_plane = plane_map.get(plane_str, rootComp.zConstructionPlane)

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
    body = get_body(rootComp, params.get('body_index'))

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
    body = get_body(rootComp, params.get('body_index'))

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
    body = get_body(rootComp, params.get('body_index'))

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
    target_body = get_body(rootComp, params.get('target_body', 0))

    tool_indices = params.get('tool_bodies', [])
    tools = adsk.core.ObjectCollection.create()
    for idx in tool_indices:
        tool_body = get_body(rootComp, idx)
        tools.add(tool_body)

    op_map = {
        'cut': adsk.fusion.FeatureOperations.CutFeatureOperation,
        'join': adsk.fusion.FeatureOperations.JoinFeatureOperation,
        'intersect': adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    operation = params.get('operation', 'join')
    if operation not in op_map:
        raise ValueError(
            f"Unknown combine operation '{operation}'. Use 'cut', 'join', or 'intersect'."
        )

    combine_feats = rootComp.features.combineFeatures
    combine_input = combine_feats.createInput(target_body, tools)
    combine_input.operation = op_map[operation]
    combine_input.isKeepToolBodies = params.get('keep_tools', False)
    combine_feat = combine_feats.add(combine_input)
    return {"success": True, "feature_name": combine_feat.name}


def sweep(design, rootComp, params):
    if rootComp.sketches.count < 2:
        return {"success": False, "error": "Sweep requires at least 2 sketches: one for the profile and one for the path"}

    profile_sketch_index = params.get('profile_sketch_index', rootComp.sketches.count - 2)
    path_sketch_index = params.get('path_sketch_index', rootComp.sketches.count - 1)

    if profile_sketch_index == path_sketch_index:
        return {"success": False, "error": "Profile and path must be in different sketches"}

    profile_sketch = rootComp.sketches.item(profile_sketch_index)
    profile_index = params.get('profile_index', 0)
    if profile_sketch.profiles.count == 0:
        return {"success": False, "error": "No profiles in profile sketch. Draw closed geometry before sweeping."}
    if profile_index < 0 or profile_index >= profile_sketch.profiles.count:
        return {"success": False, "error": f"Profile index {profile_index} out of range. Sketch has {profile_sketch.profiles.count} profiles (0-{profile_sketch.profiles.count - 1})."}
    profile = profile_sketch.profiles.item(profile_index)

    path_sketch = rootComp.sketches.item(path_sketch_index)
    path_curve_index = params.get('path_curve_index', 0)
    if path_curve_index < 0 or path_curve_index >= path_sketch.sketchCurves.count:
        return {"success": False, "error": f"Path curve index {path_curve_index} out of range. Path sketch has {path_sketch.sketchCurves.count} curves (0-{path_sketch.sketchCurves.count - 1})."}
    path_curve = path_sketch.sketchCurves.item(path_curve_index)
    path = rootComp.features.createPath(path_curve)

    op_map = {
        'new': adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        'join': adsk.fusion.FeatureOperations.JoinFeatureOperation,
        'cut': adsk.fusion.FeatureOperations.CutFeatureOperation,
        'intersect': adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    operation = params.get('operation', 'new')
    if operation not in op_map:
        return {"success": False, "error": f"Unknown operation '{operation}'. Use 'new', 'join', 'cut', or 'intersect'."}

    sweeps = rootComp.features.sweepFeatures
    sweep_input = sweeps.createInput(profile, path, op_map[operation])

    taper_angle = params.get('taper_angle', 0)
    if taper_angle != 0:
        sweep_input.taperAngle = adsk.core.ValueInput.createByString(f"{taper_angle} deg")

    twist_angle = params.get('twist_angle', 0)
    if twist_angle != 0:
        sweep_input.twistAngle = adsk.core.ValueInput.createByString(f"{twist_angle} deg")

    feat = sweeps.add(sweep_input)
    return {"success": True, "feature_name": feat.name}


def loft(design, rootComp, params):
    sketch_indices = params.get('sketch_indices', [])
    if len(sketch_indices) < 2:
        return {"success": False, "error": "Loft requires at least 2 sketch indices"}

    if len(sketch_indices) != len(set(sketch_indices)):
        return {"success": False, "error": "Loft sections must be from different sketches on different planes"}

    profile_indices = params.get('profile_indices', [0] * len(sketch_indices))
    if len(profile_indices) < len(sketch_indices):
        profile_indices.extend([0] * (len(sketch_indices) - len(profile_indices)))

    op_map = {
        'new': adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        'join': adsk.fusion.FeatureOperations.JoinFeatureOperation,
        'cut': adsk.fusion.FeatureOperations.CutFeatureOperation,
        'intersect': adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    operation = params.get('operation', 'new')
    if operation not in op_map:
        return {"success": False, "error": f"Unknown operation '{operation}'. Use 'new', 'join', 'cut', or 'intersect'."}

    loft_feats = rootComp.features.loftFeatures
    loft_input = loft_feats.createInput(op_map[operation])

    for i, sketch_idx in enumerate(sketch_indices):
        if sketch_idx < 0 or sketch_idx >= rootComp.sketches.count:
            return {"success": False, "error": f"Sketch index {sketch_idx} out of range. Design has {rootComp.sketches.count} sketches (0-{rootComp.sketches.count - 1})."}
        sketch = rootComp.sketches.item(sketch_idx)
        prof_idx = profile_indices[i]
        if sketch.profiles.count == 0:
            return {"success": False, "error": f"No profiles in sketch {sketch_idx}. Draw closed geometry before lofting."}
        if prof_idx < 0 or prof_idx >= sketch.profiles.count:
            return {"success": False, "error": f"Profile index {prof_idx} out of range for sketch {sketch_idx}. Sketch has {sketch.profiles.count} profiles (0-{sketch.profiles.count - 1})."}
        profile = sketch.profiles.item(prof_idx)
        loft_input.loftSections.add(profile)

    loft_input.isSolid = params.get('is_solid', True)
    loft_input.isClosed = params.get('is_closed', False)

    feat = loft_feats.add(loft_input)
    return {"success": True, "feature_name": feat.name}
