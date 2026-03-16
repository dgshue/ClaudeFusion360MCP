#!/usr/bin/env python3
"""
Fusion 360 MCP Server v0.5.0
==============================
79 tools for comprehensive Fusion 360 Design API coverage via MCP.

Tool Categories:
  - Sketch: create, draw, constraints, dimensions, queries, ops
  - 3D Features: extrude, revolve, sweep, loft, shell, draft
  - Threads & Holes: thread (cosmetic/modeled), query_threads, hole
  - Modifications: fillet, chamfer, combine, split_body
  - Patterns: rectangular, circular, mirror
  - Construction: point, plane, axis
  - Components: create, move, rotate, list, delete, interference
  - Joints: rigid, revolute, slider, cylindrical, pin-slot, ball
  - Parametric: set/get parameters, edit_at_timeline
  - Export/Import: STL (high refinement), STEP, 3MF, mesh import
  - Inspection: design info, body info, measure, fit view
  - Utility: undo, delete body/sketch, batch operations
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
import os
import sys
import atexit
from pathlib import Path

COMM_DIR = Path.home() / "fusion_mcp_comm"
COMM_DIR.mkdir(exist_ok=True)

RESOURCES_DIR = Path(__file__).parent / "resources"

PID_FILE = COMM_DIR / "mcp_server.pid"


def _is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running. Cross-platform."""
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True  # Exists but owned by different user (Windows)
    except OSError:
        return False


def _check_and_write_pid():
    """Prevent duplicate MCP server processes via PID lock file."""
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if _is_process_running(old_pid):
                print(f"ERROR: MCP server already running (PID {old_pid}). "
                      f"Kill it first or delete {PID_FILE}", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"Removing stale PID file (PID {old_pid} not running)", file=sys.stderr)
        except (ValueError, IOError):
            print("Removing corrupted PID file", file=sys.stderr)

    PID_FILE.write_text(str(os.getpid()))
    atexit.register(_cleanup_pid)


def _cleanup_pid():
    """Remove PID file on clean exit."""
    try:
        if PID_FILE.exists():
            stored_pid = int(PID_FILE.read_text().strip())
            if stored_pid == os.getpid():
                PID_FILE.unlink()
    except Exception:
        pass


_check_and_write_pid()

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
            result = None
            # Defensive JSON parsing - handle empty/partial response files
            for attempt in range(2):
                try:
                    raw = resp_file.read_text()
                    if not raw.strip():
                        if attempt == 0:
                            time.sleep(0.1)  # Wait for write completion
                            continue
                        raise Exception(
                            f"Empty response file for {tool_name}. "
                            "This may indicate the add-in crashed during processing."
                        )
                    result = json.loads(raw)
                    break
                except json.JSONDecodeError as e:
                    if attempt == 0:
                        time.sleep(0.1)  # Retry once - file may still be writing
                        continue
                    raise Exception(
                        f"Invalid JSON response for {tool_name}: {e}. "
                        f"Response length: {len(raw)} chars. "
                        "This may indicate a corrupted response from the add-in."
                    )

            # Clean up files
            try:
                cmd_file.unlink()
                resp_file.unlink()
            except Exception:
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
    Execute multiple Fusion commands in a single round-trip for 5-10x faster complex operations.

    Sends all commands to Fusion 360 at once instead of individual calls.
    Stops on first error and returns partial results for commands that succeeded.

    Args:
        commands: List of command dicts, each with "name" (tool name) and "params" (tool parameters).

    Examples:
        batch(commands=[{"name": "create_sketch", "params": {"plane": "XY"}},
                        {"name": "draw_rectangle", "params": {"x1": -5, "y1": -5, "x2": 5, "y2": 5}},
                        {"name": "finish_sketch", "params": {}},
                        {"name": "extrude", "params": {"distance": 3}}])
        batch(commands=[{"name": "fillet", "params": {"radius": 0.2, "edges": [0, 1]}},
                        {"name": "chamfer", "params": {"distance": 0.1, "edges": [4, 5]}}])
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
    """
    Exit sketch editing mode and make the sketch available for 3D operations.

    Must be called after completing all sketch geometry (lines, circles, etc.)
    before using extrude, revolve, or other features. Only one sketch can be
    active at a time.

    Examples:
        finish_sketch()
    """
    return send_fusion_command("finish_sketch", {})

# =============================================================================
# SKETCH GEOMETRY
# =============================================================================

@mcp.tool()
def draw_rectangle(x1: float, y1: float, x2: float, y2: float) -> dict:
    """
    Draw a rectangle in the active sketch defined by two opposite corners.

    Creates four line segments forming a closed rectangle profile ready for extrusion.

    Args:
        x1: First corner X coordinate (cm).
        y1: First corner Y coordinate (cm).
        x2: Opposite corner X coordinate (cm).
        y2: Opposite corner Y coordinate (cm).

    Examples:
        draw_rectangle(x1=-5, y1=-5, x2=5, y2=5)       # 10x10 cm centered
        draw_rectangle(x1=0, y1=0, x2=3, y2=2)          # 3x2 cm at origin corner
    """
    return send_fusion_command("draw_rectangle", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})

@mcp.tool()
def draw_circle(center_x: float, center_y: float, radius: float) -> dict:
    """
    Draw a circle in the active sketch. Creates a closed profile for extrusion or revolution.

    Args:
        center_x: Center X coordinate (cm).
        center_y: Center Y coordinate (cm).
        radius: Circle radius (cm).

    Examples:
        draw_circle(center_x=0, center_y=0, radius=2.5)    # Centered circle
        draw_circle(center_x=3, center_y=3, radius=0.5)    # Small circle offset
    """
    return send_fusion_command("draw_circle", {"center_x": center_x, "center_y": center_y, "radius": radius})

@mcp.tool()
def draw_line(x1: float, y1: float, x2: float, y2: float) -> dict:
    """
    Draw a straight line segment in the active sketch between two points.

    Lines can form profiles when connected end-to-end. Use constraints to
    lock orientation (horizontal, vertical, perpendicular).

    Args:
        x1: Start point X coordinate (cm).
        y1: Start point Y coordinate (cm).
        x2: End point X coordinate (cm).
        y2: End point Y coordinate (cm).

    Examples:
        draw_line(x1=0, y1=0, x2=5, y2=0)      # Horizontal line
        draw_line(x1=0, y1=0, x2=0, y2=5)      # Vertical line
        draw_line(x1=0, y1=0, x2=3, y2=4)      # Diagonal line
    """
    return send_fusion_command("draw_line", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})

