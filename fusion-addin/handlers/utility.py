import adsk.core
import adsk.fusion

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from helpers.bodies import get_body, get_sketch


def undo(design, rootComp, params):
    """Undo operations with timeline position validation.

    Uses executeTextCommand for undo, but validates each undo
    actually moved the timeline marker back. This catches silent
    no-ops from the undocumented text command API.
    """
    app = adsk.core.Application.get()
    count = params.get('count', 1)
    undone = 0
    timeline = design.timeline

    # Nothing to undo if timeline is empty
    if timeline.markerPosition == 0:
        return {
            "success": True,
            "undone_count": 0,
            "requested_count": count,
            "timeline_position": 0,
            "message": "Nothing to undo - timeline is empty"
        }

    for i in range(count):
        pos_before = timeline.markerPosition
        if pos_before == 0:
            break  # Already at beginning

        try:
            app.executeTextCommand("Commands.Undo")
        except Exception:
            break

        pos_after = timeline.markerPosition
        if pos_after < pos_before:
            undone += 1
        else:
            break  # Undo had no effect

    return {
        "success": True,
        "undone_count": undone,
        "requested_count": count,
        "timeline_position": timeline.markerPosition
    }


def delete_body(design, rootComp, params):
    """Delete a body by index. Uses get_body helper for validation."""
    body = get_body(rootComp, params.get('body_index'))
    body_name = body.name
    body.deleteMe()
    return {"success": True, "deleted_body": body_name}


def delete_sketch(design, rootComp, params):
    """Delete a sketch by index. Uses get_sketch helper for validation."""
    sketch = get_sketch(rootComp, params.get('sketch_index'))
    sketch_name = sketch.name
    sketch.deleteMe()
    return {"success": True, "deleted_sketch": sketch_name}


def fit_view(design, rootComp, params):
    """Fit the active viewport to show all geometry."""
    app = adsk.core.Application.get()
    app.activeViewport.fit()
    return {"success": True}
