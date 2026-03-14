from .sketch import (
    create_sketch, draw_line, draw_circle, draw_rectangle,
    draw_arc, draw_polygon, finish_sketch
)
from .feature import (
    extrude, revolve, fillet, chamfer, shell, draft,
    pattern_rectangular, pattern_circular, mirror, combine
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
from .utility import undo, delete_body, delete_sketch, fit_view
from .io import export_stl, export_step, export_3mf, import_mesh


# Dict mapping all 39 tool names (excluding batch, which is handled inline)
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
    'finish_sketch': finish_sketch,

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
}