@mcp.tool()
def draw_arc(center_x: float, center_y: float, start_x: float, start_y: float, end_x: float, end_y: float) -> dict:
    """
    Draw an arc in the active sketch defined by center, start, and end points.

    The arc sweeps counter-clockwise from start to end around the center point.
    Useful for rounded features, cam profiles, and curved transitions.

    Args:
        center_x: Arc center X coordinate (cm).
        center_y: Arc center Y coordinate (cm).
        start_x: Arc start point X coordinate (cm).
        start_y: Arc start point Y coordinate (cm).
        end_x: Arc end point X coordinate (cm).
        end_y: Arc end point Y coordinate (cm).

    Examples:
        draw_arc(center_x=0, center_y=0, start_x=2, start_y=0, end_x=0, end_y=2)    # Quarter arc
        draw_arc(center_x=5, center_y=0, start_x=5, start_y=3, end_x=5, end_y=-3)   # Half arc
    """
    return send_fusion_command("draw_arc", {
        "center_x": center_x, "center_y": center_y,
        "start_x": start_x, "start_y": start_y,
        "end_x": end_x, "end_y": end_y
    })

@mcp.tool()
def draw_polygon(center_x: float, center_y: float, radius: float, sides: int = 6) -> dict:
    """
    Draw a regular polygon in the active sketch. Default is a hexagon.

    Creates a closed profile with equal-length sides inscribed in a circle of given radius.

    Args:
        center_x: Polygon center X coordinate (cm).
        center_y: Polygon center Y coordinate (cm).
        radius: Circumscribed circle radius (cm) -- distance from center to vertex.
        sides: Number of sides (default 6 for hexagon). Minimum 3.

    Examples:
        draw_polygon(center_x=0, center_y=0, radius=3, sides=6)    # Hexagon
        draw_polygon(center_x=0, center_y=0, radius=2, sides=8)    # Octagon
        draw_polygon(center_x=0, center_y=0, radius=5, sides=3)    # Triangle
    """
    return send_fusion_command("draw_polygon", {
        "center_x": center_x, "center_y": center_y, 
        "radius": radius, "sides": sides
    })

# =============================================================================
# SKETCH ENTITY TOOLS
# =============================================================================

@mcp.tool()
def set_construction(curve_index: int, is_construction: bool = True) -> dict:
    """
    Toggle a sketch curve between regular and construction geometry.

    Construction geometry serves as reference lines and circles but is not included
    in profiles for extrusion. Useful for centerlines, layout guides, and symmetry axes.

    Args:
        curve_index: Index of the curve to toggle. Use get_sketch_info() to see available curves.
        is_construction: True to make construction, False to make regular. Default True.

    Examples:
        set_construction(curve_index=0)                         # Make curve 0 construction
        set_construction(curve_index=2, is_construction=False)  # Revert to regular
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
    """
    Draw a fitted spline through a collection of points in the active sketch.

    Creates a smooth curve passing through all specified points. Useful for organic
    shapes, airfoil profiles, and ergonomic contours.

    Args:
        points: List of [x, y] coordinate pairs (minimum 2 points). Units: cm.

    Examples:
        draw_spline(points=[[0,0], [2,3], [5,1], [8,4]])          # 4-point curve
        draw_spline(points=[[0,0], [5,2], [10,0]])                # Simple arc-like
    """
    return send_fusion_command("draw_spline", {"points": points})

@mcp.tool()
def draw_ellipse(center_x: float, center_y: float, major_radius: float, minor_radius: float, angle: float = 0) -> dict:
    """
    Draw an ellipse in the active sketch defined by center, radii, and rotation.

    Creates an oval profile for extrusion. The major axis is the longer radius.

    Args:
        center_x: Center X coordinate (cm).
        center_y: Center Y coordinate (cm).
        major_radius: Semi-major axis length (cm) -- the longer radius.
        minor_radius: Semi-minor axis length (cm) -- the shorter radius.
        angle: Rotation angle of major axis in degrees (default 0).

    Examples:
        draw_ellipse(center_x=0, center_y=0, major_radius=5, minor_radius=3)
        draw_ellipse(center_x=0, center_y=0, major_radius=4, minor_radius=2, angle=45)
    """
    return send_fusion_command("draw_ellipse", {
        "center_x": center_x, "center_y": center_y,
        "major_radius": major_radius, "minor_radius": minor_radius,
        "angle": angle
    })

@mcp.tool()
def draw_slot(center_x: float, center_y: float, end_x: float, end_y: float, width: float) -> dict:
    """
    Draw a center-point slot in the active sketch.

    A slot is a rounded rectangle (stadium shape) defined by its center, one end point,
    and width. Commonly used for mounting holes and adjustable fastener positions.

    Args:
        center_x: Slot center X coordinate (cm).
        center_y: Slot center Y coordinate (cm).
        end_x: End point X (cm) -- defines slot length and direction from center.
        end_y: End point Y (cm).
        width: Slot width perpendicular to length direction (cm).

    Examples:
        draw_slot(center_x=0, center_y=0, end_x=3, end_y=0, width=1)    # Horizontal slot
        draw_slot(center_x=0, center_y=0, end_x=0, end_y=2, width=0.5)  # Vertical slot
    """
    return send_fusion_command("draw_slot", {
        "center_x": center_x, "center_y": center_y,
        "end_x": end_x, "end_y": end_y, "width": width
    })

@mcp.tool()
def draw_point(x: float, y: float) -> dict:
    """
    Add a reference or construction point to the active sketch.

    Points serve as reference locations for constraints, dimensions, and hole positioning.
    They do not create profiles for extrusion.

    Args:
        x: Point X coordinate (cm).
        y: Point Y coordinate (cm).

    Examples:
        draw_point(x=0, y=0)           # Point at origin
        draw_point(x=3, y=4)           # Offset point
    """
    return send_fusion_command("draw_point", {"x": x, "y": y})

@mcp.tool()
def draw_text(text: str, height: float, x: float = 0, y: float = 0, font: str = None) -> dict:
    """
    Draw text in the active sketch. Text profiles can be extruded for embossing or engraving.

    Creates sketch text that generates closed profiles suitable for extrusion.
    Use positive extrude for raised text (emboss) or negative/cut for engraved text.

    Args:
        text: The text string to draw.
        height: Text height (cm).
        x: Text position X coordinate (cm). Default 0.
        y: Text position Y coordinate (cm). Default 0.
        font: Font name (optional, uses system default if omitted).

    Examples:
        draw_text(text="HELLO", height=1.0)                          # Default position
        draw_text(text="V1.0", height=0.5, x=2, y=1, font="Arial")  # Positioned with font
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
    """
    Create offset curves parallel to existing sketch geometry at a uniform distance.

    Offsets a curve (and connected curves) to create parallel geometry. Useful for
    creating wall outlines, clearance paths, and concentric shapes.

    Args:
        curve_index: Index of a curve to offset (connected curves are included automatically).
        distance: Offset distance (cm).
        direction_x: X component of offset direction (default 0).
        direction_y: Y component of offset direction (default 1).

    Examples:
        offset_curves(curve_index=0, distance=0.5)                          # Offset outward
        offset_curves(curve_index=0, distance=0.3, direction_x=1, direction_y=0)  # Offset right
    """
    return send_fusion_command("offset_curves", {
        "curve_index": curve_index, "distance": distance,
        "direction_x": direction_x, "direction_y": direction_y
    })

