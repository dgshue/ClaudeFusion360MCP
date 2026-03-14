import adsk.core
import adsk.fusion

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from helpers.bodies import get_body, get_sketch


def undo(design, rootComp, params):
    """Undo the specified number of operations.

    Uses the undocumented but community-standard executeTextCommand approach.
    Each call undoes one operation. Stops early if nothing left to undo.
    """
    app = adsk.core.Application.get()
    count = params.get('count', 1)
    undone = 0
    for i in range(count):
        try:
            app.executeTextCommand("Commands.Undo")
            undone += 1
        except:
            break  # No more operations to undo
    return {"success": True, "undone_count": undone, "requested_count": count}


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
