#!/usr/bin/env python3
"""
Fusion 360 MCP Server v7.2 - ENHANCED
=======================================
Based on v6.0 Optimized, with critical new features:

NEW TOOLS:
  o move_component    - Position components after creation (CRITICAL)
  o rotate_component  - Rotate components around axes
  o shell             - Create hollow parts/enclosures (CRITICAL)
  o draft             - Injection molding draft angles
  o pattern_rectangular - Linear arrays
  o pattern_circular  - Radial arrays
  o mirror            - Symmetric geometry
  o measure           - Dimension verification
  o get_body_info     - Edge/face listing for selection

ENHANCED TOOLS:
  o create_sketch     - Now supports offset parameter
  o extrude           - Now supports taper_angle and profile_index
  o fillet            - Now supports selective edge indices
  o chamfer           - Now supports selective edge indices

PRESERVED:
  o Batch operations (5-10x faster)
  o 50ms polling
  o 45s timeout
  o All v6.0 features
"""
from mcp.server.fastmcp import FastMCP
import json
import time
from pathlib import Path

COMM_DIR = Path.home() / "fusion_mcp_comm"
COMM_DIR.mkdir(exist_ok=True)

RESOURCES_DIR = Path(__file__).parent / "resources"

mcp = FastMCP("Fusion 360 v7.2 Enhanced")

def send_fusion_command(tool_name: str, params: dict) -> dict:
    """Send command to Fusion 360 via file system"""
    timestamp = int(time.time() * 1000)
    cmd_file = COMM_DIR / f"command_{timestamp}.json"
    resp_file = COMM_DIR / f"response_{timestamp}.json"
    
    with open(cmd_file, 'w') as f:
        json.dump({"type": "tool", "name": tool_name, "params": params, "id": timestamp}, f)
    
    # 900 iterations at 50ms = 45s timeout
    for _ in range(900):
        time.sleep(0.05)  # 50ms polling
        if resp_file.exists():
            with open(resp_file, 'r') as f:
                result = json.load(f)
            try:
                cmd_file.unlink()
                resp_file.unlink()
            except:
                pass
            if not result.get("success"):
                raise Exception(result.get("error", "Unknown error"))
            return result
    
    raise Exception("Timeout after 45s - is Fusion 360 running with FusionMCP add-in?")

# =============================================================================
# BATCH OPERATIONS
# =============================================================================

@mcp.tool()
def batch(commands: list) -> dict:
    """
    Execute multiple Fusion commands in a single call - MUCH faster for complex operations.
    
    Example: batch([
        {"name": "create_sketch", "params": {"plane": "XY"}},
        {"name": "draw_rectangle", "params": {"x1": -5, "y1": -5, "x2": 5, "y2": 5}},
        {"name": "draw_circle", "params": {"center_x": 0, "center_y": 0, "radius": 2}},
        {"name": "finish_sketch", "params": {}},
        {"name": "extrude", "params": {"distance": 3}}
    ])
    
    This executes all commands in one round-trip instead of 5 separate calls.
    Stops on first error and returns partial results.
    """
    return send_fusion_command("batch", {"commands": commands})

# =============================================================================
# SKETCH CREATION (ENHANCED)
# =============================================================================

@mcp.tool()
def create_sketch(plane: str = "XY", offset: float = 0, body_index: int = None, face: str = None) -> dict:
    """
    Create a new sketch and enter edit mode.

    By default creates sketch on a construction plane (XY, XZ, or YZ).
    Optionally sketch on a body face by providing body_index + face params.
    When face is provided, the plane param is ignored.

    Args:
        plane: Construction plane name (XY, XZ, YZ). Ignored if face is provided.
        offset: Offset distance from plane (cm). Only for construction planes.
        body_index: Body to sketch on (0 = first body). Required with face.
        face: Face selector - semantic name ('top_face', 'bottom_face') or integer index. Use get_body_info() to see faces.

    Examples:
        create_sketch(plane="XY")                          # Horizontal at origin
        create_sketch(plane="XZ", offset=5)                # Vertical, 5cm forward
        create_sketch(body_index=0, face="top_face")       # Sketch on body's top face
        create_sketch(body_index=0, face="0")              # Sketch on face index 0
    """
    params = {"plane": plane, "offset": offset}
    if body_index is not None:
        params["body_index"] = body_index
    if face is not None:
        params["face"] = face
    return send_fusion_command("create_sketch", params)

@mcp.tool()
def finish_sketch() -> dict:
    """Exit sketch editing mode"""
    return send_fusion_command("finish_sketch", {})

# =============================================================================
# SKETCH GEOMETRY
# =============================================================================

@mcp.tool()
def draw_rectangle(x1: float, y1: float, x2: float, y2: float) -> dict:
    """Draw a rectangle in the active sketch (units: cm)"""
    return send_fusion_command("draw_rectangle", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})

@mcp.tool()
def draw_circle(center_x: float, center_y: float, radius: float) -> dict:
    """Draw a circle in the active sketch (units: cm)"""
    return send_fusion_command("draw_circle", {"center_x": center_x, "center_y": center_y, "radius": radius})

@mcp.tool()
def draw_line(x1: float, y1: float, x2: float, y2: float) -> dict:
    """Draw a straight line in the active sketch (units: cm)"""
    return send_fusion_command("draw_line", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})

@mcp.tool()
def draw_arc(center_x: float, center_y: float, start_x: float, start_y: float, end_x: float, end_y: float) -> dict:
    """Draw an arc in the active sketch (units: cm)"""
    return send_fusion_command("draw_arc", {
        "center_x": center_x, "center_y": center_y,
        "start_x": start_x, "start_y": start_y,
        "end_x": end_x, "end_y": end_y
    })

@mcp.tool()
def draw_polygon(center_x: float, center_y: float, radius: float, sides: int = 6) -> dict:
    """Draw a regular polygon in the active sketch (units: cm). Default is hexagon."""
    return send_fusion_command("draw_polygon", {
        "center_x": center_x, "center_y": center_y, 
        "radius": radius, "sides": sides
    })

# =============================================================================
# SKETCH ENTITY TOOLS
# =============================================================================

@mcp.tool()
def set_construction(curve_index: int, is_construction: bool = True) -> dict:
    """Toggle a sketch curve between regular and construction geometry.
    Construction geometry is used as reference but not included in profiles.

    Args:
        curve_index: Index of the curve to toggle. Use get_sketch_info() to see available curves.
        is_construction: True to make construction, False to make regular. Default True.
    """
    return send_fusion_command("set_construction", {
        "curve_index": curve_index,
        "is_construction": is_construction
    })

# =============================================================================
# NEW SKETCH PRIMITIVES (Phase 2)
# =============================================================================

@mcp.tool()
def draw_spline(points: list) -> dict:
    """Draw a fitted spline through a collection of points in the active sketch.

    Args:
        points: List of [x, y] coordinate pairs (minimum 2 points). Units: cm.

    Example: draw_spline(points=[[0,0], [2,3], [5,1], [8,4]])
    """
    return send_fusion_command("draw_spline", {"points": points})