@mcp.tool()
def project_geometry(body_index: int = 0, edge_index: int = None, face_index: int = None) -> dict:
    """
    Project body edges or faces onto the active sketch plane.

    Creates sketch curves from 3D body geometry. Useful for creating profiles that
    reference existing features, or for sketching relative to body edges.

    Args:
        body_index: Which body to project from (default 0).
        edge_index: Specific edge index to project (optional).
        face_index: Specific face index to project (optional).

    Examples:
        project_geometry()                                   # Project all edges of body 0
        project_geometry(body_index=0, edge_index=3)         # Project specific edge
        project_geometry(body_index=1, face_index=0)         # Project a face outline
    """
    params = {"body_index": body_index}
    if edge_index is not None:
        params["edge_index"] = edge_index
    if face_index is not None:
        params["face_index"] = face_index
    return send_fusion_command("project_geometry", params)

@mcp.tool()
def import_svg(file_path: str, x: float = 0, y: float = 0, scale: float = 1.0) -> dict:
    """
    Import an SVG file into the active sketch using Fusion 360's native SVG import.

    Converts SVG vector paths into sketch curves. Useful for importing logos,
    custom profiles, and complex 2D shapes for extrusion.

    Args:
        file_path: Full absolute path to the SVG file on disk.
        x: X position for import origin (cm). Default 0.
        y: Y position for import origin (cm). Default 0.
        scale: Scale factor (default 1.0 = native SVG dimensions).

    Examples:
        import_svg(file_path="C:/designs/logo.svg")
        import_svg(file_path="C:/designs/profile.svg", x=2, y=3, scale=0.5)
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

    Construction planes provide additional sketch surfaces beyond the three default
    planes. Use offset mode for parallel planes, angle mode for tilted surfaces.

    Args:
        mode: Creation mode -- "offset" (parallel to base plane) or "angle" (rotated around axis).
        plane: Base plane -- "XY", "XZ", or "YZ" (default "XY").
        offset: Distance from base plane (cm). Used in offset mode. Default 1.0.
        axis: Rotation axis for angle mode -- "X", "Y", or "Z" (default "X").
        angle: Rotation angle (degrees). Used in angle mode. Default 45.0.

    Examples:
        construction_plane(mode="offset", plane="XY", offset=5)        # 5cm above XY
        construction_plane(mode="angle", plane="XY", axis="X", angle=30)  # Tilted 30 deg
    """
    params = {"mode": mode, "plane": plane, "offset": offset, "axis": axis, "angle": angle}
    return send_fusion_command("construction_plane", params)

@mcp.tool()
def construction_axis(mode: str = "two_points", point1_x: float = 0, point1_y: float = 0, point1_z: float = 0, point2_x: float = 0, point2_y: float = 0, point2_z: float = 1.0) -> dict:
    """
    Create a construction (reference) axis for patterns, revolves, or other operations.

    Defines a line in 3D space from two points. Use for custom rotation axes in
    circular patterns, revolve operations, or as reference geometry.

    Args:
        mode: Creation mode -- "two_points" (default).
        point1_x: First point X coordinate (cm). Default 0.
        point1_y: First point Y coordinate (cm). Default 0.
        point1_z: First point Z coordinate (cm). Default 0.
        point2_x: Second point X coordinate (cm). Default 0.
        point2_y: Second point Y coordinate (cm). Default 0.
        point2_z: Second point Z coordinate (cm). Default 1.0.

    Examples:
        construction_axis()                                              # Default Z-axis
        construction_axis(point1_x=0, point1_y=0, point1_z=0, point2_x=1, point2_y=1, point2_z=0)  # Diagonal axis
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
    Create a construction (reference) point in 3D space.

    Construction points serve as positioning references for holes, patterns,
    and other features that need a specific location in the design.

    Args:
        x: X coordinate (cm). Default 0.
        y: Y coordinate (cm). Default 0.
        z: Z coordinate (cm). Default 0.

    Examples:
        construction_point(x=5, y=0, z=0)           # Point on X axis
        construction_point(x=2, y=3, z=4)           # Arbitrary 3D point
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
        diameter: Hole diameter (cm).
        depth: Hole depth (cm). Omit for through-all.
        hole_type: "simple", "counterbore", or "countersink" (default "simple").
        x: X position on face (cm). Default 0.
        y: Y position on face (cm). Default 0.
        face: Face index for hole placement (default: top face). Use get_body_info() to find.
        body_index: Which body (default: most recent).
        counterbore_diameter: Counterbore diameter (cm). Required for counterbore type.
        counterbore_depth: Counterbore depth (cm). Required for counterbore type.
        countersink_diameter: Countersink diameter (cm). Required for countersink type.
        countersink_angle: Countersink angle (degrees). Default 82.

    Examples:
        hole(diameter=0.5, depth=1.0)                                         # Simple 5mm hole
        hole(diameter=0.3)                                                    # Through-all hole
        hole(diameter=0.5, depth=1.0, hole_type="counterbore", counterbore_diameter=0.8, counterbore_depth=0.3)
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
        face: Face index of the cylindrical face to thread. Use get_body_info() to find.
        body_index: Which body (default: most recent).
        thread_type: Thread standard (default "ISO Metric profile").
        designation: Thread size designation (default "M6x1.0").
        thread_class: Thread tolerance class (default "6g" external, "6H" internal).
        is_internal: True for internal threads (holes), False for external. Default False.
        full_length: Thread the full length of the face. Default True.
        length: Thread length (cm). Used when full_length is False.

    Examples:
        thread(face=2)                                                    # M6 external thread
        thread(face=0, designation="M3x0.5", is_internal=True, thread_class="6H")  # Internal M3
        thread(face=1, full_length=False, length=1.0)                    # Partial thread
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
    Extrude the most recent sketch profile into a 3D solid body.

    Positive distance extrudes upward (along plane normal), negative downward.
    Use taper_angle for tapered extrusions (draft). Use profile_index when a
    sketch contains multiple closed regions.

    Args:
        distance: Extrusion distance (cm). Positive = normal direction, negative = opposite.
        profile_index: Which profile if sketch has multiple closed regions (default 0).
        taper_angle: Draft angle during extrusion (degrees). Default 0.

    Examples:
        extrude(distance=3)                                    # Simple 3cm extrude
        extrude(distance=-2, profile_index=1)                  # Downward, second profile
        extrude(distance=5, taper_angle=3)                     # Tapered extrude
    """
    return send_fusion_command("extrude", {
        "distance": distance, 
        "profile_index": profile_index, 
        "taper_angle": taper_angle
    })

