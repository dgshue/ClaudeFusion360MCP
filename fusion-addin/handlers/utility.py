import adsk.core
import adsk.fusion


def undo(design, rootComp, params):
    app = adsk.core.Application.get()
    count = params.get('count', 1)
    for _ in range(count):
        app.executeTextCommand("Commands.Undo")
    return {"success": True, "undo_count": count}


def delete_body(design, rootComp, params):
    if rootComp.bRepBodies.count == 0:
        return {"success": False, "error": "No bodies in design."}

    body_index = params.get('body_index', rootComp.bRepBodies.count - 1)
    if body_index < 0 or body_index >= rootComp.bRepBodies.count:
        return {
            "success": False,
            "error": f"Body index {body_index} out of range. Design has {rootComp.bRepBodies.count} bodies (0-{rootComp.bRepBodies.count - 1})."
        }
    body = rootComp.bRepBodies.item(body_index)
    body_name = body.name
    body.deleteMe()
    return {"success": True, "deleted": body_name}


def delete_sketch(design, rootComp, params):
    if rootComp.sketches.count == 0:
        return {"success": False, "error": "No sketches in design."}

    sketch_index = params.get('sketch_index', rootComp.sketches.count - 1)
    if sketch_index < 0 or sketch_index >= rootComp.sketches.count:
        return {
            "success": False,
            "error": f"Sketch index {sketch_index} out of range. Design has {rootComp.sketches.count} sketches (0-{rootComp.sketches.count - 1})."
        }
    sketch = rootComp.sketches.item(sketch_index)
    sketch_name = sketch.name
    sketch.deleteMe()
    return {"success": True, "deleted": sketch_name}


def fit_view(design, rootComp, params):
    app = adsk.core.Application.get()
    app.activeViewport.fit()
    return {"success": True}
