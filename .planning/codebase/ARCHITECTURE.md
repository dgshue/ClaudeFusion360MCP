# Architecture

**Analysis Date:** 2026-03-13

## Pattern Overview

**Overall:** Client-Server with File-System IPC (Inter-Process Communication)

**Key Characteristics:**
- Claude Desktop communicates with MCP server via Model Context Protocol (HTTP/stdio)
- MCP server communicates with Fusion 360 add-in via JSON files in shared directory
- Asynchronous, polling-based command execution with 50ms polling interval
- 45-second timeout for all operations
- Batch command support for multi-step operations
- Stateless server design - each command is independent

## Layers

**Claude Desktop (Client):**
- Purpose: User interface and AI reasoning layer
- Location: External to codebase (Anthropic's Claude Desktop app)
- Contains: User prompts, conversation history, tool invocation logic
- Depends on: MCP protocol from server
- Used by: End users requesting Fusion 360 CAD operations

**MCP Server:**
- Purpose: Bridge between Claude and Fusion 360; tool definition and command routing
- Location: `mcp-server/fusion360_mcp_server.py`
- Contains: 50+ tool definitions wrapped with `@mcp.tool()` decorators
- Depends on: FastMCP framework, file system I/O
- Used by: Claude Desktop via MCP protocol

**File System IPC Layer:**
- Purpose: Asynchronous communication channel between server and add-in
- Location: `~/fusion_mcp_comm/` directory (created at runtime)
- Contains: JSON command files (`command_*.json`) and response files (`response_*.json`)
- Depends on: File system, timestamp coordination
- Used by: Both MCP server and Fusion 360 add-in

**Fusion 360 Add-in:**
- Purpose: Execute commands directly against Fusion 360 API
- Location: `fusion-addin/FusionMCP.py`
- Contains: Command handler functions that interact with `adsk.fusion` and `adsk.core` APIs
- Depends on: Autodesk Fusion 360 Python API
- Used by: Fusion 360 application itself (runs in-process)

## Data Flow

**Create Simple Box Workflow:**

1. Claude receives user prompt: "Create a 5cm cube"
2. Claude determines tool sequence and calls MCP server:
   - `create_sketch(plane="XY")`
3. MCP server (`fusion360_mcp_server.py::send_fusion_command`):
   - Creates JSON: `{"type": "tool", "name": "create_sketch", "params": {"plane": "XY"}, "id": 1234567890123}`
   - Writes to `~/fusion_mcp_comm/command_1234567890123.json`
   - Enters polling loop: checks for `response_1234567890123.json` every 50ms for up to 900 iterations (45s)
4. Fusion 360 add-in (`fusion-addin/FusionMCP.py::monitor_commands`):
   - Background thread runs continuously
   - Detects command file every 100ms
   - Calls `execute_command()` which dispatches to `create_sketch()` handler
   - Handler uses `adsk.fusion` API to create sketch
   - Writes response: `{"success": true, "sketch_name": "Sketch1"}`
   - Writes to `~/fusion_mcp_comm/response_1234567890123.json`
   - Deletes command file
5. MCP server receives response:
   - Parses JSON response
   - Deletes response file
   - Returns result to Claude
6. Claude processes result and continues workflow

**Batch Operation Workflow (5-10x faster):**

1. Claude calls `batch([{commands...}])`
2. MCP server sends single command with `"type": "batch"` containing array of commands
3. Add-in processes all commands sequentially in single handler call
4. Returns array of results back in single response
5. Reduces round-trip latency from 5 separate requests to 1 request

**State Management:**
- Fusion 360 maintains state internally (active sketch, most recent body, component list)
- MCP server is stateless - does not cache Fusion state
- Commands target "most recent" objects by default (sketch, body, component)
- Explicit indices used when selecting specific objects (body_index, face_index, edge_index)
- No state synchronization between server and add-in required

## Key Abstractions

**Tool Pattern:**
- Purpose: Defines callable operations exposed to Claude
- Examples: `draw_rectangle()`, `extrude()`, `fillet()`, `move_component()`
- Pattern: Python function decorated with `@mcp.tool()` decorator
- Each tool validates parameters and calls `send_fusion_command()` with standardized JSON

**Command Handler Pattern:**
- Purpose: Execute a specific tool in Fusion 360 context
- Examples: `create_sketch()`, `draw_rectangle()`, `extrude_profile()`, `add_fillet()`
- Pattern: Standalone function in add-in code that takes params dict and returns success/error dict
- Directly uses `adsk.fusion` and `adsk.core` APIs

**Request/Response Protocol:**
- Purpose: Encode parameters and results across file system IPC
- Request format: `{"type": "tool", "name": "tool_name", "params": {...}, "id": timestamp}`
- Response format: `{"success": true/false, "error": "message", ...result_fields}`
- Timestamp used for file matching and prevents race conditions

## Entry Points

**MCP Server Entry Point:**
- Location: `mcp-server/fusion360_mcp_server.py::main`
- Triggers: `if __name__ == "__main__": mcp.run()`
- Responsibilities:
  - Initializes FastMCP server instance
  - Registers 50+ tool functions
  - Runs HTTP/stdio server listening for Claude Desktop connections
  - Handles tool invocation requests
  - Manages IPC polling and timeout logic

**Add-in Entry Point:**
- Location: `fusion-addin/FusionMCP.py::run(context)`
- Triggers: Fusion 360 starts add-in (manually enabled in Utilities → Add-Ins)
- Responsibilities:
  - Gets Fusion 360 application and UI objects
  - Creates `~/fusion_mcp_comm` directory
  - Starts background monitoring thread
  - Shows success message to user
  - Daemon thread runs indefinitely until `stop()` called

**Add-in Stop Entry Point:**
- Location: `fusion-addin/FusionMCP.py::stop(context)`
- Triggers: User disables add-in in Fusion 360
- Responsibilities:
  - Sets `stop_thread = True` flag
  - Background thread checks this flag and exits
  - Shows stop message to user

## Error Handling

**Strategy:** Fail-fast with informative error messages

**Patterns:**

1. **Server-Level Timeout:**
   - If response not received within 45 seconds, raise exception: "Timeout after 45s - is Fusion 360 running with FusionMCP add-in?"
   - Informs user that either Fusion 360 is not running or add-in is not started
   - Location: `fusion360_mcp_server.py::send_fusion_command()` (line 64)

2. **Add-in Command Execution Error:**
   - All `execute_command()` calls wrapped in try-except
   - Returns `{"success": false, "error": str(e)}` with traceback info
   - Errors silently caught and logged (no UI disruption from failed background operations)
   - Location: `fusion-addin/FusionMCP.py::execute_command()` (line 88)

3. **Precondition Validation:**
   - Many operations require prior state (e.g., "No sketches - call create_sketch first")
   - Checked before attempting Fusion API calls
   - Examples: `draw_circle()` requires active sketch, `extrude()` requires profiles
   - Location: Lines 103-125 in add-in code

4. **JSON Parsing Error:**
   - File I/O wrapped in try-except during command read/write
   - Silently catches and continues to next file
   - Location: `fusion-addin/FusionMCP.py::monitor_commands()` (lines 45-53)

5. **Response Success Check:**
   - Server checks `result.get("success")` before returning
   - If false, extracts error message and raises exception to Claude
   - Location: `fusion360_mcp_server.py::send_fusion_command()` (line 60-61)

## Cross-Cutting Concerns

**Logging:**
- Minimal logging; errors returned as JSON in response dict
- No centralized log files
- UI messages show success states (e.g., "Fusion MCP Started!")

**Validation:**
- Parameter validation implicit in tool docstrings
- Type hints not enforced at runtime
- Fusion API calls fail with exceptions if types incorrect

**Authentication:**
- Not applicable - local file system communication
- No network security concerns
- Any process with file system access can invoke commands

**Unit Conversion:**
- All coordinates and dimensions in centimeters
- Emphasis in documentation but no runtime conversion
- User responsible for correct conversion (common error source documented in docs/)

---

*Architecture analysis: 2026-03-13*
