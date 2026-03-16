import adsk.core
import adsk.fusion


def resolve_edges(body, selectors):
    """Resolve a list of edge selectors to BRepEdge objects.

    Each selector can be:
    - An integer: direct edge index via body.edges.item(i)
    - A string: semantic name resolved via SEMANTIC_EDGE_SELECTORS

    When a semantic selector matches multiple edges, ALL matches are returned.

    Args:
        body: BRepBody to select edges from
        selectors: List of int or str selectors

    Returns:
        List of BRepEdge objects

    Raises:
        ValueError: If an integer index is out of range
    """
    if not selectors:
        return []

    edges = []
    for selector in selectors:
        if isinstance(selector, int):
            if selector < 0 or selector >= body.edges.count:
                raise ValueError(
                    f"Edge index {selector} out of range. Body has {body.edges.count} edges (0-{body.edges.count - 1}). "
                    f"Use get_body_info() to see available edges."
                )
            edges.append(body.edges.item(selector))
        elif isinstance(selector, str):
            resolver = SEMANTIC_EDGE_SELECTORS.get(selector.lower())
            if resolver is None:
                available = ', '.join(sorted(SEMANTIC_EDGE_SELECTORS.keys()))
                raise ValueError(
                    f"Unknown edge selector '{selector}'. Available selectors: {available}"
                )
            matched = resolver(body)
            if isinstance(matched, list):
                edges.extend(matched)
            else:
                edges.append(matched)
    return edges


def resolve_faces(body, selectors):
    """Resolve a list of face selectors to BRepFace objects.

    Each selector can be:
    - An integer: direct face index via body.faces.item(i)
    - A string: semantic name resolved via SEMANTIC_FACE_SELECTORS

    When a semantic selector matches multiple faces, ALL matches are returned.

    Args:
        body: BRepBody to select faces from
        selectors: List of int or str selectors

    Returns:
        List of BRepFace objects

    Raises:
        ValueError: If an integer index is out of range
    """
    if not selectors:
        return []

    faces = []
    for selector in selectors:
        if isinstance(selector, int):
            if selector < 0 or selector >= body.faces.count:
                raise ValueError(
                    f"Face index {selector} out of range. Body has {body.faces.count} faces (0-{body.faces.count - 1}). "
                    f"Use get_body_info() to see available faces."
                )
            faces.append(body.faces.item(selector))
        elif isinstance(selector, str):
            resolver = SEMANTIC_FACE_SELECTORS.get(selector.lower())
            if resolver is None:
                available = ', '.join(sorted(SEMANTIC_FACE_SELECTORS.keys()))
                raise ValueError(
                    f"Unknown face selector '{selector}'. Available selectors: {available}"
                )
            matched = resolver(body)
            if isinstance(matched, list):
                faces.extend(matched)
            else:
                faces.append(matched)
    return faces


def label_edge(edge, index, body):
    """Generate a semantic label for an edge.

    Computes the edge's midpoint position relative to the body bounding box
    to determine position labels (top/bottom/left/right/front/back).
    Includes edge geometry type and length.

    Returns:
        String label like "Edge 3 (top-front, linear, 5.00cm)"
    """
    bbox = body.boundingBox
    mid_x = (bbox.minPoint.x + bbox.maxPoint.x) / 2
    mid_y = (bbox.minPoint.y + bbox.maxPoint.y) / 2
    mid_z = (bbox.minPoint.z + bbox.maxPoint.z) / 2

    # Get edge midpoint
    try:
        pt = edge.pointOnEdge
        ex, ey, ez = pt.x, pt.y, pt.z
    except Exception:
        return f"Edge {index} ({round(edge.length, 2)}cm)"

    # Position labels
    positions = []
    threshold = 0.01  # tolerance for "at center"
    range_x = bbox.maxPoint.x - bbox.minPoint.x
    range_y = bbox.maxPoint.y - bbox.minPoint.y
    range_z = bbox.maxPoint.z - bbox.minPoint.z

    if range_y > threshold:
        if ey > mid_y + range_y * 0.25:
            positions.append("top")
        elif ey < mid_y - range_y * 0.25:
            positions.append("bottom")

    if range_z > threshold:
        if ez > mid_z + range_z * 0.25:
            positions.append("front")
        elif ez < mid_z - range_z * 0.25:
            positions.append("back")

    if range_x > threshold:
        if ex > mid_x + range_x * 0.25:
            positions.append("right")
        elif ex < mid_x - range_x * 0.25:
            positions.append("left")

    # Edge geometry type
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

    pos_str = "-".join(positions) if positions else "center"
    return f"Edge {index} ({pos_str}, {edge_type}, {round(edge.length, 2)}cm)"