@mcp.tool()
def draw_ellipse(center_x: float, center_y: float, major_radius: float, minor_radius: float, angle: float = 0) -> dict:
    """Draw an ellipse in the active sketch (units: cm).

    Args:
        center_x: Center X coordinate
        center_y: Center Y coordinate
        major_radius: Semi-major axis length
        minor_radius: Semi-minor axis length
        angle: Rotation angle of major axis in degrees (default 0)
    """
    return send_fusion_command("draw_ellipse", {
        "center_x": center_x, "center_y": center_y,
        "major_radius": major_radius, "minor_radius": minor_radius,
        "angle": angle
    })

@mcp.tool()
def draw_slot(center_x: float, center_y: float, end_x: float, end_y: float, width: float) -> dict:
    """Draw a center-point slot in the active sketch (units: cm).
    A slot is a rounded rectangle defined by center, end point, and width.

    Args:
        center_x: Slot center X
        center_y: Slot center Y
        end_x: End point X (defines slot length/direction)
        end_y: End point Y
        width: Slot width (perpendicular to length direction)
    """
    return send_fusion_command("draw_slot", {
        "center_x": center_x, "center_y": center_y,
        "end_x": end_x, "end_y": end_y, "width": width
    })

@mcp.tool()
def draw_point(x: float, y: float) -> dict:
    """Add a reference/construction point to the active sketch (units: cm).

    Args:
        x: Point X coordinate
        y: Point Y coordinate
    """
    return send_fusion_command("draw_point", {"x": x, "y": y})

@mcp.tool()
def draw_text(text: str, height: float, x: float = 0, y: float = 0, font: str = None) -> dict:
    """Draw text in the active sketch. Text profiles can be extruded for embossing/engraving.

    Args:
        text: The text string to draw
        height: Text height in cm
        x: Text position X (default 0)
        y: Text position Y (default 0)
        font: Font name (optional, uses system default)
    """
    params = {"text": text, "height": height, "x": x, "y": y}
    if font is not None:
        params["font"] = font
    return send_fusion_command("draw_text", params)

# =============================================================================
# SKETCH OPERATIONS (Phase 2)
# =============================================================================

@mcp.tool()
def offset_curves(curve_index: int, distance: float, direction_x: float = 0, direction_y: float = 1) -> dict:
    """Create offset curves parallel to existing sketch geometry at a uniform distance.

    Args:
        curve_index: Index of a curve to offset (connected curves are included automatically)
        distance: Offset distance in cm
        direction_x: X component of offset direction (default 0)
        direction_y: Y component of offset direction (default 1)

    Use get_sketch_info() to see available curve indices.
    """
    return send_fusion_command("offset_curves", {
        "curve_index": curve_index, "distance": distance,
        "direction_x": direction_x, "direction_y": direction_y
    })

@mcp.tool()
def project_geometry(body_index: int = 0, edge_index: int = None, face_index: int = None) -> dict:
    """Project body edges or faces onto the active sketch plane.

    Args:
        body_index: Which body to project from (default 0)
        edge_index: Specific edge index to project (optional)
        face_index: Specific face index to project (optional)

    If neither edge_index nor face_index provided, projects all edges.
    Use get_body_info() to see available edge/face indices.
    """
    params = {"body_index": body_index}
    if edge_index is not None:
        params["edge_index"] = edge_index
    if face_index is not None:
        params["face_index"] = face_index
    return send_fusion_command("project_geometry", params)

@mcp.tool()
def import_svg(file_path: str, x: float = 0, y: float = 0, scale: float = 1.0) -> dict:
    """Import an SVG file into the active sketch. Uses Fusion 360's native SVG import.

    Args:
        file_path: Full path to the SVG file
        x: X position for import origin (default 0)
        y: Y position for import origin (default 0)
        scale: Scale factor (default 1.0 = native SVG dimensions)
    """
    return send_fusion_command("import_svg", {
        "file_path": file_path, "x": x, "y": y, "scale": scale
    })

# =============================================================================
# CONSTRUCTION GEOMETRY (Phase 3)
# =============================================================================

@mcp.tool()
def construction_plane(mode: str = "offset", plane: str = "XY", offset: float = 1.0, axis: str = "X", angle: float = 45.0) -> dict:
    """
    Create a construction (reference) plane for sketching or feature operations.

    Args:
        mode: Creation mode - "offset" (parallel to base plane) or "angle" (rotated around axis)
        plane: Base plane - "XY", "XZ", or "YZ" (default "XY")
        offset: Distance from base plane in cm (used in offset mode, default 1.0)
        axis: Rotation axis for angle mode - "X", "Y", or "Z" (default "X")
        angle: Rotation angle in degrees (used in angle mode, default 45.0)
    """
    params = {"mode": mode, "plane": plane, "offset": offset, "axis": axis, "angle": angle}
    return send_fusion_command("construction_plane", params)

@mcp.tool()
def construction_axis(mode: str = "two_points", point1_x: float = 0, point1_y: float = 0, point1_z: float = 0, point2_x: float = 0, point2_y: float = 0, point2_z: float = 1.0) -> dict:
    """
    Create a construction (reference) axis for patterns, revolves, or other operations.

    Args:
        mode: Creation mode - "two_points" (default)
        point1_x: First point X coordinate in cm (default 0)
        point1_y: First point Y coordinate in cm (default 0)
        point1_z: First point Z coordinate in cm (default 0)
        point2_x: Second point X coordinate in cm (default 0)
        point2_y: Second point Y coordinate in cm (default 0)
        point2_z: Second point Z coordinate in cm (default 1.0)
    """
    params = {
        "mode": mode,
        "point1": {"x": point1_x, "y": point1_y, "z": point1_z},
        "point2": {"x": point2_x, "y": point2_y, "z": point2_z}
    }
    return send_fusion_command("construction_axis", params)

@mcp.tool()
def construction_point(x: float = 0, y: float = 0, z: float = 0) -> dict:
    """
    Create a construction (reference) point for positioning holes, patterns, or other features.

    Args:
        x: X coordinate in cm (default 0)
        y: Y coordinate in cm (default 0)
        z: Z coordinate in cm (default 0)
    """
    return send_fusion_command("construction_point", {"x": x, "y": y, "z": z})

# =============================================================================
# MANUFACTURING FEATURES (HOLES & THREADS)
# =============================================================================

