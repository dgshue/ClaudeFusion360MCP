import adsk.core
import adsk.fusion
import json
import os
import sys
import threading
import traceback
from pathlib import Path

# Ensure sub-packages are importable from the add-in directory
_addin_dir = os.path.dirname(os.path.abspath(__file__))
if _addin_dir not in sys.path:
    sys.path.insert(0, _addin_dir)

from handlers import HANDLER_MAP
from helpers.errors import wrap_handler

# Module-level state
app = None
handlers = []  # prevent GC of event handlers (Pitfall 2)
stop_flag = None
custom_event = None
monitor_thread = None

COMM_DIR = Path.home() / "fusion_mcp_comm"
CUSTOM_EVENT_ID = 'FusionMCP_CommandEvent'


class CommandEventHandler(adsk.core.CustomEventHandler):
    """Handles commands on the main thread via CustomEvent."""

    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            event_data = json.loads(args.additionalInfo)
            command = event_data['command']
            cmd_id = event_data['id']

            # Execute on main thread -- safe to call Fusion API here
            result = execute_command(command)

            # Write response file
            resp_file = COMM_DIR / f"response_{cmd_id}.json"
            with open(resp_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            # Write error response so the MCP server doesn't hang
            try:
                cmd_id = event_data.get('id', 'unknown')
            except Exception:
                cmd_id = 'unknown'
            resp_file = COMM_DIR / f"response_{cmd_id}.json"
            try:
                with open(resp_file, 'w') as f:
                    json.dump({
                        "success": False,
                        "error": f"Internal error processing command: {str(e)}"
                    }, f, indent=2)
            except Exception:
                pass  # File write failure during error handling -- nothing more we can do
            # Log full traceback for debugging
            app.log(f"FusionMCP CommandEventHandler error: {traceback.format_exc()}")


class MonitorThread(threading.Thread):
    """Monitors COMM_DIR for command files and fires CustomEvents.

    This thread does NO Fusion API calls -- it only reads files and fires
    events. All Fusion API work happens in CommandEventHandler.notify()
    on the main thread.
    """

    def __init__(self, event):
        threading.Thread.__init__(self)
        self.stopped = event
        self.daemon = True

    def run(self):
        while not self.stopped.wait(0.1):
            try:
                cmd_files = list(COMM_DIR.glob("command_*.json"))
                for cmd_file in cmd_files:
                    try:
                        with open(cmd_file, 'r') as f:
                            command = json.load(f)
                        # Remove command file after reading
                        try:
                            cmd_file.unlink()
                        except OSError:
                            pass  # File already removed or locked -- non-fatal
                        # Fire custom event -- handler runs on main thread
                        app.fireCustomEvent(CUSTOM_EVENT_ID, json.dumps({
                            'command': command,
                            'id': command.get('id', 'unknown')
                        }))
                    except (json.JSONDecodeError, KeyError):
                        # Malformed command file -- skip it
                        try:
                            cmd_file.unlink()
                        except OSError:
                            pass
                    except Exception:
                        pass  # File I/O error during polling -- non-fatal
            except Exception:
                pass  # COMM_DIR glob error -- non-fatal, will retry on next loop


def execute_command(command):
    """Dispatch a command to the appropriate handler.

    Uses HANDLER_MAP for dict-based dispatch. The special 'batch' command
    is handled inline -- it iterates commands and stops on first error,
    returning partial results.
    """
    global app
    tool_name = command.get('name')
    params = command.get('params', {})

    try:
        design = app.activeProduct
        if not design:
            return {"success": False, "error": "No active design. Open or create a design first."}
        rootComp = design.rootComponent
    except Exception as e:
        return {"success": False, "error": f"Cannot access active design: {str(e)}"}

    # Special case: batch command
    if tool_name == 'batch':
        return _execute_batch(design, rootComp, params)

    # Dict-based dispatch
    handler = HANDLER_MAP.get(tool_name)
    if handler is None:
        available = sorted(HANDLER_MAP.keys())
        return {
            "success": False,
            "error": f"Unknown tool: '{tool_name}'. Available tools: {', '.join(available)}"
        }

    return wrap_handler(tool_name, handler, design, rootComp, params)


def _execute_batch(design, rootComp, params):
    """Execute a batch of commands, stopping on first error."""
    commands_list = params.get('commands', [])
    if not commands_list:
        return {"success": False, "error": "Batch requires a 'commands' array."}

    results = []
    for i, cmd in enumerate(commands_list):
        sub_name = cmd.get('name', '')
        sub_params = cmd.get('params', {})

        handler = HANDLER_MAP.get(sub_name)
        if handler is None:
            results.append({
                "command_index": i,
                "tool": sub_name,
                "success": False,
                "error": f"Unknown tool: '{sub_name}'"
            })
            return {
                "success": False,
                "error": f"Batch stopped at command {i}: unknown tool '{sub_name}'",
                "results": results
            }

        result = wrap_handler(sub_name, handler, design, rootComp, sub_params)
        result["command_index"] = i
        result["tool"] = sub_name
        results.append(result)

        if not result.get("success", False):
            return {
                "success": False,
                "error": f"Batch stopped at command {i} ({sub_name}): {result.get('error', 'unknown error')}",
                "results": results
            }

    return {"success": True, "results": results, "completed": len(results)}


def run(context):
    global app, custom_event, stop_flag, monitor_thread, handlers
    try:
        app = adsk.core.Application.get()
        COMM_DIR.mkdir(exist_ok=True)

        # Register custom event for main-thread execution
        custom_event = app.registerCustomEvent(CUSTOM_EVENT_ID)
        handler = CommandEventHandler()
        custom_event.add(handler)
        handlers.append(handler)  # prevent GC

        # Start monitor thread (only does file I/O + fireCustomEvent)
        stop_flag = threading.Event()
        monitor_thread = MonitorThread(stop_flag)
        monitor_thread.start()

        app.log(f"FusionMCP started. Listening at: {COMM_DIR}")
    except Exception:
        app.log(f"FusionMCP failed to start: {traceback.format_exc()}")


def stop(context):
    global stop_flag, custom_event, handlers, monitor_thread
    try:
        if stop_flag:
            stop_flag.set()
        if custom_event and handlers:
            custom_event.remove(handlers[0])
        if custom_event:
            app.unregisterCustomEvent(CUSTOM_EVENT_ID)
        handlers.clear()
        app.log("FusionMCP stopped.")
    except Exception:
        pass  # Cleanup errors during shutdown -- non-fatal