def label_face(face, index, body):
    """Generate a semantic label for a face.

    Determines face type (planar, cylindrical, etc.) and centroid position
    relative to the body bounding box.

    Returns:
        String label like "Face 0 (top, planar, 25.00cm2)"
    """
    bbox = body.boundingBox
    mid_x = (bbox.minPoint.x + bbox.maxPoint.x) / 2
    mid_y = (bbox.minPoint.y + bbox.maxPoint.y) / 2
    mid_z = (bbox.minPoint.z + bbox.maxPoint.z) / 2

    # Face type
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

    # Centroid position
    positions = []
    try:
        centroid = face.centroid
        cx, cy, cz = centroid.x, centroid.y, centroid.z

        threshold = 0.01
        range_x = bbox.maxPoint.x - bbox.minPoint.x
        range_y = bbox.maxPoint.y - bbox.minPoint.y
        range_z = bbox.maxPoint.z - bbox.minPoint.z

        if range_y > threshold:
            if cy > mid_y + range_y * 0.25:
                positions.append("top")
            elif cy < mid_y - range_y * 0.25:
                positions.append("bottom")

        if range_z > threshold:
            if cz > mid_z + range_z * 0.25:
                positions.append("front")
            elif cz < mid_z - range_z * 0.25:
                positions.append("back")

        if range_x > threshold:
            if cx > mid_x + range_x * 0.25:
                positions.append("right")
            elif cx < mid_x - range_x * 0.25:
                positions.append("left")
    except Exception:
        pass

    pos_str = "-".join(positions) if positions else "center"
    area = round(face.area, 2)
    return f"Face {index} ({pos_str}, {face_type}, {area}cm2)"


# --- Semantic Edge Selectors ---

def _top_edges(body):
    """Edges with highest midpoint Y position."""
    return _edges_by_position(body, axis='y', direction='max')


def _bottom_edges(body):
    """Edges with lowest midpoint Y position."""
    return _edges_by_position(body, axis='y', direction='min')


def _left_edges(body):
    """Edges with lowest midpoint X position."""
    return _edges_by_position(body, axis='x', direction='min')


def _right_edges(body):
    """Edges with highest midpoint X position."""
    return _edges_by_position(body, axis='x', direction='max')


def _front_edges(body):
    """Edges with highest midpoint Z position."""
    return _edges_by_position(body, axis='z', direction='max')


def _back_edges(body):
    """Edges with lowest midpoint Z position."""
    return _edges_by_position(body, axis='z', direction='min')


def _longest_edge(body):
    """Edge with greatest length."""
    best = None
    best_len = -1
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        if edge.length > best_len:
            best_len = edge.length
            best = edge
    return [best] if best else []


def _shortest_edge(body):
    """Edge with smallest length."""
    best = None
    best_len = float('inf')
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        if edge.length < best_len:
            best_len = edge.length
            best = edge
    return [best] if best else []


