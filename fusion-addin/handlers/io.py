import adsk.core
import adsk.fusion

from pathlib import Path


def export_stl(design, rootComp, params):
    """Export the design to an STL file with medium mesh refinement.

    Automatically appends .stl extension if missing.
    """
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    # Ensure filepath has .stl extension
    if not filepath.lower().endswith('.stl'):
        filepath += '.stl'

    export_mgr = design.exportManager
    stl_options = export_mgr.createSTLExportOptions(rootComp, filepath)
    stl_options.sendToPrintUtility = False
    stl_options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium

    export_mgr.execute(stl_options)
    return {"success": True, "filepath": filepath}


def export_step(design, rootComp, params):
    """Export the design to a STEP file.

    Automatically appends .step extension if missing.
    Note: STEP export options take (filepath, component) -- different arg order than STL.
    """
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    # Ensure filepath has .step or .stp extension
    if not filepath.lower().endswith('.step') and not filepath.lower().endswith('.stp'):
        filepath += '.step'

    export_mgr = design.exportManager
    step_options = export_mgr.createSTEPExportOptions(filepath, rootComp)
    export_mgr.execute(step_options)
    return {"success": True, "filepath": filepath}


def export_3mf(design, rootComp, params):
    """Export the design to a 3MF file, with graceful fallback.

    Tries dedicated 3MF export first. If not available, attempts STL export
    with 3MF path. If that also fails, raises a clear error message.
    """
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    # Ensure filepath has .3mf extension
    if not filepath.lower().endswith('.3mf'):
        filepath += '.3mf'

    export_mgr = design.exportManager

    # Try dedicated 3MF method first
    try:
        options = export_mgr.createC3MFExportOptions(rootComp, filepath)
        export_mgr.execute(options)
        return {"success": True, "filepath": filepath, "format": "3mf"}
    except AttributeError:
        pass

    # Fallback: try STL options with 3MF path (some versions support this)
    try:
        stl_options = export_mgr.createSTLExportOptions(rootComp, filepath)
        stl_options.sendToPrintUtility = False
        export_mgr.execute(stl_options)
        return {"success": True, "filepath": filepath, "format": "3mf_via_stl"}
    except:
        raise RuntimeError(
            "3MF export is not supported in this Fusion 360 version. "
            "Use export_stl() instead and convert to 3MF with an external tool."
        )


def import_mesh(design, rootComp, params):
    """Import a mesh file (STL/OBJ/3MF) into the design.

    Handles both parametric and direct design modes. In parametric mode,
    creates a BaseFeature context as required by the Fusion API.

    This is the one handler that accepts a unit parameter (all others use cm).
    """
    filepath = params.get('filepath', '')
    if not filepath:
        return {"success": False, "error": "Missing 'filepath' parameter."}

    # Verify file exists
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Mesh file not found: {filepath}")

    unit_map = {
        'mm': adsk.fusion.MeshUnits.MillimeterMeshUnit,
        'cm': adsk.fusion.MeshUnits.CentimeterMeshUnit,
        'in': adsk.fusion.MeshUnits.InchMeshUnit,
        'ft': adsk.fusion.MeshUnits.FootMeshUnit,
        'm': adsk.fusion.MeshUnits.MeterMeshUnit,
    }
    units = unit_map.get(params.get('unit', 'mm'), adsk.fusion.MeshUnits.MillimeterMeshUnit)

    # Parametric designs require BaseFeature context (Pitfall 4 from research)
    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        base_feats = rootComp.features.baseFeatures
        base_feat = base_feats.add()
        base_feat.startEdit()
        meshes = rootComp.meshBodies.add(filepath, units, base_feat)
        base_feat.finishEdit()
    else:
        meshes = rootComp.meshBodies.add(filepath, units)

    return {
        "success": True,
        "mesh_count": meshes.count if hasattr(meshes, 'count') else 1,
    }