@mcp.tool()
def revolve(angle: float, axis: str = "Y") -> dict:
    """
    Revolve the most recent sketch profile around an axis to create rotational solids.

    Creates bodies like cylinders, cones, donuts, and bowls. The sketch profile
    must be on one side of the axis (no crossing). Use 360 for full revolution.

    Args:
        angle: Revolve angle (degrees). 360 for full revolution.
        axis: Revolve axis -- "X", "Y", or "Z" (default "Y").

    Examples:
        revolve(angle=360)                         # Full revolution around Y
        revolve(angle=180, axis="X")               # Half revolution around X
        revolve(angle=90, axis="Z")                # Quarter turn around Z
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
        profile_sketch_index: Sketch containing the profile (default: second-to-last sketch).
        profile_index: Which profile in the sketch (default 0).
        path_sketch_index: Sketch containing the path curve (default: last sketch).
        path_curve_index: Which curve to use as path (default 0).
        taper_angle: Taper angle (degrees) during sweep. Default 0.
        twist_angle: Twist angle (degrees) along sweep. Default 0.
        operation: "new", "join", "cut", or "intersect" (default "new").

    Examples:
        sweep()                                                    # Default: profile in second-to-last sketch, path in last
        sweep(profile_sketch_index=0, path_sketch_index=1)         # Explicit sketch indices
        sweep(twist_angle=90, operation="join")                    # Twisted sweep, joined to existing body
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
        sketch_indices: List of sketch indices containing profiles (minimum 2, order matters).
        profile_indices: List of profile indices per sketch (default [0, 0, ...]).
        is_solid: Create solid body (True) or surface (False). Default True.
        is_closed: Close the loft (connect last section to first). Default False.
        operation: "new", "join", "cut", or "intersect" (default "new").

    Examples:
        loft(sketch_indices=[0, 1])                            # Loft between two sketches
        loft(sketch_indices=[0, 1, 2], is_closed=True)         # Closed 3-section loft
        loft(sketch_indices=[0, 1], is_solid=False)            # Surface loft
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
    Add fillets (rounded edges) to a body. Use to smooth sharp edges.

    Fillets improve appearance, reduce stress concentrations, and are required
    for many manufacturing processes.

    Args:
        radius: Fillet radius (cm).
        edges: List of edge indices to fillet. If None, fillets all edges.
        body_index: Which body (default: most recent).

    Examples:
        fillet(radius=0.2)                                  # Fillet all edges
        fillet(radius=0.5, edges=[0, 1, 2])                 # Fillet specific edges
        fillet(radius=0.1, body_index=0)                    # Fillet body 0
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
    Add chamfers (angled cuts) to edges of a body.

    Chamfers create flat beveled edges, often used for lead-in on holes,
    deburring, and decorative styling.

    Args:
        distance: Chamfer distance (cm) -- the setback from the edge.
        edges: List of edge indices to chamfer. If None, chamfers all edges.
        body_index: Which body (default: most recent).

    Examples:
        chamfer(distance=0.1)                                # Chamfer all edges
        chamfer(distance=0.3, edges=[4, 5])                  # Chamfer specific edges
        chamfer(distance=0.2, body_index=1)                  # Chamfer body 1
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
    Apply draft angles to faces for injection molding release.

    Adds a slight taper to faces so parts can be pulled from molds cleanly.
    Guideline: 1 degree per inch of depth. Typical range: 0.5-3 degrees.

    Args:
        angle: Draft angle (degrees). Typically 0.5-3 degrees.
        faces: List of face indices to draft. If None, drafts all eligible faces.
        body_index: Which body (default: most recent).
        pull_x: Pull direction X component. Default 0.
        pull_y: Pull direction Y component. Default 0.
        pull_z: Pull direction Z component. Default 1 (+Z).

    Examples:
        draft(angle=1.5)                                    # Draft all faces at 1.5 deg
        draft(angle=2, faces=[1, 3])                        # Draft specific faces
        draft(angle=1, pull_x=0, pull_y=0, pull_z=-1)      # Pull direction: -Z
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
    Create a mirrored copy of a body across a plane.

    Produces a symmetric duplicate on the opposite side of the mirror plane.
    Useful for creating symmetric designs by modeling half and mirroring.

    Args:
        plane: Mirror plane -- "XY", "XZ", or "YZ" (default "YZ" for left-right symmetry).
        body_index: Which body to mirror (default: most recent).

    Examples:
        mirror(plane="YZ")                         # Left-right mirror
        mirror(plane="XZ")                         # Front-back mirror
        mirror(plane="XY", body_index=0)           # Top-bottom mirror of body 0
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
    """
    Fit the viewport to show all geometry in the current design.

    Adjusts the camera to frame all visible bodies and sketches. Useful after
    creating or positioning geometry to see the full result.

    Examples:
        fit_view()
    """
    return send_fusion_command("fit_view", {})

@mcp.tool()
def get_design_info() -> dict:
    """
    Get overview information about the current Fusion 360 design.

    Returns the design name, body count, sketch count, component count, and
    whether a sketch is currently active. Use as a starting point to understand
    the design state before performing operations.

    Examples:
        get_design_info()
    """
    return send_fusion_command("get_design_info", {})

# =============================================================================
# NEW: MEASUREMENT & INSPECTION
# =============================================================================

@mcp.tool()
def get_body_info(body_index: int = None) -> dict:
    """
    Get detailed information about a body including all edges, faces, and semantic labels.

    Returns edge indices with lengths, face indices with areas and semantic labels
    (e.g., "top_face", "bottom_face"). Essential for finding indices before applying
    fillet, chamfer, shell, draft, hole, or thread operations.

    Args:
        body_index: Which body to inspect (default: most recent).

    Examples:
        get_body_info()                    # Inspect most recent body
        get_body_info(body_index=0)        # Inspect first body
    """
    params = {}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("get_body_info", params)

@mcp.tool()
def get_sketch_info() -> dict:
    """
    Get detailed information about the active sketch including all curves, points, constraints, and dimensions.

    Returns curves with semantic labels (e.g., "Curve 0 (line, horizontal, 5cm)"),
    points with coordinates, geometric constraints, parametric dimensions, and
    overall constraint status. Essential for finding indices before applying
    constraints, dimensions, or other sketch operations.

    Args:
        (none)

    Examples:
        get_sketch_info()     # Inspect active sketch entities and constraint status
    """
    return send_fusion_command("get_sketch_info", {})

@mcp.tool()
def measure(type: str = "body", body_index: int = None,
            edge_index: int = None, face_index: int = None) -> dict:
    """
    Measure dimensions of bodies, edges, or faces for verification and inspection.

    Returns physical measurements: volume and surface area for bodies, length for
    edges, area for faces. Use to verify design dimensions match intent.

    Args:
        type: What to measure -- "body", "edge", or "face".
        body_index: Which body (default: most recent).
        edge_index: Edge index (required for type="edge"). Use get_body_info() to find.
        face_index: Face index (required for type="face"). Use get_body_info() to find.

    Examples:
        measure(type="body")                                # Measure body volume/area
        measure(type="edge", edge_index=0)                  # Measure edge length
        measure(type="face", face_index=2, body_index=0)    # Measure face area
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
    """
    Convert the most recent body into a new component for assembly.

    Components are required for joints and assembly operations. Each component
    can be independently positioned and connected via joints.

    Args:
        name: Component name (optional). Auto-generated if omitted.

    Examples:
        create_component(name="bracket")         # Named component
        create_component()                       # Auto-named component
    """
    params = {}
    if name:
        params["name"] = name
    return send_fusion_command("create_component", params)

