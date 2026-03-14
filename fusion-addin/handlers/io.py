import adsk.core
import adsk.fusion


def export_stl(design, rootComp, params):
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    export_mgr = design.exportManager
    stl_options = export_mgr.createSTLExportOptions(rootComp, filepath)
    stl_options.sendToPrintUtility = False

    refinement = params.get('refinement', 'medium').lower()
    refinement_map = {
        'low': adsk.fusion.MeshRefinementSettings.MeshRefinementLow,
        'medium': adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,
        'high': adsk.fusion.MeshRefinementSettings.MeshRefinementHigh,
    }
    stl_options.meshRefinement = refinement_map.get(refinement, adsk.fusion.MeshRefinementSettings.MeshRefinementMedium)

    export_mgr.execute(stl_options)
    return {"success": True, "filepath": filepath}


def export_step(design, rootComp, params):
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    export_mgr = design.exportManager
    step_options = export_mgr.createSTEPExportOptions(filepath, rootComp)
    export_mgr.execute(step_options)
    return {"success": True, "filepath": filepath}


def export_3mf(design, rootComp, params):
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    export_mgr = design.exportManager

    # Try 3MF-specific export if available, fall back to STL
    try:
        options_3mf = export_mgr.createC3MFExportOptions(rootComp, filepath)
        export_mgr.execute(options_3mf)
        return {"success": True, "filepath": filepath, "format": "3mf"}
    except AttributeError:
        # 3MF export not available in this API version, fall back to STL
        stl_path = filepath.rsplit('.', 1)[0] + '.stl' if '.' in filepath else filepath + '.stl'
        stl_options = export_mgr.createSTLExportOptions(rootComp, stl_path)
        stl_options.sendToPrintUtility = False
        export_mgr.execute(stl_options)
        return {
            "success": True,
            "filepath": stl_path,
            "format": "stl",
            "warning": "3MF export not available in this API version. Exported as STL instead."
        }


def import_mesh(design, rootComp, params):
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    unit_map = {
        'mm': adsk.fusion.MeshUnits.MillimeterMeshUnit,
        'cm': adsk.fusion.MeshUnits.CentimeterMeshUnit,
        'in': adsk.fusion.MeshUnits.InchMeshUnit,
        'ft': adsk.fusion.MeshUnits.FootMeshUnit,
        'm': adsk.fusion.MeshUnits.MeterMeshUnit,
    }
    units = unit_map.get(params.get('unit', 'mm'), adsk.fusion.MeshUnits.MillimeterMeshUnit)

    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        base_feats = rootComp.features.baseFeatures
        base_feat = base_feats.add()
        base_feat.startEdit()
        meshes = rootComp.meshBodies.add(filepath, units, base_feat)
        base_feat.finishEdit()
    else:
        meshes = rootComp.meshBodies.add(filepath, units)

    return {"success": True, "mesh_count": meshes.count}
