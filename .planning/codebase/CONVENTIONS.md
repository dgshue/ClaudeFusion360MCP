# Coding Conventions

**Analysis Date:** 2026-03-13

## Naming Patterns

**Files:**
- Descriptive PascalCase with clear purpose: `FusionMCP.py`, `fusion360_mcp_server.py`
- Add-in manifest files use the same base name: `FusionMCP.manifest`
- Convention: primary module has capitalized name, server scripts use snake_case

**Functions:**
- snake_case for all function names: `run()`, `monitor_commands()`, `send_fusion_command()`, `create_sketch()`
- Helper functions follow same convention: `execute_command()`, `draw_circle()`, `add_fillet()`
- MCP decorator functions (tools exposed to Claude): snake_case with `@mcp.tool()` decorator

**Variables:**
- Global state: UPPER_CASE (e.g., `COMM_DIR`, `stop_thread`, `app`, `ui`)
- Local variables and parameters: snake_case (e.g., `tool_name`, `params`, `plane_name`, `sketch`)
- Dictionary keys: snake_case (e.g., `"success"`, `"error"`, `"center_x"`, `"distance"`)

**Types/Classes:**
- MCP tools are decorated functions, not classes: `@mcp.tool()` pattern
- No type hints used in current codebase (Python 3.10+ but untyped)
- Return values are always dictionaries with consistent structure: `{"success": bool, "error": str, ...}`

## Code Style

**Formatting:**
- No explicit formatter configured (no .prettier, .black, etc.)
- Line length appears to follow standard convention (80-100 chars observed)
- Indentation: 4 spaces (Python standard)
- Opening braces on same line
- Empty lines used to separate logical sections

**Linting:**
- No linter configuration detected (.eslintrc, .pylintrc, etc.)
- Code follows basic Python conventions but not enforced
- See `/c/Users/dgshue/Documents/GitHub/ClaudeFusion360MCP/.vscode/launch.json` - VSCode debugging configured but no lint config

**Section Organization:**
- Files use comment separators for major sections:
  ```python
  # =============================================================================
  # BATCH OPERATIONS
  # =============================================================================
  ```
- All tools grouped by functional area (sketching, 3D operations, assembly, etc.)
- Related operations clustered together

## Import Organization

**Order:**
1. Standard library (adsk, json, time, threading, traceback, math, pathlib)
2. Third-party framework (mcp.server.fastmcp)
3. No local imports (monolithic files)

**Pattern from `fusion360_mcp_server.py`:**
```python
from mcp.server.fastmcp import FastMCP
import json
import time
from pathlib import Path
```

**Pattern from `FusionMCP.py`:**
```python
import adsk.core
import adsk.fusion
import traceback
import json
import time
import threading
from pathlib import Path
```

**Path Aliases:**
- Not used; all imports are absolute
- File system paths use `Path` from `pathlib`: `COMM_DIR = Path.home() / "fusion_mcp_comm"`

## Error Handling

**Patterns:**
1. **Broad exception catching:** Used defensively in background threads and I/O operations
   ```python
   try:
       # Operation that might fail
   except:
       pass  # Silently continue
   ```
   Location: `FusionMCP.py` lines 26-28, 32-37, 42-56

2. **Specific exception handling:** Used for explicit errors
   ```python
   except Exception as e:
       return {"success": False, "error": str(e)}
   ```
   Location: `FusionMCP.py` line 88; `fusion360_mcp_server.py` lines 55-62

3. **Return-based error reporting:** All command functions return consistent dict
   ```python
   return {"success": False, "error": "No active design"}
   return {"success": True, "sketch_name": sketch.name}
   ```

4. **Timeout-based exceptions:** Raised for timeout conditions
   ```python
   raise Exception("Timeout after 45s - is Fusion 360 running with FusionMCP add-in?")
   ```
   Location: `fusion360_mcp_server.py` line 64

**Convention:** All exceptions converted to error responses with human-readable messages in command handlers.

## Logging

**Framework:** `console` (none; uses UI message boxes in add-in, no logging framework)

**Patterns:**
- Add-in uses UI message boxes for status: `ui.messageBox('Fusion MCP Started!\n\nListening at:\n' + str(COMM_DIR))`
- No structured logging; errors either silently ignored or returned as dicts
- Thread-based monitor has no log output (silent background operation)

**When to Log:**
- Status on startup/shutdown (UI messageBox in `run()` and `stop()`)
- Errors are returned in response dict, not logged
- Silent failures in background monitoring (defensive catch-all in `monitor_commands()`)

## Comments

**When to Comment:**
- Section headers for functional groupings (see section markers above)
- Inline comments rare; code is self-documenting through function names
- No TODO/FIXME comments observed in production code

**JSDoc/Docstrings:**
- Extensive docstrings on all MCP tools (tools exposed to Claude)
- Format: Google-style docstring with `Args:`, `Returns:`, `Examples:` sections
- Located in `fusion360_mcp_server.py` tools (lines 71-86, 93-104, 152-166, etc.)
- Example:
  ```python
  @mcp.tool()
  def batch(commands: list) -> dict:
      """
      Execute multiple Fusion commands in a single call - MUCH faster for complex operations.

      Example: batch([
          {"name": "create_sketch", "params": {"plane": "XY"}},
          ...
      ])
      """
  ```
- No docstrings on helper functions (non-MCP functions in `FusionMCP.py`)

**Convention:** Document all user-facing API methods extensively; helpers and internals can be minimal.

## Function Design

**Size:**
- Most functions 5-20 lines
- Largest functions: `send_fusion_command()` (24 lines), `monitor_commands()` (18 lines)
- Generally small, focused operations

**Parameters:**
- Positional + optional keyword arguments with defaults
- Example: `pattern_circular(count: int, angle: float = 360, axis: str = "Z", body_index: int = None)`
- Always include reasonable defaults for optional params

**Return Values:**
- All MCP tools return dicts with `"success"` boolean
- Dict always includes `"error"` key if unsuccessful
- Dict includes relevant data when successful (e.g., `"sketch_name"`, `"feature_name"`, `"body_count"`)
- Helper functions return dicts with success/error pattern

**Pattern:**
```python
def command_handler(param1, param2=default):
    try:
        # Do work
        return {"success": True, "result_key": value}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Module Design

**Exports:**
- MCP server exposes 50+ tools via `@mcp.tool()` decorator
- Add-in exports two lifecycle functions: `run(context)` and `stop(context)` (Fusion API convention)
- No explicit `__all__` lists

**Barrel Files:**
- Not used; code is organized in single files per module
- `fusion360_mcp_server.py` is ~627 lines, all tools in one file
- `FusionMCP.py` is ~177 lines, all handlers in one file

**Communication Pattern:**
- File-system-based IPC via JSON files in `~/fusion_mcp_comm/`
- Commands written as `command_{timestamp}.json`
- Responses written as `response_{timestamp}.json`
- Polling interval: 50ms (200 iterations max for 45s timeout)

## Parameter Passing

**Convention:**
- MCP tool parameters passed as typed function args: `extrude(distance: float, profile_index: int = 0, taper_angle: float = 0)`
- Internal command dicts use same parameter names: `{"distance": distance, "profile_index": profile_index, "taper_angle": taper_angle}`
- Parser in add-in extracts params from command dict: `params = command.get('params', {})`

**Consistency Rule:**
- Parameter names must match exactly between MCP tool signature and internal command dict
- Unit conversions handled by caller (all dimensions in centimeters, no unit parameters)

---

*Convention analysis: 2026-03-13*