@mcp.tool()
def list_components() -> dict:
    """
    List all components in the design with names, positions, and bounding boxes.

    Returns component indices needed for move_component, rotate_component, and
    joint creation. Shows current position and size of each component.

    Examples:
        list_components()
    """
    return send_fusion_command("list_components", {})

@mcp.tool()
def delete_component(name: str = None, index: int = None) -> dict:
    """
    Delete a component from the design by name or index.

    Removes the component and its associated bodies from the design.
    Provide either name or index, not both.

    Args:
        name: Component name to delete (optional).
        index: Component index to delete (optional). Use list_components() to find.

    Examples:
        delete_component(name="bracket")         # Delete by name
        delete_component(index=1)                # Delete by index
    """
    params = {}
    if name:
        params["name"] = name
    if index is not None:
        params["index"] = index
    return send_fusion_command("delete_component", params)

@mcp.tool()
def check_interference() -> dict:
    """
    Check if any components overlap using bounding box collision detection.

    Scans all component pairs and reports any that have overlapping bounding boxes.
    Useful after positioning components to verify no unintended intersections.

    Examples:
        check_interference()
    """
    return send_fusion_command("check_interference", {})

# =============================================================================
# NEW: COMPONENT POSITIONING (CRITICAL)
# =============================================================================

@mcp.tool()
def move_component(x: float = 0, y: float = 0, z: float = 0,
                   index: int = None, name: str = None, 
                   absolute: bool = True) -> dict:
    """
    Move a component to a new position or by an offset.

    CRITICAL: Use this to position components after creation to avoid overlaps.
    In absolute mode, sets the component's world position. In relative mode,
    adds the offset to the current position.

    Args:
        x: X target position or offset (cm). Default 0.
        y: Y target position or offset (cm). Default 0.
        z: Z target position or offset (cm). Default 0.
        index: Component index (from list_components). Optional.
        name: Component name (alternative to index). Optional.
        absolute: If True, set absolute position. If False, move by offset. Default True.

    Examples:
        move_component(x=0, y=10, z=0, index=1)                    # Move to Y=10
        move_component(x=5, y=0, z=0, index=0, absolute=False)     # Move 5cm in X
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
    Rotate a component around an axis at a specified origin point.

    Rotates the component in-place around the given axis. Use origin parameters
    to set the pivot point for rotation.

    Args:
        angle: Rotation angle (degrees).
        axis: Rotation axis -- "X", "Y", or "Z" (default "Z").
        index: Component index (from list_components). Optional.
        name: Component name (alternative to index). Optional.
        origin_x: Rotation origin X coordinate (cm). Default 0.
        origin_y: Rotation origin Y coordinate (cm). Default 0.
        origin_z: Rotation origin Z coordinate (cm). Default 0.

    Examples:
        rotate_component(angle=90, axis="Z", index=0)                     # Rotate 90 deg around Z
        rotate_component(angle=45, axis="Y", name="bracket")              # Rotate by name
        rotate_component(angle=180, axis="X", index=1, origin_x=5)       # Rotate around offset origin
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
    """
    Create a revolute (rotating) joint between two components. Allows rotation around one axis.

    Used for hinges, doors, wheels, and any single-axis rotation. The joint position
    defines the pivot point; the axis defines the rotation direction.

    Args:
        component1_index: First component index (from list_components). Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.
        axis_x: Rotation axis X component. Default 0.
        axis_y: Rotation axis Y component. Default 0.
        axis_z: Rotation axis Z component. Default 1 (Z-axis rotation).
        min_angle: Minimum rotation limit (degrees). Optional.
        max_angle: Maximum rotation limit (degrees). Optional.
        flip: Reverse rotation direction. Default False.

    Examples:
        create_revolute_joint(component1_index=0, component2_index=1, x=0, y=0, z=0)
        create_revolute_joint(component1_index=0, component2_index=1, axis_x=0, axis_y=1, axis_z=0, min_angle=-90, max_angle=90)
    """
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
    """
    Create a slider (linear) joint between two components. Allows translation along one axis.

    Used for drawers, linear actuators, and sliding mechanisms. The axis defines
    the direction of allowed movement.

    Args:
        component1_index: First component index. Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.
        axis_x: Slide axis X component. Default 1 (X-axis sliding).
        axis_y: Slide axis Y component. Default 0.
        axis_z: Slide axis Z component. Default 0.
        min_distance: Minimum slide distance (cm). Optional.
        max_distance: Maximum slide distance (cm). Optional.

    Examples:
        create_slider_joint(component1_index=0, component2_index=1, axis_x=1, axis_y=0, axis_z=0)
        create_slider_joint(component1_index=0, component2_index=1, min_distance=0, max_distance=5)
    """
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
    """
    Create a rigid (fixed) joint between two components. No relative motion allowed.

    Locks two components together at their current positions. Used for permanently
    attached parts like welded brackets or glued assemblies.

    Args:
        component1_index: First component index. Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.

    Examples:
        create_rigid_joint(component1_index=0, component2_index=1)
        create_rigid_joint(component1_index=0, component2_index=1, x=5, y=0, z=0)
    """
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
    """
    Create a cylindrical joint allowing rotation and translation along the same axis.

    Combines revolute and slider motion on one axis (2 DOF). Used for threaded
    connections, telescoping tubes, and screw-type mechanisms.

    Args:
        component1_index: First component index. Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.
        axis_x: Axis X component. Default 0.
        axis_y: Axis Y component. Default 0.
        axis_z: Axis Z component. Default 1 (Z-axis).
        min_angle: Minimum rotation limit (degrees). Optional.
        max_angle: Maximum rotation limit (degrees). Optional.
        min_distance: Minimum slide distance (cm). Optional.
        max_distance: Maximum slide distance (cm). Optional.

    Examples:
        create_cylindrical_joint(component1_index=0, component2_index=1)
        create_cylindrical_joint(component1_index=0, component2_index=1, min_distance=0, max_distance=3)
    """
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
    """
    Create a pin-slot joint allowing rotation and sliding along the axis direction.

    The axis defines the slot sliding direction; rotation occurs perpendicular to the
    slot axis. Used for adjustable hinges and cam mechanisms (2 DOF).

    Args:
        component1_index: First component index. Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.
        axis_x: Slot direction X component. Default 0.
        axis_y: Slot direction Y component. Default 0.
        axis_z: Slot direction Z component. Default 1 (Z-axis).
        min_angle: Minimum rotation limit (degrees). Optional.
        max_angle: Maximum rotation limit (degrees). Optional.
        min_distance: Minimum slide distance (cm). Optional.
        max_distance: Maximum slide distance (cm). Optional.

    Examples:
        create_pin_slot_joint(component1_index=0, component2_index=1, axis_x=1, axis_y=0, axis_z=0)
        create_pin_slot_joint(component1_index=0, component2_index=1, min_distance=-2, max_distance=2)
    """
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
    """
    Create a planar joint allowing 2D sliding and rotation on a plane (3 DOF).

    The axis defines the plane normal. Components can slide in two directions on
    the plane and rotate around the normal. Used for flat surfaces that need to
    slide freely (e.g., a puck on a table).

    Args:
        component1_index: First component index. Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.
        axis_x: Plane normal X component. Default 0.
        axis_y: Plane normal Y component. Default 1 (XZ plane).
        axis_z: Plane normal Z component. Default 0.
        min_primary_slide: Minimum primary slide distance (cm). Optional.
        max_primary_slide: Maximum primary slide distance (cm). Optional.
        min_secondary_slide: Minimum secondary slide distance (cm). Optional.
        max_secondary_slide: Maximum secondary slide distance (cm). Optional.
        min_angle: Minimum rotation limit (degrees). Optional.
        max_angle: Maximum rotation limit (degrees). Optional.

    Examples:
        create_planar_joint(component1_index=0, component2_index=1)
        create_planar_joint(component1_index=0, component2_index=1, axis_x=0, axis_y=0, axis_z=1)
    """
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
    """
    Create a ball joint allowing spherical rotation in all directions (3 DOF).

    No axis needed -- rotation is unconstrained around the joint point.
    Used for universal joints, camera mounts, and robotic linkages.

    Args:
        component1_index: First component index. Default: auto-detect.
        component2_index: Second component index. Default: auto-detect.
        x: Joint position X coordinate (cm). Default 0.
        y: Joint position Y coordinate (cm). Default 0.
        z: Joint position Z coordinate (cm). Default 0.
        min_pitch: Minimum pitch limit (degrees). Optional.
        max_pitch: Maximum pitch limit (degrees). Optional.
        min_roll: Minimum roll limit (degrees). Optional.
        max_roll: Maximum roll limit (degrees). Optional.
        min_yaw: Minimum yaw limit (degrees). Optional.
        max_yaw: Maximum yaw limit (degrees). Optional.

    Examples:
        create_ball_joint(component1_index=0, component2_index=1, x=0, y=5, z=0)
        create_ball_joint(component1_index=0, component2_index=1, min_pitch=-45, max_pitch=45)
    """
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
    """
    Drive rotation on a revolute, cylindrical, or pin-slot joint.

    Sets the angular position of a joint that supports rotation. Use to animate
    or position jointed assemblies.

    Args:
        angle: Target rotation angle (degrees).
        joint_index: Which joint to drive (default: most recent joint).

    Examples:
        set_joint_angle(angle=45)                          # Rotate most recent joint
        set_joint_angle(angle=90, joint_index=0)           # Rotate first joint
    """
    params = {"angle": angle}
    if joint_index is not None:
        params["joint_index"] = joint_index
    return send_fusion_command("set_joint_angle", params)

@mcp.tool()
def set_joint_distance(distance: float, joint_index: int = None) -> dict:
    """
    Drive translation on a slider, cylindrical, or pin-slot joint.

    Sets the linear position of a joint that supports sliding. Use to animate
    or position jointed assemblies.

    Args:
        distance: Target slide distance (cm).
        joint_index: Which joint to drive (default: most recent joint).

    Examples:
        set_joint_distance(distance=2.5)                   # Slide most recent joint
        set_joint_distance(distance=-1, joint_index=0)     # Slide first joint backward
    """
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
    Perform boolean operations (cut, join, or intersect) between bodies.

    Modifies the target body using one or more tool bodies. Use get_body_info()
    to verify body indices before combining.

    Args:
        target_body: Index of body to modify (0 = first body).
        tool_bodies: List of body indices to use as tools.
        operation: "cut" (subtract), "join" (add), or "intersect". Default "cut".
        keep_tools: If True, keep tool bodies after operation. Default False.

    Examples:
        combine(target_body=0, tool_bodies=[1], operation="cut")       # Subtract body 1 from body 0
        combine(target_body=0, tool_bodies=[1, 2], operation="join")   # Merge 3 bodies
        combine(target_body=0, tool_bodies=[1], operation="intersect") # Keep only overlap
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
    Undo recent operations in the Fusion 360 design history.

    Reverts the most recent operations. Returns the actual number of operations
    undone, which may be less than requested if fewer operations exist.

    Args:
        count: Number of operations to undo (default 1).

    Examples:
        undo()                    # Undo last operation
        undo(count=3)             # Undo last 3 operations
    """
    return send_fusion_command("undo", {"count": count})

