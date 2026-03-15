from .sketch import (
    create_sketch, draw_line, draw_circle, draw_rectangle,
    draw_arc, draw_polygon, set_construction, finish_sketch
)
from .feature import (
    extrude, revolve, fillet, chamfer, shell, draft,
    pattern_rectangular, pattern_circular, mirror, combine,
    sweep, loft
)
from .query import get_design_info, get_body_info, measure
from .component import (
    create_component, list_components, delete_component,
    move_component, rotate_component, check_interference
)
from .joint import (
    create_revolute_joint, create_slider_joint,
    set_joint_angle, set_joint_distance
)
from .sketch_primitives import (
    draw_spline, draw_ellipse, draw_slot, draw_point, draw_text
)
from .sketch_ops import (
    offset_curves, project_geometry, import_svg
)
from .utility import undo, delete_body, delete_sketch, fit_view
from .io import export_stl, export_step, export_3mf, import_mesh
from .sketch_constraints import (
    constrain_horizontal, constrain_vertical, constrain_perpendicular,
    constrain_parallel, constrain_tangent, constrain_coincident,
    constrain_concentric, constrain_equal, constrain_symmetric
)
from .sketch_dimensions import (
    dimension_distance, dimension_radial, dimension_angular
)
from .sketch_query import get_sketch_info
from .construction import construction_plane, construction_axis, construction_point
from .hole_thread import hole, thread


# Dict mapping all 42 tool names (excluding batch, which is handled inline)
# to their handler functions. Each handler has signature:
#   handler(design, rootComp, params) -> dict
HANDLER_MAP = {
    # Sketch tools (7)
    'create_sketch': create_sketch,
    'draw_line': draw_line,
    'draw_circle': draw_circle,
    'draw_rectangle': draw_rectangle,
    'draw_arc': draw_arc,
    'draw_polygon': draw_polygon,
    'set_construction': set_construction,
    'finish_sketch': finish_sketch,

    # New sketch primitives (Phase 2)
    'draw_spline': draw_spline,
    'draw_ellipse': draw_ellipse,
    'draw_slot': draw_slot,
    'draw_point': draw_point,
    'draw_text': draw_text,
    # Sketch operations (Phase 2)
    'offset_curves': offset_curves,
    'project_geometry': project_geometry,
    'import_svg': import_svg,

    # Feature tools (10)
    'extrude': extrude,
    'revolve': revolve,
    'fillet': fillet,
    'chamfer': chamfer,
    'shell': shell,
    'draft': draft,
    'pattern_rectangular': pattern_rectangular,
    'pattern_circular': pattern_circular,
    'mirror': mirror,
    'combine': combine,
    'sweep': sweep,
    'loft': loft,

    # Query tools (3)
    'get_design_info': get_design_info,
    'get_body_info': get_body_info,
    'measure': measure,

    # Component tools (6)
    'create_component': create_component,
    'list_components': list_components,
    'delete_component': delete_component,
    'move_component': move_component,
    'rotate_component': rotate_component,
    'check_interference': check_interference,

    # Joint tools (4)
    'create_revolute_joint': create_revolute_joint,
    'create_slider_joint': create_slider_joint,
    'set_joint_angle': set_joint_angle,
    'set_joint_distance': set_joint_distance,

    # Utility tools (4)
    'undo': undo,
    'delete_body': delete_body,
    'delete_sketch': delete_sketch,
    'fit_view': fit_view,

    # I/O tools (4)
    'export_stl': export_stl,
    'export_step': export_step,
    'export_3mf': export_3mf,
    'import_mesh': import_mesh,

    # Sketch constraints (Phase 2)
    'constrain_horizontal': constrain_horizontal,
    'constrain_vertical': constrain_vertical,
    'constrain_perpendicular': constrain_perpendicular,
    'constrain_parallel': constrain_parallel,
    'constrain_tangent': constrain_tangent,
    'constrain_coincident': constrain_coincident,
    'constrain_concentric': constrain_concentric,
    'constrain_equal': constrain_equal,
    'constrain_symmetric': constrain_symmetric,

    # Sketch dimensions (Phase 2)
    'dimension_distance': dimension_distance,
    'dimension_radial': dimension_radial,
    'dimension_angular': dimension_angular,

    # Sketch query (Phase 2)
    'get_sketch_info': get_sketch_info,

    # Construction geometry (Phase 3)
    'construction_plane': construction_plane,
    'construction_axis': construction_axis,
    'construction_point': construction_point,

    # Manufacturing features (Phase 3)
    'hole': hole,
    'thread': thread,
}