def _edges_by_position(body, axis, direction):
    """Find edges at the extreme position along an axis.

    Returns all edges whose midpoint is within tolerance of the extreme value.
    """
    bbox = body.boundingBox
    axis_map = {'x': 0, 'y': 1, 'z': 2}
    axis_idx = axis_map[axis]

    edge_positions = []
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        try:
            pt = edge.pointOnEdge
            pos = [pt.x, pt.y, pt.z][axis_idx]
            edge_positions.append((edge, pos))
        except Exception:
            continue

    if not edge_positions:
        return []

    if direction == 'max':
        extreme = max(p for _, p in edge_positions)
    else:
        extreme = min(p for _, p in edge_positions)

    # Tolerance: edges within 1% of body size from the extreme
    axis_range = [
        bbox.maxPoint.x - bbox.minPoint.x,
        bbox.maxPoint.y - bbox.minPoint.y,
        bbox.maxPoint.z - bbox.minPoint.z
    ][axis_idx]
    tolerance = max(axis_range * 0.01, 0.001)

    return [edge for edge, pos in edge_positions if abs(pos - extreme) <= tolerance]


# --- Semantic Face Selectors ---

def _top_face(body):
    """Face(s) with highest centroid Y position."""
    return _faces_by_position(body, axis='y', direction='max')


def _bottom_face(body):
    """Face(s) with lowest centroid Y position."""
    return _faces_by_position(body, axis='y', direction='min')


def _left_face(body):
    """Face(s) with lowest centroid X position."""
    return _faces_by_position(body, axis='x', direction='min')


def _right_face(body):
    """Face(s) with highest centroid X position."""
    return _faces_by_position(body, axis='x', direction='max')


def _front_face(body):
    """Face(s) with highest centroid Z position."""
    return _faces_by_position(body, axis='z', direction='max')


def _back_face(body):
    """Face(s) with lowest centroid Z position."""
    return _faces_by_position(body, axis='z', direction='min')


def _largest_face(body):
    """Face with greatest area."""
    best = None
    best_area = -1
    for i in range(body.faces.count):
        face = body.faces.item(i)
        if face.area > best_area:
            best_area = face.area
            best = face
    return [best] if best else []


def _smallest_face(body):
    """Face with smallest area."""
    best = None
    best_area = float('inf')
    for i in range(body.faces.count):
        face = body.faces.item(i)
        if face.area < best_area:
            best_area = face.area
            best = face
    return [best] if best else []


def _faces_by_position(body, axis, direction):
    """Find faces at the extreme position along an axis.

    Returns all faces whose centroid is within tolerance of the extreme value.
    """
    bbox = body.boundingBox
    axis_map = {'x': 0, 'y': 1, 'z': 2}
    axis_idx = axis_map[axis]

    face_positions = []
    for i in range(body.faces.count):
        face = body.faces.item(i)
        try:
            centroid = face.centroid
            pos = [centroid.x, centroid.y, centroid.z][axis_idx]
            face_positions.append((face, pos))
        except Exception:
            continue

    if not face_positions:
        return []

    if direction == 'max':
        extreme = max(p for _, p in face_positions)
    else:
        extreme = min(p for _, p in face_positions)

    axis_range = [
        bbox.maxPoint.x - bbox.minPoint.x,
        bbox.maxPoint.y - bbox.minPoint.y,
        bbox.maxPoint.z - bbox.minPoint.z
    ][axis_idx]
    tolerance = max(axis_range * 0.01, 0.001)

    return [face for face, pos in face_positions if abs(pos - extreme) <= tolerance]


# Semantic selector maps
SEMANTIC_EDGE_SELECTORS = {
    'top_edge': _top_edges,
    'top_edges': _top_edges,
    'bottom_edge': _bottom_edges,
    'bottom_edges': _bottom_edges,
    'left_edge': _left_edges,
    'left_edges': _left_edges,
    'right_edge': _right_edges,
    'right_edges': _right_edges,
    'front_edge': _front_edges,
    'front_edges': _front_edges,
    'back_edge': _back_edges,
    'back_edges': _back_edges,
    'longest_edge': _longest_edge,
    'shortest_edge': _shortest_edge,
}

SEMANTIC_FACE_SELECTORS = {
    'top_face': _top_face,
    'bottom_face': _bottom_face,
    'left_face': _left_face,
    'right_face': _right_face,
    'front_face': _front_face,
    'back_face': _back_face,
    'largest_face': _largest_face,
    'smallest_face': _smallest_face,
}
