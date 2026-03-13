# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**Autodesk Fusion 360:**
- What it's used for: Complete 3D CAD modeling, sketching, assembly, feature operations, and export
  - SDK/Client: `adsk.core`, `adsk.fusion` - Autodesk native Python API
  - Auth: None required - uses local Fusion 360 session authentication
  - Location: `fusion-addin/FusionMCP.py`
  - Communication: Direct object model calls via Fusion 360 process

**Claude Desktop (via MCP):**
- What it's used for: Receives tool calls from Claude AI, executes Fusion 360 operations, returns results
  - SDK/Client: `mcp.server.fastmcp` - MCP framework
  - Auth: None - local IPC protocol
  - Location: `mcp-server/fusion360_mcp_server.py`
  - Communication: JSON-based command/response protocol via file system

## Data Storage

**File Storage:**
- **Type:** Local filesystem only
- **Usage:** Command/response communication between MCP server and Fusion 360 add-in
- **Location:** `~/fusion_mcp_comm/` directory
- **File format:** JSON
- **Lifecycle:** Temporary command files deleted after response received
  - Command file: `command_{timestamp}.json`
  - Response file: `response_{timestamp}.json`

**Databases:**
- None used - application is stateless
- All state managed by Fusion 360's active design document

**File Import/Export:**
- STL format - `export_stl()` in `mcp-server/fusion360_mcp_server.py:599`
- STEP format - `export_step()` in `mcp-server/fusion360_mcp_server.py:604`
- 3MF format - `export_3mf()` in `mcp-server/fusion360_mcp_server.py:609`
- Mesh import - `import_mesh()` supports STL, OBJ, 3MF in `mcp-server/fusion360_mcp_server.py:618`

## Authentication & Identity

**Auth Provider:**
- None for MCP/Claude communication
- Fusion 360 add-in: Uses Fusion 360's built-in session (no explicit auth required)

## Monitoring & Observability

**Error Tracking:**
- None detected - local error handling only

**Logs:**
- Fusion 360 add-in: Writes to UI message boxes via `ui.messageBox()`
  - Startup message: `'Fusion MCP Started!\n\nListening at:\n' + str(COMM_DIR)`
  - Errors reported via exception traceback display
  - Location: `fusion-addin/FusionMCP.py:25, 35, 89`

**Standard Output:**
- MCP server writes JSON responses to response files
- Error messages in JSON response `{"success": false, "error": "..."}`

## CI/CD & Deployment

**Hosting:**
- Local desktop application - no server deployment
- Runs within Fusion 360 process (add-in)
- MCP server runs as subprocess started by Claude Desktop

**CI Pipeline:**
- None detected - purely local development

**Installation Process:**
1. `pip install mcp` - Install MCP framework
2. Clone repository
3. Install add-in to Fusion 360 (manual via GUI: Utilities → Add-Ins → FusionMCP folder)
4. Update Claude Desktop config file with server path
5. Restart Claude Desktop

## Environment Configuration

**Required env vars:**
- None explicitly required
- Uses default home directory: `Path.home() / "fusion_mcp_comm"`

**Secrets location:**
- No secrets managed by application
- Fusion 360 authentication is handled by Fusion 360 itself

**Configuration files:**
- Claude Desktop: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- Fusion 360 add-in manifest: `fusion-addin/FusionMCP.manifest`

**Required configuration in Claude Desktop config:**
```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python",
      "args": ["C:/path/to/fusion360-mcp/mcp-server/fusion360_mcp_server.py"]
    }
  }
}
```

## Webhooks & Callbacks

**Incoming:**
- No webhook endpoints - application is request/response only

**Outgoing:**
- None detected

## Communication Flow

**MCP Server → Add-in Communication:**
1. Claude calls MCP tool via `@mcp.tool()` decorator
2. `send_fusion_command()` in `mcp-server/fusion360_mcp_server.py:40` creates command JSON
3. Command written to `~/fusion_mcp_comm/command_{timestamp}.json`
4. MCP server polls for response file every 50ms (45s timeout)
5. Add-in's monitor thread (`fusion-addin/FusionMCP.py:39`) detects command file
6. Executes via `execute_command()` and Fusion 360 API calls
7. Response written to `~/fusion_mcp_comm/response_{timestamp}.json`
8. MCP server reads response, returns result to Claude
9. Both command and response files deleted

**Timeout:** 900 iterations × 50ms = 45 seconds max wait time

## Supported Export/Import

**Export operations:**
- `export_stl(filepath)` - 3D printing format
- `export_step(filepath)` - CAD standard format
- `export_3mf(filepath)` - Modern 3D printing format

**Import operations:**
- `import_mesh(filepath, unit)` - Supports STL, OBJ, 3MF
  - Unit options: "mm", "cm", or "in"
  - File is converted to Fusion 360 body

## Measurement & Inspection

**Geometry inspection:**
- `measure(type, body_index, edge_index, face_index)` - Get dimensions
  - Returns volume, surface_area, bounding_box for bodies
  - Returns length for edges
  - Returns area for faces

## Design Querying

**Design information:**
- `get_design_info()` - Returns design name, body count, sketch count, component count
- `get_body_info(body_index)` - Returns detailed body info with edge and face indices
- `list_components()` - Returns all components with names, positions, bounding boxes

---

*Integration audit: 2026-03-13*