@mcp.tool()
def delete_body(body_index: int = None) -> dict:
    """
    Delete a body from the design by index.

    Removes the specified body permanently. Use get_design_info() to see body count
    and get_body_info() for detailed body information before deleting.

    Args:
        body_index: Index of body to delete (default: most recent body).

    Examples:
        delete_body()                    # Delete most recent body
        delete_body(body_index=0)        # Delete first body
    """
    params = {}
    if body_index is not None:
        params["body_index"] = body_index
    return send_fusion_command("delete_body", params)

@mcp.tool()
def delete_sketch(sketch_index: int = None) -> dict:
    """
    Delete a sketch from the design by index.

    Removes the specified sketch and any geometry it contains. Features built
    from this sketch (e.g., extrusions) may become invalid.

    Args:
        sketch_index: Index of sketch to delete (default: most recent sketch).

    Examples:
        delete_sketch()                      # Delete most recent sketch
        delete_sketch(sketch_index=0)        # Delete first sketch
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
    """
    Export the design as an STL file for 3D printing.

    STL is the most widely supported 3D printing format. Creates a triangulated
    mesh of all visible bodies.

    Args:
        filepath: Full absolute path for the output STL file.

    Examples:
        export_stl(filepath="C:/exports/part.stl")
    """
    return send_fusion_command("export_stl", {"filepath": filepath})

@mcp.tool()
def export_step(filepath: str) -> dict:
    """
    Export the design as a STEP file for CAD interchange.

    STEP is the standard format for sharing precise CAD geometry between different
    CAD software. Preserves exact surfaces, unlike mesh formats.

    Args:
        filepath: Full absolute path for the output STEP file.

    Examples:
        export_step(filepath="C:/exports/part.step")
    """
    return send_fusion_command("export_step", {"filepath": filepath})

@mcp.tool()
def export_3mf(filepath: str) -> dict:
    """
    Export the design as a 3MF file for modern 3D printing.

    3MF supports color, materials, and multi-body prints. Preferred over STL
    for printers that support it. Falls back gracefully on older Fusion versions.

    Args:
        filepath: Full absolute path for the output 3MF file.

    Examples:
        export_3mf(filepath="C:/exports/part.3mf")
    """
    return send_fusion_command("export_3mf", {"filepath": filepath})

# =============================================================================
# IMPORT
# =============================================================================

@mcp.tool()
def import_mesh(filepath: str, unit: str = "mm") -> dict:
    """
    Import a mesh file (STL, OBJ, or 3MF) into the design.

    Imports triangulated mesh geometry. The imported mesh becomes a body that can
    be used with other operations. Specify the unit the mesh was designed in.

    Args:
        filepath: Full absolute path to the mesh file (STL, OBJ, or 3MF).
        unit: Unit of the mesh file -- "mm", "cm", or "in" (default "mm").

    Examples:
        import_mesh(filepath="C:/models/bracket.stl")
        import_mesh(filepath="C:/models/part.obj", unit="cm")
    """
    return send_fusion_command("import_mesh", {"filepath": filepath, "unit": unit})

# =============================================================================
# SKETCH CONSTRAINTS (Phase 2)
# =============================================================================

@mcp.tool()
def constrain_horizontal(curve_index: int) -> dict:
    """
    Constrain a sketch line to be horizontal (parallel to X axis).

    Forces the line to remain perfectly horizontal regardless of other geometry changes.

    Args:
        curve_index: Index of the line to constrain. Use get_sketch_info() to see curves.

    Examples:
        constrain_horizontal(curve_index=0)
    """
    return send_fusion_command("constrain_horizontal", {"curve_index": curve_index})

@mcp.tool()
def constrain_vertical(curve_index: int) -> dict:
    """
    Constrain a sketch line to be vertical (parallel to Y axis).

    Forces the line to remain perfectly vertical regardless of other geometry changes.

    Args:
        curve_index: Index of the line to constrain. Use get_sketch_info() to see curves.

    Examples:
        constrain_vertical(curve_index=1)
    """
    return send_fusion_command("constrain_vertical", {"curve_index": curve_index})

@mcp.tool()
def constrain_perpendicular(curve_index: int, curve_index_2: int) -> dict:
    """
    Constrain two sketch lines to be perpendicular (90 degrees apart).

    Forces the two lines to maintain a right angle relationship.

    Args:
        curve_index: First line index.
        curve_index_2: Second line index.

    Examples:
        constrain_perpendicular(curve_index=0, curve_index_2=1)
    """
    return send_fusion_command("constrain_perpendicular", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_parallel(curve_index: int, curve_index_2: int) -> dict:
    """
    Constrain two sketch lines to remain parallel.

    Forces the two lines to maintain the same angle regardless of geometry changes.

    Args:
        curve_index: First line index.
        curve_index_2: Second line index.

    Examples:
        constrain_parallel(curve_index=0, curve_index_2=2)
    """
    return send_fusion_command("constrain_parallel", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_tangent(curve_index: int, curve_index_2: int) -> dict:
    """
    Constrain two sketch curves to be tangent at their nearest endpoints.

    Forces smooth (G1) continuity between curves. Works with lines, arcs,
    circles, and splines.

    Args:
        curve_index: First curve index (line, arc, circle, or spline).
        curve_index_2: Second curve index.

    Examples:
        constrain_tangent(curve_index=0, curve_index_2=1)
    """
    return send_fusion_command("constrain_tangent", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_coincident(point_index: int, curve_index: int = None, point_index_2: int = None) -> dict:
    """
    Constrain a sketch point to lie on a curve or coincide with another point.

    Provide either curve_index (point-on-curve) or point_index_2 (point-to-point),
    not both. Use get_sketch_info() to see available indices.

    Args:
        point_index: The point to constrain.
        curve_index: Target curve (point will be placed on this curve). Optional.
        point_index_2: Target point (points will coincide). Optional.

    Examples:
        constrain_coincident(point_index=0, curve_index=2)          # Point on curve
        constrain_coincident(point_index=0, point_index_2=3)        # Points coincide
    """
    params = {"point_index": point_index}
    if curve_index is not None:
        params["curve_index"] = curve_index
    if point_index_2 is not None:
        params["point_index_2"] = point_index_2
    return send_fusion_command("constrain_coincident", params)

@mcp.tool()
def constrain_concentric(curve_index: int, curve_index_2: int) -> dict:
    """
    Constrain two circles or arcs to share the same center point.

    Forces the two curves to be concentric (same center). Useful for creating
    rings, washers, and nested circular features.

    Args:
        curve_index: First circle or arc index.
        curve_index_2: Second circle or arc index.

    Examples:
        constrain_concentric(curve_index=0, curve_index_2=1)
    """
    return send_fusion_command("constrain_concentric", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_equal(curve_index: int, curve_index_2: int) -> dict:
    """
    Constrain two sketch curves to have equal size.

    For lines: forces equal length. For circles/arcs: forces equal radius.
    Both curves must be the same type.

    Args:
        curve_index: First curve index.
        curve_index_2: Second curve index (must be same type as first).

    Examples:
        constrain_equal(curve_index=0, curve_index_2=2)     # Equal length lines
    """
    return send_fusion_command("constrain_equal", {
        "curve_index": curve_index, "curve_index_2": curve_index_2
    })

@mcp.tool()
def constrain_symmetric(symmetry_curve_index: int, curve_index: int = None, curve_index_2: int = None,
                         point_index: int = None, point_index_2: int = None) -> dict:
    """
    Constrain two entities to be symmetric about a line of symmetry.

    Mirrors the position and shape of one entity to match the other across the
    symmetry line. Provide either (curve_index + curve_index_2) for curve symmetry
    or (point_index + point_index_2) for point symmetry.

    Args:
        symmetry_curve_index: The line of symmetry (must be a line curve).
        curve_index: First curve for curve symmetry. Optional.
        curve_index_2: Second curve for curve symmetry. Optional.
        point_index: First point for point symmetry. Optional.
        point_index_2: Second point for point symmetry. Optional.

    Examples:
        constrain_symmetric(symmetry_curve_index=4, curve_index=0, curve_index_2=2)
        constrain_symmetric(symmetry_curve_index=4, point_index=0, point_index_2=1)
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
    """
    Add a distance dimension to constrain length between two points or along a curve.

    Dimensions drive geometry -- specifying a value forces sketch entities to match.
    Provide either curve_index (line length) or point_index + point_index_2 (point-to-point).

    Args:
        value: Dimension value (cm). Required -- dimensions drive geometry.
        curve_index: Line to dimension (uses its start/end points). Optional.
        point_index: First point for point-to-point distance. Optional.
        point_index_2: Second point for point-to-point distance. Optional.

    Examples:
        dimension_distance(value=5, curve_index=0)                          # Set line length
        dimension_distance(value=3, point_index=0, point_index_2=1)         # Point-to-point
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
    """
    Add a diameter or radius dimension to a circle or arc.

    Forces the circle or arc to match the specified size. Use "diameter" for
    overall width or "radius" for half-width.

    Args:
        curve_index: Index of the circle or arc to dimension.
        value: Dimension value (cm) -- diameter or radius depending on type.
        type: "diameter" or "radius" (default "diameter").

    Examples:
        dimension_radial(curve_index=0, value=5)                        # 5cm diameter
        dimension_radial(curve_index=1, value=2.5, type="radius")       # 2.5cm radius
    """
    return send_fusion_command("dimension_radial", {
        "curve_index": curve_index, "value": value, "type": type
    })

@mcp.tool()
def dimension_angular(curve_index: int, curve_index_2: int, value: float) -> dict:
    """
    Add an angular dimension between two sketch lines.

    Forces the angle between two intersecting or non-parallel lines to match
    the specified value.

    Args:
        curve_index: First line index.
        curve_index_2: Second line index.
        value: Angle value (degrees).

    Examples:
        dimension_angular(curve_index=0, curve_index_2=1, value=45)     # 45 degree angle
        dimension_angular(curve_index=2, curve_index_2=3, value=90)     # Right angle
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

# FEAT-05 NOTE: hole() and thread() ARE registered (79+ tools total).
# Claude Code defers tools when count exceeds threshold ("Tool Search" mode).
# Users can invoke them directly or use /mcp to verify registration.
# This is expected MCP client behavior, not a server-side issue.

if __name__ == "__main__":
    print(f"Fusion 360 MCP Server starting (PID {os.getpid()})", file=sys.stderr)
    mcp.run()
