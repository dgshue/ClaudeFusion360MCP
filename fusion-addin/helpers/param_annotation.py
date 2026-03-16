import adsk.core
import adsk.fusion


def annotate_value(design, value, unit="cm"):
    """Annotate a numeric value with parameter linkage if driven by a user parameter.

    Iterates user parameters to find one whose value matches (within tolerance).
    Returns a dict with value/unit and optional driven_by/expression fields.
    """
    result = {"value": value, "unit": unit}
    try:
        userParams = design.userParameters
        for i in range(userParams.count):
            param = userParams.item(i)
            if abs(param.value - value) < 1e-6:
                result["driven_by"] = param.name
                result["expression"] = param.expression
                break
    except Exception:
        pass
    return result


def annotate_feature_dimensions(design, feature):
    """Inspect a feature's extent to extract and annotate dimension values.

    Supports ExtrudeFeature (distance) and RevolveFeature (angle).
    Returns a dict of dimension annotations, or empty dict on failure.
    """
    dims = {}
    try:
        # ExtrudeFeature: check extentOne for DistanceExtentDefinition
        if hasattr(feature, 'extentOne'):
            extent = feature.extentOne
            if hasattr(extent, 'distance'):
                dist_value = extent.distance.value
                dims["distance"] = annotate_value(design, dist_value, "cm")

        # RevolveFeature: check extentDefinition for angle
        if hasattr(feature, 'extentDefinition'):
            extent_def = feature.extentDefinition
            if hasattr(extent_def, 'angle'):
                angle_value = extent_def.angle.value
                dims["angle"] = annotate_value(design, angle_value, "rad")
    except Exception:
        pass
    return dims