@mcp.tool()
def hole(diameter: float, depth: float = None, hole_type: str = "simple",
         x: float = 0, y: float = 0, face: int = None, body_index: int = None,
         counterbore_diameter: float = None, counterbore_depth: float = None,
         countersink_diameter: float = None, countersink_angle: float = 82) -> dict:
    """
    Create a hole in a body face. Automatically creates a sketch point for positioning.

    Supports three hole types: simple, counterbore, and countersink.
    If depth is omitted, creates a through-all hole.

    Args:
        diameter: Hole diameter in cm
        depth: Hole depth in cm (omit for through-all)
        hole_type: "simple", "counterbore", or "countersink" (default "simple")
        x: X position on face in cm (default 0)
        y: Y position on face in cm (default 0)
        face: Face index for hole placement (default: top face)
        body_index: Which body (default: most recent)
        counterbore_diameter: Counterbore diameter in cm (required for counterbore type)
        counterbore_depth: Counterbore depth in cm (required for counterbore type)
        countersink_diameter: Countersink diameter in cm (required for countersink type)
        countersink_angle: Countersink angle in degrees (default 82)

    Use get_body_info() to find face indices.
    """
    params = {"diameter": diameter, "hole_type": hole_type, "x": x, "y": y,
              "countersink_angle": countersink_angle}
    if depth is not None:
        params["depth"] = depth
    if face is not None:
        params["face"] = face
    if body_index is not None:
        params["body_index"] = body_index
    if counterbore_diameter is not None:
        params["counterbore_diameter"] = counterbore_diameter
    if counterbore_depth is not None:
        params["counterbore_depth"] = counterbore_depth
    if countersink_diameter is not None:
        params["countersink_diameter"] = countersink_diameter
    return send_fusion_command("hole", params)

@mcp.tool()
def thread(face: int, body_index: int = None, thread_type: str = "ISO Metric profile",
           designation: str = "M6x1.0", thread_class: str = "6g",
           is_internal: bool = False, full_length: bool = True,
           length: float = None) -> dict:
    """
    Apply threads to a cylindrical face. Face MUST be cylindrical.

    Uses ISO Metric thread specifications by default. Common designations:
    M3x0.5, M4x0.7, M5x0.8, M6x1.0, M8x1.25, M10x1.5, M12x1.75

    Args:
        face: Face index of the cylindrical face to thread (use get_body_info() to find)
        body_index: Which body (default: most recent)
        thread_type: Thread standard (default "ISO Metric profile")
        designation: Thread size designation (default "M6x1.0")
        thread_class: Thread tolerance class (default "6g" for external, use "6H" for internal)
        is_internal: True for internal threads (holes), False for external (default False)
        full_length: Thread the full length of the face (default True)
        length: Thread length in cm (used when full_length is False)
    """
    params = {"face": face, "thread_type": thread_type,
              "designation": designation, "thread_class": thread_class,
              "is_internal": is_internal, "full_length": full_length}
    if body_index is not None:
        params["body_index"] = body_index
    if length is not None:
        params["length"] = length
    return send_fusion_command("thread", params)

# =============================================================================
# 3D FEATURE OPERATIONS (ENHANCED)
# =============================================================================

@mcp.tool()
def extrude(distance: float, profile_index: int = 0, taper_angle: float = 0) -> dict:
    """
    Extrude the most recent sketch profile (units: cm).
    
    Args:
        distance: Extrusion distance (positive or negative)
        profile_index: Which profile if multiple exist (default 0)
        taper_angle: Draft angle during extrusion in degrees (default 0)
    """
    return send_fusion_command("extrude", {
        "distance": distance, 
        "profile_index": profile_index, 
        "taper_angle": taper_angle
    })

@mcp.tool()
def revolve(angle: float, axis: str = "Y") -> dict:
    """
    Revolve the most recent sketch profile around an axis (degrees).

    Args:
        angle: Revolve angle in degrees (360 for full revolution)
        axis: Revolve axis - "X", "Y", or "Z" (default "Y")
    """
    return send_fusion_command("revolve", {"angle": angle, "axis": axis})

@mcp.tool()
def sweep(profile_sketch_index: int = None, profile_index: int = 0,
          path_sketch_index: int = None, path_curve_index: int = 0,
          taper_angle: float = 0, twist_angle: float = 0,
          operation: str = "new") -> dict:
    """
    Sweep a sketch profile along a path curve to create pipes, channels, or curved extrusions.

    IMPORTANT: Profile and path must be in DIFFERENT sketches.
    Default behavior: uses second-to-last sketch for profile, last sketch for path.

    Args:
        profile_sketch_index: Sketch containing the profile (default: second-to-last sketch)
        profile_index: Which profile in the sketch (default 0)
        path_sketch_index: Sketch containing the path curve (default: last sketch)
        path_curve_index: Which curve to use as path (default 0)
        taper_angle: Taper angle in degrees during sweep (default 0)
        twist_angle: Twist angle in degrees along sweep (default 0)
        operation: "new", "join", "cut", or "intersect" (default "new")
    """
    params = {
        "profile_index": profile_index,
        "path_curve_index": path_curve_index,
        "taper_angle": taper_angle,
        "twist_angle": twist_angle,
        "operation": operation
    }
    if profile_sketch_index is not None:
        params["profile_sketch_index"] = profile_sketch_index
    if path_sketch_index is not None:
        params["path_sketch_index"] = path_sketch_index
    return send_fusion_command("sweep", params)

@mcp.tool()
def loft(sketch_indices: list, profile_indices: list = None,
         is_solid: bool = True, is_closed: bool = False,
         operation: str = "new") -> dict:
    """
    Loft between 2 or more sketch profiles to create smooth shape transitions.

    Each profile must be in a different sketch on a different plane.
    Use construction_plane() to create offset planes for multi-section lofts.

    Args:
        sketch_indices: List of sketch indices containing profiles (minimum 2, order matters)
        profile_indices: List of profile indices per sketch (default [0, 0, ...])
        is_solid: Create solid body (True) or surface (False) (default True)
        is_closed: Close the loft (connect last section to first) (default False)
        operation: "new", "join", "cut", or "intersect" (default "new")
    """
    params = {
        "sketch_indices": sketch_indices,
        "is_solid": is_solid,
        "is_closed": is_closed,
        "operation": operation
    }
    if profile_indices is not None:
        params["profile_indices"] = profile_indices
    return send_fusion_command("loft", params)

@mcp.tool()
def fillet(radius: float, edges: list = None, body_index: int = None) -> dict:
    """
    Add fillets to edges of a body (units: cm).
    
    Args:
        radius: Fillet radius
        edges: Optional list of edge indices. If None, fillets all edges.
        body_index: Which body (default: most recent)
    
    Use get_body_info() to see available edge indices.
    """
    params = {"radius": radius}
    if edges is not None:
        params["edges"] = edges
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("fillet", params)

@mcp.tool()
def chamfer(distance: float, edges: list = None, body_index: int = None) -> dict:
    """
    Add chamfers to edges of a body (units: cm).
    
    Args:
        distance: Chamfer distance
        edges: Optional list of edge indices. If None, chamfers all edges.
        body_index: Which body (default: most recent)
    
    Use get_body_info() to see available edge indices.
    """
    params = {"distance": distance}
    if edges is not None:
        params["edges"] = edges
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("chamfer", params)

