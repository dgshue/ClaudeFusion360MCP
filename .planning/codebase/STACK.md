# Technology Stack

**Analysis Date:** 2026-03-13

## Languages

**Primary:**
- Python 3.10+ - Core MCP server and Fusion 360 add-in implementation

**Secondary:**
- JSON - Configuration and command/response serialization

## Runtime

**Environment:**
- Python 3.10 or later

**Package Manager:**
- pip
- Lockfile: Not detected

## Frameworks

**Core:**
- MCP (Model Context Protocol) - FastMCP - Framework for building Claude-compatible servers
  - Used in: `mcp-server/fusion360_mcp_server.py`
  - Version: Latest stable (installed via `pip install mcp`)

**Integration:**
- Autodesk Fusion 360 API - Python API for CAD operations
  - SDK imports: `adsk.core`, `adsk.fusion`
  - Used in: `fusion-addin/FusionMCP.py`
  - No pip package - ships with Fusion 360 installation

**Scripting/Add-in:**
- Fusion 360 Add-in Framework - Custom Python scripts run within Fusion 360
  - Configuration: `fusion-addin/FusionMCP.manifest`
  - Entry point: `fusion-addin/FusionMCP.py`

## Key Dependencies

**Critical:**
- `mcp` - Model Context Protocol framework for creating Claude-compatible tools
  - Purpose: Exposes Python functions as MCP tools callable by Claude Desktop
  - Import: `from mcp.server.fastmcp import FastMCP`

**Standard Library:**
- `json` - Command/response serialization (v7.2)
- `time` - Polling delays and timeouts (50ms polling)
- `pathlib.Path` - Cross-platform file I/O and home directory access
- `threading` - Background monitoring thread in add-in
- `traceback` - Error reporting
- `math` - Angle conversions (radians in Fusion API)

## Configuration

**Environment:**
- Not explicitly configured - uses defaults
- Communicates via file system at `~/fusion_mcp_comm/` directory
  - Created dynamically if missing: `COMM_DIR.mkdir(exist_ok=True)`

**Build:**
- No build system required
- Direct Python execution via `python fusion360_mcp_server.py`

**Runtime Configuration:**
- Claude Desktop config: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)
- Config entries must reference Python interpreter and server script path
- Paths must use forward slashes even on Windows

## Platform Requirements

**Development:**
- Python 3.10+
- Autodesk Fusion 360 (free for personal use, installed locally)
- Claude Desktop app with MCP support
- Windows or macOS (per `FusionMCP.manifest`: `supportedOS: "windows|mac"`)

**Production:**
- Same as development - runs locally with Fusion 360 desktop application
- No cloud deployment; communicates via local file system

## Add-in Manifest Configuration

**Location:** `fusion-addin/FusionMCP.manifest`

**Key settings:**
- `autodeskProduct`: "Fusion" - Target application
- `type`: "addin" - Fusion 360 add-in type
- `id`: "FusionMCP" - Unique identifier
- `version`: "2.0.0" - Add-in version
- `runOnStartup`: true - Automatically start with Fusion 360
- `supportedOS`: "windows|mac" - Cross-platform
- `editEnabled`: true - Code can be edited in Fusion 360 UI

## Communication Protocol

**File System Based:**
- Command files: `~/fusion_mcp_comm/command_{timestamp}.json`
- Response files: `~/fusion_mcp_comm/response_{timestamp}.json`
- Polling interval: 50ms (900 iterations = 45s timeout)
- No network communication - purely local file I/O

**Command Structure:**
```json
{
  "type": "tool",
  "name": "tool_name",
  "params": {...},
  "id": timestamp
}
```

**Response Structure:**
```json
{
  "success": true/false,
  "error": "error message if failed",
  "data": {...}
}
```

## Unit System

**CRITICAL:** All dimensions in centimeters, not millimeters
- 50 mm → 5.0
- 100 mm → 10.0
- 1 inch → 2.54

---

*Stack analysis: 2026-03-13*
