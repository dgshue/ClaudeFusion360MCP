import adsk.core
import adsk.fusion


def detect_sketch_plane(sketch):
    """Determine which construction plane a sketch was created on.

    Returns 'XY', 'XZ', 'YZ', or 'custom'.

    Primary method: Check FusionMCP attribute (set by create_sketch handler,
    works even for offset construction planes).
    Secondary method: Check the sketch's reference plane against the root
    component's construction planes.
    Fallback: Analyze the sketch transform matrix.
    """
    # Check FusionMCP attribute first (handles offset planes)
    try:
        attr = sketch.attributes.itemByName('FusionMCP', 'base_plane')
        if attr and attr.value in ('XY', 'XZ', 'YZ'):
            return attr.value
    except Exception:
        pass

    try:
        ref_plane = sketch.referencePlane
        rootComp = sketch.parentComponent

        if ref_plane == rootComp.xYConstructionPlane:
            return 'XY'
        if ref_plane == rootComp.xZConstructionPlane:
            return 'XZ'
        if ref_plane == rootComp.yZConstructionPlane:
            return 'YZ'
    except Exception:
        pass

    # Fallback: analyze the sketch transform matrix
    try:
        transform = sketch.transform
        # XY plane: identity-like (no rotation)
        # XZ plane: 90-degree rotation about X axis
        # YZ plane: 90-degree rotation about Y axis

        # Get the normal direction from the transform
        # The Z column of the rotation matrix gives the sketch normal
        z_x = transform.getCell(0, 2)
        z_y = transform.getCell(1, 2)
        z_z = transform.getCell(2, 2)

        # XY plane normal is (0, 0, 1)
        if abs(z_z) > 0.9 and abs(z_x) < 0.1 and abs(z_y) < 0.1:
            return 'XY'
        # XZ plane normal is (0, 1, 0) or (0, -1, 0)
        if abs(z_y) > 0.9 and abs(z_x) < 0.1 and abs(z_z) < 0.1:
            return 'XZ'
        # YZ plane normal is (1, 0, 0) or (-1, 0, 0)
        if abs(z_x) > 0.9 and abs(z_y) < 0.1 and abs(z_z) < 0.1:
            return 'YZ'
    except Exception:
        pass

    return 'custom'


def transform_to_sketch_coords(x, y, sketch):
    """Transform world-intuitive coordinates to sketch-local coordinates.

    For XZ plane sketches: user provides (x, z_world) in world terms.
    Sketch local Y maps to -world Z, so we negate y to correct.
    For XY and YZ planes: no correction needed, pass through unchanged.

    This correction is silent -- the user never knows it happens.
    """
    plane = detect_sketch_plane(sketch)
    if plane == 'XZ':
        return (x, -y)
    return (x, y)


def transform_from_sketch_coords(x, y, sketch):
    """Transform sketch-local coordinates back to world-intuitive coordinates.

    Reverse of transform_to_sketch_coords. For XZ plane, negate y
    back to world Z. For XY and YZ planes, pass through unchanged.

    Used for tool responses that return coordinates, so input/output
    coordinates are consistent from the user's perspective.
    """
    plane = detect_sketch_plane(sketch)
    if plane == 'XZ':
        return (x, -y)
    return (x, y)


def create_point(x, y, sketch=None):
    """Create a Point3D with coordinate correction applied if needed.

    If a sketch is provided and it's on the XZ plane, coordinates
    are silently corrected. Z coordinate is always 0 (sketch-local).
    """
    if sketch is not None:
        x, y = transform_to_sketch_coords(x, y, sketch)
    return adsk.core.Point3D.create(x, y, 0)