# =============================================================================
# NEW: SHELL, DRAFT, PATTERNS, MIRROR
# =============================================================================

@mcp.tool()
def shell(thickness: float, faces_to_remove: list = None, body_index: int = None) -> dict:
    """
    Create a hollow shell from a solid body (units: cm).
    
    Args:
        thickness: Wall thickness
        faces_to_remove: List of face indices to remove (create openings). Default: closed shell.
        body_index: Which body (default: most recent)
    
    Examples:
        shell(thickness=0.2)                        # 2mm closed shell
        shell(thickness=0.15, faces_to_remove=[0])  # Open-top container
    
    Use get_body_info() to see available face indices.
    """
    params = {"thickness": thickness}
    if faces_to_remove is not None:
        params["faces_to_remove"] = faces_to_remove
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("shell", params)

@mcp.tool()
def draft(angle: float, faces: list = None, body_index: int = None, 
          pull_x: float = 0, pull_y: float = 0, pull_z: float = 1) -> dict:
    """
    Apply draft angles to faces for injection molding (angle in degrees).
    
    Args:
        angle: Draft angle (typically 0.5-3 degrees, guideline: 1 degree per inch)
        faces: List of face indices. If None, drafts all faces.
        body_index: Which body (default: most recent)
        pull_x, pull_y, pull_z: Pull direction vector (default: +Z)
    """
    params = {"angle": angle, "pull_x": pull_x, "pull_y": pull_y, "pull_z": pull_z}
    if faces is not None:
        params["faces"] = faces
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("draft", params)

@mcp.tool()
def pattern_rectangular(x_count: int, x_spacing: float, 
                        y_count: int = 1, y_spacing: float = 0, 
                        body_index: int = None) -> dict:
    """
    Create a rectangular (linear) pattern of a body (spacing in cm).
    
    Args:
        x_count: Number of instances in X direction
        x_spacing: Spacing between instances in X
        y_count: Number of instances in Y direction (default 1)
        y_spacing: Spacing between instances in Y
        body_index: Which body (default: most recent)
    
    Example:
        pattern_rectangular(x_count=4, x_spacing=2.5, y_count=3, y_spacing=2.5)
        # Creates 4x3 = 12 instances
    """
    params = {"x_count": x_count, "x_spacing": x_spacing, "y_count": y_count, "y_spacing": y_spacing}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("pattern_rectangular", params)

@mcp.tool()
def pattern_circular(count: int, angle: float = 360, axis: str = "Z", body_index: int = None) -> dict:
    """
    Create a circular (radial) pattern of a body.
    
    Args:
        count: Number of instances
        angle: Total angle in degrees (default 360 for full circle)
        axis: Rotation axis - "X", "Y", or "Z" (default "Z")
        body_index: Which body (default: most recent)
    
    Example:
        pattern_circular(count=6, angle=360, axis="Z")
        # 6 instances evenly spaced around Z axis
    """
    params = {"count": count, "angle": angle, "axis": axis}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("pattern_circular", params)

@mcp.tool()
def mirror(plane: str = "YZ", body_index: int = None) -> dict:
    """
    Create a mirrored copy of a body.
    
    Args:
        plane: Mirror plane - "XY", "XZ", or "YZ" (default "YZ" for left-right symmetry)
        body_index: Which body (default: most recent)
    """
    params = {"plane": plane}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("mirror", params)

# =============================================================================
# VIEW & DESIGN INFO
# =============================================================================

@mcp.tool()
def fit_view() -> dict:
    """Fit the viewport to show all geometry"""
    return send_fusion_command("fit_view", {})

@mcp.tool()
def get_design_info() -> dict:
    """Get information about the current design (name, body count, sketch count, component count, active sketch status)"""
    return send_fusion_command("get_design_info", {})

# =============================================================================
# NEW: MEASUREMENT & INSPECTION
# =============================================================================

@mcp.tool()
def get_body_info(body_index: int = None) -> dict:
    """
    Get detailed information about a body including all edges and faces.
    
    Args:
        body_index: Which body (default: most recent)
    
    Returns edge indices with lengths, face indices with areas.
    Use this to find indices for selective fillet, chamfer, shell, or draft.
    """
    params = {}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("get_body_info", params)

@mcp.tool()
def get_sketch_info() -> dict:
    """Get detailed information about the active sketch including all curves, points, constraints, and dimensions.

    Returns curves with semantic labels (e.g., "Curve 0 (line, horizontal, 5cm)"),
    points with coordinates, geometric constraints, parametric dimensions, and
    overall constraint status.

    This is the primary tool for understanding sketch state before applying
    constraints, dimensions, or other operations. Similar to get_body_info for 3D bodies.

    Example workflow:
        1. create_sketch(plane="XY")
        2. draw_line(...), draw_circle(...)
        3. get_sketch_info()  # see all entities with indices
        4. constrain_horizontal(curve_index=0)
        5. dimension_distance(value=5, curve_index=0)
    """
    return send_fusion_command("get_sketch_info", {})

@mcp.tool()
def measure(type: str = "body", body_index: int = None,
            edge_index: int = None, face_index: int = None) -> dict:
    """
    Measure dimensions of bodies, edges, or faces.
    
    Args:
        type: What to measure - "body", "edge", or "face"
        body_index: Which body (default: most recent)
        edge_index: Edge index (for type="edge")
        face_index: Face index (for type="face")
    
    Returns:
        body: volume, surface_area, bounding_box with size
        edge: length
        face: area
    """
    params = {"type": type}
    if body_index is not None:
        params["body_index"] = body_index
    if edge_index is not None:
        params["edge_index"] = edge_index
    if face_index is not None:
        params["face_index"] = face_index
    return send_fusion_command("measure", params)

# =============================================================================
# COMPONENT & ASSEMBLY
# =============================================================================

@mcp.tool()
def create_component(name: str = None) -> dict:
    """Convert the most recent body into a new component for assembly"""
    params = {}
    if name:
        params["name"] = name
    return send_fusion_command("create_component", params)

@mcp.tool()
def list_components() -> dict:
    """List all components with names, positions, and bounding boxes"""
    return send_fusion_command("list_components", {})

@mcp.tool()
def delete_component(name: str = None, index: int = None) -> dict:
    """Delete a component by name or index"""
    params = {}
    if name:
        params["name"] = name
    if index is not None:
        params["index"] = index
    return send_fusion_command("delete_component", params)

@mcp.tool()
def check_interference() -> dict:
    """Check if any components overlap (bounding box collision detection)"""
    return send_fusion_command("check_interference", {})

# =============================================================================
# NEW: COMPONENT POSITIONING (CRITICAL)
# =============================================================================

