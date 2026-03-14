import adsk.core
import traceback


def wrap_handler(tool_name, handler_fn, design, rootComp, params):
    """Execute a handler with error wrapping.

    Catches any exception and returns a verbose, user-friendly error message
    with tool name, formatted params, and a contextual hint. Never exposes
    raw Python tracebacks or adsk error codes to the caller.

    Full traceback is logged via app.log() for debugging.
    """
    try:
        return handler_fn(design, rootComp, params)
    except Exception as e:
        # Log full traceback for debugging
        try:
            app = adsk.core.Application.get()
            app.log(f"FusionMCP handler error [{tool_name}]: {traceback.format_exc()}")
        except Exception:
            pass

        error_msg = _human_readable_error(e)
        hint = generate_hint(tool_name, params, e)
        result = {
            "success": False,
            "error": f"{tool_name}({format_params(params)}) failed: {error_msg}"
        }
        if hint:
            result["hint"] = hint
        return result


def format_params(params):
    """Format a params dict as a readable string for error context.

    Example: "radius=0.5, edges=[3, 7]"
    """
    if not params:
        return ""
    parts = []
    for key, value in params.items():
        if isinstance(value, str) and len(value) > 50:
            value = value[:47] + "..."
        parts.append(f"{key}={value}")
    return ", ".join(parts)


def _human_readable_error(exception):
    """Convert an exception to a human-readable error message.

    Strips adsk error codes and cryptic internal messages, replacing
    them with plain English.
    """
    msg = str(exception)

    # Common adsk error patterns mapped to friendly messages
    error_patterns = {
        "RuntimeError: 2": "Operation failed - check that all parameters are valid",
        "RuntimeError: 3": "Invalid input - one or more parameters are out of range",
        "RuntimeError: 4": "Operation not available in current context",
        "index out of range": "Index out of range",
        "NoneType": "Required object not found (may have been deleted or doesn't exist yet)",
    }

    for pattern, friendly in error_patterns.items():
        if pattern in msg:
            return friendly

    # If the message is short and readable, use it as-is
    if len(msg) < 200 and not msg.startswith("RuntimeError"):
        return msg

    # Fallback: generic but helpful
    return f"Operation failed: {msg[:150]}"


def generate_hint(tool_name, params, exception):
    """Generate a contextual hint based on the tool, params, and error.

    Maps common error patterns to actionable suggestions that help
    the caller fix the issue.
    """
    msg = str(exception).lower()

    # Index out of range hints
    if "index" in msg and ("range" in msg or "out of" in msg):
        if tool_name in ('fillet', 'chamfer'):
            return "Use get_body_info() to see available edges with their indices and labels."
        if tool_name in ('shell', 'draft'):
            return "Use get_body_info() to see available faces with their indices and labels."
        if 'body' in msg or tool_name in ('extrude', 'revolve'):
            return "Use get_design_info() to see body and sketch counts."
        if 'sketch' in msg:
            return "Use get_design_info() to see available sketches."
        return "Use get_design_info() or get_body_info() to see available indices."

    # No sketches / no profiles
    if "no sketch" in msg or "sketches" in msg:
        return "Call create_sketch() first to create a sketch, then draw geometry in it."
    if "no profile" in msg or "profiles" in msg:
        return "Draw closed geometry in the sketch before extruding. Profiles are formed by closed shapes (rectangles, circles, etc.)."

    # No bodies
    if "no bod" in msg:
        return "Create geometry first: create_sketch() -> draw shapes -> extrude()."

    # No design
    if "no active design" in msg or "no design" in msg:
        return "Open or create a Fusion 360 design document first."

    # NoneType / missing object
    if "nonetype" in msg or "none" in msg:
        return "A required object was not found. Use get_design_info() to check the current state."

    # File path errors
    if "path" in msg or "file" in msg or "directory" in msg:
        return "Check that the file path exists and is accessible."

    # Joint errors
    if tool_name.startswith('create_') and 'joint' in tool_name:
        return "Joints require at least 2 components. Use create_component() first."

    # Component errors
    if tool_name in ('move_component', 'rotate_component', 'delete_component'):
        return "Use list_components() to see available components with their indices."

    return None