@mcp.tool()
def move_component(x: float = 0, y: float = 0, z: float = 0,
                   index: int = None, name: str = None, 
                   absolute: bool = True) -> dict:
    """
    Move a component to a new position (units: cm).
    
    Args:
        x, y, z: Target position or offset
        index: Component index (from list_components)
        name: Component name (alternative to index)
        absolute: If True, set absolute position. If False, move by offset.
    
    Examples:
        move_component(x=0, y=10, z=0, index=1)                    # Move to Y=10
        move_component(x=5, y=0, z=0, index=0, absolute=False)     # Move 5cm in X
    
    CRITICAL: Use this to position components after creation to avoid overlaps.
    """
    params = {"x": x, "y": y, "z": z, "absolute": absolute}
    if index is not None:
        params["index"] = index
    if name is not None:
        params["name"] = name
    return send_fusion_command("move_component", params)

@mcp.tool()
def rotate_component(angle: float, axis: str = "Z",
                     index: int = None, name: str = None,
                     origin_x: float = 0, origin_y: float = 0, origin_z: float = 0) -> dict:
    """
    Rotate a component around an axis (angle in degrees).
    
    Args:
        angle: Rotation angle in degrees
        axis: Rotation axis - "X", "Y", or "Z" (default "Z")
        index: Component index (from list_components)
        name: Component name (alternative to index)
        origin_x, origin_y, origin_z: Rotation origin point (cm)
    """
    params = {
        "angle": angle, "axis": axis,
        "origin_x": origin_x, "origin_y": origin_y, "origin_z": origin_z
    }
    if index is not None:
        params["index"] = index
    if name is not None:
        params["name"] = name
    return send_fusion_command("rotate_component", params)

# =============================================================================
# JOINTS
# =============================================================================

@mcp.tool()
def create_revolute_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0,
    axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
    min_angle: float = None, max_angle: float = None,
    flip: bool = False
) -> dict:
    """Create a revolute (rotating) joint between two components"""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z, "flip": flip}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_angle is not None:
        params["min_angle"] = min_angle
    if max_angle is not None:
        params["max_angle"] = max_angle
    return send_fusion_command("create_revolute_joint", params)

@mcp.tool()
def create_slider_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0,
    axis_x: float = 1, axis_y: float = 0, axis_z: float = 0,
    min_distance: float = None, max_distance: float = None
) -> dict:
    """Create a slider (linear) joint between two components"""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_distance is not None:
        params["min_distance"] = min_distance
    if max_distance is not None:
        params["max_distance"] = max_distance
    return send_fusion_command("create_slider_joint", params)

@mcp.tool()
def create_rigid_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0
) -> dict:
    """Create a rigid (fixed) joint between two components. No relative motion allowed.
    Position defaults to origin since rigid joints lock components in place."""
    params = {"x": x, "y": y, "z": z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    return send_fusion_command("create_rigid_joint", params)

@mcp.tool()
def create_cylindrical_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0,
    axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
    min_angle: float = None, max_angle: float = None,
    min_distance: float = None, max_distance: float = None
) -> dict:
    """Create a cylindrical joint (rotation + translation along same axis)."""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_angle is not None:
        params["min_angle"] = min_angle
    if max_angle is not None:
        params["max_angle"] = max_angle
    if min_distance is not None:
        params["min_distance"] = min_distance
    if max_distance is not None:
        params["max_distance"] = max_distance
    return send_fusion_command("create_cylindrical_joint", params)

@mcp.tool()
def create_pin_slot_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0,
    axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
    min_angle: float = None, max_angle: float = None,
    min_distance: float = None, max_distance: float = None
) -> dict:
    """Create a pin-slot joint (rotation + sliding). Axis defines slot direction; rotation is perpendicular."""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_angle is not None:
        params["min_angle"] = min_angle
    if max_angle is not None:
        params["max_angle"] = max_angle
    if min_distance is not None:
        params["min_distance"] = min_distance
    if max_distance is not None:
        params["max_distance"] = max_distance
    return send_fusion_command("create_pin_slot_joint", params)

@mcp.tool()
def create_planar_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0,
    axis_x: float = 0, axis_y: float = 1, axis_z: float = 0,
    min_primary_slide: float = None, max_primary_slide: float = None,
    min_secondary_slide: float = None, max_secondary_slide: float = None,
    min_angle: float = None, max_angle: float = None
) -> dict:
    """Create a planar joint (2D sliding + rotation on a plane). Axis defines plane normal. All DOF unconstrained by default."""
    params = {"x": x, "y": y, "z": z, "axis_x": axis_x, "axis_y": axis_y, "axis_z": axis_z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_primary_slide is not None:
        params["min_primary_slide"] = min_primary_slide
    if max_primary_slide is not None:
        params["max_primary_slide"] = max_primary_slide
    if min_secondary_slide is not None:
        params["min_secondary_slide"] = min_secondary_slide
    if max_secondary_slide is not None:
        params["max_secondary_slide"] = max_secondary_slide
    if min_angle is not None:
        params["min_angle"] = min_angle
    if max_angle is not None:
        params["max_angle"] = max_angle
    return send_fusion_command("create_planar_joint", params)

@mcp.tool()
def create_ball_joint(
    component1_index: int = None,
    component2_index: int = None,
    x: float = 0, y: float = 0, z: float = 0,
    min_pitch: float = None, max_pitch: float = None,
    min_roll: float = None, max_roll: float = None,
    min_yaw: float = None, max_yaw: float = None
) -> dict:
    """Create a ball joint (spherical rotation, 3 DOF). No axis needed -- rotation is unconstrained in all directions."""
    params = {"x": x, "y": y, "z": z}
    if component1_index is not None:
        params["component1_index"] = component1_index
    if component2_index is not None:
        params["component2_index"] = component2_index
    if min_pitch is not None:
        params["min_pitch"] = min_pitch
    if max_pitch is not None:
        params["max_pitch"] = max_pitch
    if min_roll is not None:
        params["min_roll"] = min_roll
    if max_roll is not None:
        params["max_roll"] = max_roll
    if min_yaw is not None:
        params["min_yaw"] = min_yaw
    if max_yaw is not None:
        params["max_yaw"] = max_yaw
    return send_fusion_command("create_ball_joint", params)

@mcp.tool()
def set_joint_angle(angle: float, joint_index: int = None) -> dict:
    """Drive rotation on a revolute, cylindrical, or pin-slot joint (degrees)"""
    params = {"angle": angle}
    if joint_index is not None:
        params["joint_index"] = joint_index
    return send_fusion_command("set_joint_angle", params)

@mcp.tool()
def set_joint_distance(distance: float, joint_index: int = None) -> dict:
    """Drive translation on a slider, cylindrical, or pin-slot joint (cm)"""
    params = {"distance": distance}
    if joint_index is not None:
        params["joint_index"] = joint_index
    return send_fusion_command("set_joint_distance", params)

# =============================================================================
# BOOLEAN OPERATIONS (v7.1 - Added combine)
# =============================================================================

@mcp.tool()
def combine(target_body: int, tool_bodies: list, operation: str = "cut", keep_tools: bool = False) -> dict:
    """
    Boolean operations: cut, join, or intersect bodies.
    
    Args:
        target_body: Index of body to modify (0 = first body)
        tool_bodies: List of body indices to use as tools
        operation: "cut" (subtract), "join" (add), or "intersect"
        keep_tools: If True, keep tool bodies after operation
    
    Examples:
        combine(target_body=0, tool_bodies=[1], operation="cut")  # Cut body1 from body0
        combine(target_body=0, tool_bodies=[1,2], operation="join")  # Merge 3 bodies
    
    Use get_body_info() to verify body indices before combining.
    """
    return send_fusion_command("combine", {
        "target_body": target_body,
        "tool_bodies": tool_bodies,
        "operation": operation,
        "keep_tools": keep_tools
    })
# =============================================================================
# UTILITY OPERATIONS (v7.2 - undo, delete_body, delete_sketch)
# =============================================================================

@mcp.tool()
def undo(count: int = 1) -> dict:
    """
    Undo recent operations.
    
    Args:
        count: Number of operations to undo (default 1)
    
    Returns:
        undone_count: How many operations were actually undone
    """
    return send_fusion_command("undo", {"count": count})

@mcp.tool()
def delete_body(body_index: int = None) -> dict:
    """
    Delete a body by index.
    
    Args:
        body_index: Index of body to delete (default: most recent body)
    
    Use get_design_info() to see body count, get_body_info() for details.
    """
    params = {}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("delete_body", params)

@mcp.tool()
def delete_sketch(sketch_index: int = None) -> dict:
    """
    Delete a sketch by index.
    
    Args:
        sketch_index: Index of sketch to delete (default: most recent sketch)
    
    Use get_design_info() to see sketch count.
    """
    params = {}
    if sketch_index is not None:
        params["sketch_index"] = sketch_index
    return send_fusion_command("delete_sketch", params)
# =============================================================================
# EXPORT
# =============================================================================

@mcp.tool()
def export_stl(filepath: str) -> dict:
    """Export the design as STL file for 3D printing"""
    return send_fusion_command("export_stl", {"filepath": filepath})

@mcp.tool()
def export_step(filepath: str) -> dict:
    """Export the design as STEP file (CAD standard)"""
    return send_fusion_command("export_step", {"filepath": filepath})

@mcp.tool()
def export_3mf(filepath: str) -> dict:
    """Export the design as 3MF file (modern 3D printing format)"""
    return send_fusion_command("export_3mf", {"filepath": filepath})

# =============================================================================
# IMPORT
# =============================================================================

@mcp.tool()
def import_mesh(filepath: str, unit: str = "mm") -> dict:
    """Import STL, OBJ, or 3MF mesh file. Units: mm, cm, or in"""
    return send_fusion_command("import_mesh", {"filepath": filepath, "unit": unit})

# =============================================================================
# SKETCH CONSTRAINTS (Phase 2)
# =============================================================================

@mcp.tool()
def constrain_horizontal(curve_index: int) -> dict:
    """Constrain a sketch line to be horizontal.

    Args:
        curve_index: Index of the line to constrain. Use get_sketch_info() to see curves.
    """
    return send_fusion_command("constrain_horizontal", {"curve_index": curve_index})

@mcp.tool()
def constrain_vertical(curve_index: int) -> dict:
    """Constrain a sketch line to be vertical.

    Args:
        curve_index: Index of the line to constrain. Use get_sketch_info() to see curves.
    """
    return send_fusion_command("constrain_vertical", {"curve_index": curve_index})

@mcp.tool()
def constrain_perpendicular(curve_index: int, curve_index_2: int) -> dict:
    """Constrain two sketch lines to be perpendicular (90 degrees).

    Args:
        curve_index: First line index
        curve_index_2: Second line index
    """
    return send_fusion_command("constrain_perpendicular", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_parallel(curve_index: int, curve_index_2: int) -> dict:
    """Constrain two sketch lines to be parallel.

    Args:
        curve_index: First line index
        curve_index_2: Second line index
    """
    return send_fusion_command("constrain_parallel", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_tangent(curve_index: int, curve_index_2: int) -> dict:
    """Constrain two sketch curves to be tangent at their nearest endpoints.

    Args:
        curve_index: First curve index (line, arc, circle, or spline)
        curve_index_2: Second curve index
    """
    return send_fusion_command("constrain_tangent", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_coincident(point_index: int, curve_index: int = None, point_index_2: int = None) -> dict:
    """Constrain a sketch point to lie on a curve or coincide with another point.

    Args:
        point_index: The point to constrain
        curve_index: Target curve (point will be placed on this curve)
        point_index_2: Target point (points will coincide). Provide curve_index OR point_index_2.

    Use get_sketch_info() to see available point and curve indices.
    """
    params = {"point_index": point_index}
    if curve_index is not None:
        params["curve_index"] = curve_index
    if point_index_2 is not None:
        params["point_index_2"] = point_index_2
    return send_fusion_command("constrain_coincident", params)

@mcp.tool()
def constrain_concentric(curve_index: int, curve_index_2: int) -> dict:
    """Constrain two circles or arcs to share the same center point.

    Args:
        curve_index: First circle/arc index
        curve_index_2: Second circle/arc index
    """
    return send_fusion_command("constrain_concentric", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_equal(curve_index: int, curve_index_2: int) -> dict:
    """Constrain two sketch curves to have equal size (lines: same length, circles: same radius).

    Args:
        curve_index: First curve index
        curve_index_2: Second curve index (must be same type as first)
    """
    return send_fusion_command("constrain_equal", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_symmetric(symmetry_curve_index: int, curve_index: int = None, curve_index_2: int = None,
                         point_index: int = None, point_index_2: int = None) -> dict:
    """Constrain two entities to be symmetric about a line.

    Args:
        symmetry_curve_index: The line of symmetry
        curve_index: First curve (use with curve_index_2 for curve symmetry)
        curve_index_2: Second curve
        point_index: First point (use with point_index_2 for point symmetry)
        point_index_2: Second point

    Provide either (curve_index + curve_index_2) or (point_index + point_index_2).
    """
    params = {"symmetry_curve_index": symmetry_curve_index}
    if curve_index is not None:
        params["curve_index"] = curve_index
    if curve_index_2 is not None:
        params["curve_index_2"] = curve_index_2
    if point_index is not None:
        params["point_index"] = point_index
    if point_index_2 is not None:
        params["point_index_2"] = point_index_2
    return send_fusion_command("constrain_symmetric", params)

# =============================================================================
# SKETCH DIMENSIONS (Phase 2)
# =============================================================================

@mcp.tool()
def dimension_distance(value: float, curve_index: int = None, point_index: int = None, point_index_2: int = None) -> dict:
    """Add a distance dimension to constrain length between two points or along a curve.

    Args:
        value: The dimension value in cm (required -- dimensions drive geometry)
        curve_index: Line to dimension (uses its start/end points)
        point_index: First point (use with point_index_2 for point-to-point)
        point_index_2: Second point

    Provide either curve_index OR (point_index + point_index_2).
    """
    params = {"value": value}
    if curve_index is not None:
        params["curve_index"] = curve_index
    if point_index is not None:
        params["point_index"] = point_index
    if point_index_2 is not None:
        params["point_index_2"] = point_index_2
    return send_fusion_command("dimension_distance", params)

@mcp.tool()
def dimension_radial(curve_index: int, value: float, type: str = "diameter") -> dict:
    """Add a diameter or radius dimension to a circle or arc.

    Args:
        curve_index: Index of the circle or arc to dimension
        value: The dimension value in cm (diameter or radius depending on type)
        type: "diameter" or "radius" (default "diameter")
    """
    return send_fusion_command("dimension_radial", {
        "curve_index": curve_index, "value": value, "type": type
    })

@mcp.tool()
def dimension_angular(curve_index: int, curve_index_2: int, value: float) -> dict:
    """Add an angular dimension between two sketch lines.

    Args:
        curve_index: First line index
        curve_index_2: Second line index
        value: Angle value in degrees
    """
    return send_fusion_command("dimension_angular", {
        "curve_index": curve_index, "curve_index_2": curve_index_2, "value": value
    })

# =============================================================================
# PARAMETRIC DESIGN (Phase 5)
# =============================================================================

@mcp.tool()
def create_parameter(name: str, expression: str, unit: str = "cm", comment: str = "") -> dict:
    """Create a named user parameter with an expression. Expressions can reference other parameters.
    The parameter drives geometry when used in dimensions or features.

    Args:
        name: Parameter name (e.g., "width", "height")
        expression: Value or expression (e.g., "5", "width * 2")
        unit: Unit type -- cm, mm, in, ft, deg, rad (default "cm")
        comment: Optional description of the parameter

    Examples:
        create_parameter(name="width", expression="5", unit="cm")
        create_parameter(name="height", expression="width * 2", unit="cm")
    """
    return send_fusion_command("create_parameter", {
        "name": name, "expression": expression, "unit": unit, "comment": comment
    })

@mcp.tool()
def set_parameter(name: str, expression: str) -> dict:
    """Update an existing parameter's expression. The model regenerates automatically.
    Expressions can reference other parameters.

    Args:
        name: Parameter to update
        expression: New value or expression (e.g., "10", "width + 3")

    Examples:
        set_parameter(name="width", expression="10")
        set_parameter(name="height", expression="width + 3")
    """
    return send_fusion_command("set_parameter", {"name": name, "expression": expression})

# =============================================================================
# TIMELINE NAVIGATION (Phase 5)
# =============================================================================

@mcp.tool()
def get_timeline() -> dict:
    """Retrieve the design timeline showing all features with their status.
    Use to understand design history and find positions for rollback.

    Examples:
        get_timeline()
    """
    return send_fusion_command("get_timeline", {})

@mcp.tool()
def edit_at_timeline(position: int) -> dict:
    """Move the timeline marker to a specific position. Features after the marker are suppressed.
    Use position=-1 to return to end (all features active).

    Args:
        position: Timeline position (0=before all features, N=after Nth feature, -1=end)

    Examples:
        edit_at_timeline(position=3)
        edit_at_timeline(position=-1)
    """
    return send_fusion_command("edit_at_timeline", {"position": position})

@mcp.tool()
def create_marker(name: str) -> dict:
    """Create a named marker at the current timeline position. Markers are stored in-memory
    (not persistent across Fusion sessions). Use with undo_to_marker for named rollback points.

    Args:
        name: Marker identifier

    Examples:
        create_marker(name="before_fillets")
        create_marker(name="base_shape")
    """
    return send_fusion_command("create_marker", {"name": name})

@mcp.tool()
def undo_to_marker(name: str) -> dict:
    """Roll the timeline back to a previously created marker position. Features after the marker
    are suppressed. Use get_timeline() to see current state after rollback.

    Args:
        name: Marker to roll back to

    Examples:
        undo_to_marker(name="before_fillets")
    """
    return send_fusion_command("undo_to_marker", {"name": name})

# =============================================================================
# MCP RESOURCE ENDPOINTS (Phase 5 - Discoverability)
# =============================================================================

@mcp.resource("docs://tools/sketch")
def resource_tools_sketch() -> str:
    """Tool reference documentation for sketch operations."""
    path = RESOURCES_DIR / "tools" / "sketch.md"
    if not path.exists():
        return "Error: sketch.md resource file not found. Expected at: " + str(path)
    return path.read_text()

@mcp.resource("docs://tools/3d-features")
def resource_tools_3d_features() -> str:
    """Tool reference documentation for 3D feature operations."""
    path = RESOURCES_DIR / "tools" / "3d-features.md"
    if not path.exists():
        return "Error: 3d-features.md resource file not found. Expected at: " + str(path)
    return path.read_text()

@mcp.resource("docs://tools/assembly")
def resource_tools_assembly() -> str:
    """Tool reference documentation for assembly and joint operations."""
    path = RESOURCES_DIR / "tools" / "assembly.md"
    if not path.exists():
        return "Error: assembly.md resource file not found. Expected at: " + str(path)
    return path.read_text()

@mcp.resource("docs://tools/utility")
def resource_tools_utility() -> str:
    """Tool reference documentation for utility, query, and I/O operations."""
    path = RESOURCES_DIR / "tools" / "utility.md"
    if not path.exists():
        return "Error: utility.md resource file not found. Expected at: " + str(path)
    return path.read_text()

@mcp.resource("docs://guides/coordinates")
def resource_guides_coordinates() -> str:
    """Coordinate system guide including units, planes, and XZ inversion."""
    path = RESOURCES_DIR / "guides" / "coordinates.md"
    if not path.exists():
        return "Error: coordinates.md resource file not found. Expected at: " + str(path)
    return path.read_text()

@mcp.resource("docs://guides/workflows")
def resource_guides_workflows() -> str:
    """Workflow patterns guide with step-by-step CAD patterns and reasoning."""
    path = RESOURCES_DIR / "guides" / "workflows.md"
    if not path.exists():
        return "Error: workflows.md resource file not found. Expected at: " + str(path)
    return path.read_text()

# =============================================================================
# MCP PROMPT TEMPLATES (Phase 5 - Discoverability)
# =============================================================================

@mcp.prompt()
def box_enclosure(width: str = "10", depth: str = "8", height: str = "5",
                  wall_thickness: str = "0.2", fillet_radius: str = "0.3") -> str:
    """Generate a step-by-step guide for creating a box enclosure with rounded edges."""
    return f"""Create a box enclosure with these dimensions:
- Width: {width} cm, Depth: {depth} cm, Height: {height} cm
- Wall thickness: {wall_thickness} cm, Fillet radius: {fillet_radius} cm

Step-by-step workflow:

1. **Create the base sketch**
   create_sketch(plane="XY")

2. **Draw the rectangle**
   draw_rectangle(x1=-{width}/2, y1=-{depth}/2, x2={width}/2, y2={depth}/2)
   finish_sketch()

3. **Extrude to full height**
   extrude(distance={height})

4. **Shell the body (remove top face)**
   shell(thickness={wall_thickness}, faces_to_remove=[0])
   REASONING: Shell BEFORE fillet because filleting changes edge topology.
   If you fillet first, the face indices for shell will be wrong.

5. **Fillet the outer edges**
   fillet(radius={fillet_radius})
   REASONING: Apply fillet last so shell face removal works on the original box geometry.

Key tool sequence: create_sketch -> draw_rectangle -> finish_sketch -> extrude -> shell -> fillet
The ordering matters: shell before fillet preserves correct face indices."""

@mcp.prompt()
def cylinder(radius: str = "2.5", height: str = "5",
             hollow: str = "false", wall_thickness: str = "0.2") -> str:
    """Generate a step-by-step guide for creating a solid or hollow cylinder."""
    hollow_step = ""
    if hollow.lower() == "true":
        hollow_step = f"""
5. **Shell to make hollow**
   shell(thickness={wall_thickness}, faces_to_remove=[0])
   This removes the top face and hollows the cylinder with {wall_thickness} cm walls.
"""
    return f"""Create a {"hollow " if hollow.lower() == "true" else ""}cylinder:
- Radius: {radius} cm, Height: {height} cm
{"- Wall thickness: " + wall_thickness + " cm" if hollow.lower() == "true" else ""}

Step-by-step workflow:

1. **Create the base sketch**
   create_sketch(plane="XY")

2. **Draw the circle**
   draw_circle(center_x=0, center_y=0, radius={radius})

3. **Finish the sketch**
   finish_sketch()

4. **Extrude to height**
   extrude(distance={height})
{hollow_step}
Key tool sequence: create_sketch -> draw_circle -> finish_sketch -> extrude{" -> shell" if hollow.lower() == "true" else ""}"""

@mcp.prompt()
def spur_gear(module: str = "1", teeth: str = "20",
              thickness: str = "5", bore_diameter: str = "3") -> str:
    """Generate a step-by-step guide for creating an approximated spur gear."""
    return f"""Create an approximated spur gear:
- Module: {module}, Teeth: {teeth}, Thickness: {thickness} cm, Bore diameter: {bore_diameter} cm
- Pitch diameter = module * teeth = {module} * {teeth} cm
- Outer diameter = (teeth + 2) * module

REASONING: True involute tooth profiles require complex math. This approach uses
a simplified polygon approximation that works for prototyping and visual models.
For production gears, use dedicated gear generation software.

Step-by-step workflow:

1. **Create a user parameter for the gear**
   create_parameter(name="gear_module", expression="{module}", unit="cm")
   create_parameter(name="gear_teeth", expression="{teeth}")
   create_parameter(name="pitch_radius", expression="gear_module * gear_teeth / 2", unit="cm")

2. **Create the base sketch for the gear blank**
   create_sketch(plane="XY")

3. **Draw the outer circle (addendum circle)**
   draw_circle(center_x=0, center_y=0, radius=({module} * ({teeth} + 2)) / 2)

4. **Finish the sketch and extrude**
   finish_sketch()
   extrude(distance={thickness})

5. **Create the tooth profile sketch**
   create_sketch(plane="XY")
   REASONING: Sketch on the same plane to create a cutting profile for one tooth gap.

6. **Draw a simplified tooth gap (wedge shape)**
   Use draw_line() to create a V-shaped notch at the pitch circle radius.
   The gap angle per tooth = 360 / {teeth} degrees, gap is roughly half that.

7. **Pattern the tooth cuts circularly**
   finish_sketch()
   extrude(distance={thickness})  -- as a cut through the blank
   pattern_circular(count={teeth}, angle=360, axis="Z")

8. **Create the bore hole**
   create_sketch(plane="XY")
   draw_circle(center_x=0, center_y=0, radius={bore_diameter}/2)
   finish_sketch()
   extrude(distance={thickness})
   combine(target_body=0, tool_bodies=[1], operation="cut")

Key tool sequence: create_parameter -> create_sketch -> draw_circle -> extrude (blank) ->
  create_sketch -> draw tooth profile -> extrude (cut) -> pattern_circular -> bore hole"""

@mcp.prompt()
def simple_hinge(pin_diameter: str = "0.5", plate_width: str = "4",
                 plate_height: str = "3", plate_thickness: str = "0.3") -> str:
    """Generate a step-by-step guide for creating a simple two-plate hinge with a revolute joint."""
    return f"""Create a simple two-plate hinge:
- Pin diameter: {pin_diameter} cm, Plate: {plate_width} x {plate_height} x {plate_thickness} cm

REASONING: A hinge requires two separate components connected by a revolute joint.
The joint axis must align with the pin axis for correct rotation behavior.
Create each plate as its own component before adding the joint.

Step-by-step workflow:

1. **Create plate 1 (left plate)**
   create_sketch(plane="XY")
   draw_rectangle(x1=-{plate_width}/2, y1=0, x2=0, y2={plate_height})
   finish_sketch()
   extrude(distance={plate_thickness})
   create_component(name="hinge_plate_1")

2. **Create knuckle cylinder on plate 1**
   create_sketch(plane="XZ")
   draw_circle(center_x=0, center_y={plate_thickness}/2, radius={pin_diameter})
   finish_sketch()
   extrude(distance={plate_height} * 0.4)
   combine(target_body=0, tool_bodies=[1], operation="join")
   REASONING: The knuckle must be part of the plate component for joint to work correctly.

3. **Create plate 2 (right plate)**
   create_sketch(plane="XY")
   draw_rectangle(x1=0, y1=0, x2={plate_width}/2, y2={plate_height})
   finish_sketch()
   extrude(distance={plate_thickness})
   create_component(name="hinge_plate_2")

4. **Create knuckle cylinder on plate 2**
   create_sketch(plane="XZ")
   draw_circle(center_x=0, center_y={plate_thickness}/2, radius={pin_diameter})
   finish_sketch()
   extrude(distance={plate_height} * 0.4)
   move_component(y={plate_height} * 0.5, index=1)
   REASONING: Offset the second knuckle so the two interleave along the hinge axis.

5. **Create revolute joint between plates**
   create_revolute_joint(component1_index=0, component2_index=1,
                          x=0, y=0, z=0,
                          axis_x=0, axis_y=1, axis_z=0)
   REASONING: Joint axis is Y (vertical along hinge pin). This allows the plates
   to rotate open/closed around the pin axis.

6. **Test the joint**
   set_joint_angle(angle=45)
   REASONING: Verify the hinge opens to 45 degrees correctly.

Key tool sequence: create_sketch -> draw_rectangle -> extrude -> create_component (x2) ->
  create_revolute_joint -> set_joint_angle"""

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    mcp.run()
