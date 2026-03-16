# Fusion 360 MCP Server

Control Autodesk Fusion 360 with Claude AI through the Model Context Protocol (MCP).

![Version](https://img.shields.io/badge/Version-0.5.0-blue)
![Fusion 360](https://img.shields.io/badge/Fusion%20360-2024+-orange)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What This Does

This MCP server lets Claude AI directly control Fusion 360 to:
- Create 3D sketches, extrusions, revolves, and sweeps
- Apply threads (cosmetic or modeled for 3D printing)
- Build multi-component assemblies with proper positioning
- Apply fillets, chamfers, shells, and patterns
- Export to STL, STEP, and 3MF formats
- Measure geometry and verify designs

**Example prompt:** *"Create a 50mm cube with 5mm rounded edges"* -- Claude creates it directly in Fusion 360.

---

## Quick Start (5 minutes)

### Prerequisites
- Autodesk Fusion 360 (free for personal use)
- Claude Desktop app with MCP support
- Python 3.10+ with `pip`

### Step 1: Install the MCP Server

```bash
# Install the MCP framework
pip install mcp

# Clone this repository (or download ZIP)
git clone https://github.com/dgshue/ClaudeFusion360MCP.git
cd ClaudeFusion360MCP
```

### Step 2: Install the Fusion 360 Add-in

1. Open Fusion 360
2. Go to **Utilities** > **ADD-INS** (or press `Shift+S`)
3. Click **Add-Ins** tab > **Green Plus (+)** button
4. Navigate to the `fusion-addin` folder from this repo
5. Select `FusionMCP` folder > Click **Open**
6. Check **Run on Startup** > Click **Run**

You should see: *"Fusion MCP Started! Listening at: C:\Users\...\fusion_mcp_comm"*

### Step 3: Configure Claude Desktop

Edit your Claude Desktop config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "python",
      "args": ["C:/path/to/ClaudeFusion360MCP/mcp-server/fusion360_mcp_server.py"]
    }
  }
}
```

> **Note:** Use forward slashes in the path, even on Windows.

### Step 4: Add the Skill File (Recommended)

For best results, create a **Claude Project** and paste the contents of [`docs/SKILL.md`](docs/SKILL.md) into the **Project Instructions**. This teaches Claude:
- Fusion 360 coordinate system rules
- Unit conventions (everything in centimeters!)
- Best practices for assemblies
- Common pitfalls to avoid

**For advanced spatial reasoning**, also include [`docs/SPATIAL_AWARENESS.md`](docs/SPATIAL_AWARENESS.md). This teaches Claude:
- How to verify geometry placement BEFORE operations
- Coordinate mapping between sketch planes and world space
- The critical Z-negation rule for XZ/YZ planes
- Pre/post operation verification protocols

### Step 5: Restart and Test

1. Restart Claude Desktop
2. Open Fusion 360 (ensure the add-in is running)
3. Ask Claude: *"Create a simple box that is 5cm x 3cm x 2cm"*

---

## How It Works

```
Claude Desktop  <-->  MCP Server  <-->  Fusion 360 Add-in
                      (Python)          (FusionMCP.py)
```

1. Claude sends commands via MCP protocol
2. MCP server writes command to `~/fusion_mcp_comm/command_*.json`
3. Fusion add-in polls for commands, executes them via Fusion API
4. Results written to `~/fusion_mcp_comm/response_*.json`
5. MCP server returns result to Claude

---

## Available Tools

| Category | Tools |
|----------|-------|
| **Sketching** | `create_sketch`, `draw_rectangle`, `draw_circle`, `draw_line`, `draw_arc`, `draw_polygon`, `draw_slot`, `draw_spline`, `draw_point`, `finish_sketch` |
| **Sketch Queries** | `get_sketch_info`, `get_sketch_profiles` |
| **Sketch Constraints** | `coincident`, `horizontal`, `vertical`, `tangent`, `perpendicular`, `parallel`, `equal`, `concentric` |
| **Sketch Dimensions** | `linear_dimension`, `angular_dimension`, `radial_dimension`, `diameter_dimension` |
| **Sketch Ops** | `offset_curves`, `trim_curves`, `extend_curves` |
| **3D Operations** | `extrude`, `revolve`, `sweep`, `loft`, `shell`, `draft` |
| **Threads & Holes** | `thread`, `query_threads`, `hole` |
| **Modifications** | `fillet`, `chamfer`, `combine`, `split_body` |
| **Patterns** | `pattern_rectangular`, `pattern_circular`, `mirror` |
| **Construction** | `construction_point`, `construction_plane`, `construction_axis` |
| **Components** | `create_component`, `move_component`, `rotate_component`, `list_components`, `delete_component`, `check_interference` |
| **Joints** | `rigid_joint`, `revolute_joint`, `slider_joint`, `cylindrical_joint`, `pin_slot_joint`, `ball_joint` |
| **Parametric** | `set_parameter`, `get_parameters`, `edit_at_timeline` |
| **Export/Import** | `export_stl`, `export_step`, `export_3mf`, `import_mesh` |
| **Inspection** | `get_design_info`, `get_body_info`, `measure`, `fit_view` |
| **Utility** | `undo`, `delete_body`, `delete_sketch`, `batch_operations` |

See [`docs/TOOL_REFERENCE.md`](docs/TOOL_REFERENCE.md) for the complete API reference with parameters and examples.

---

## Important: Units Are in Centimeters!

> **All dimensions in the MCP are in CENTIMETERS**, not millimeters.

| You Want | You Enter |
|----------|-----------|
| 50 mm | `5.0` |
| 100 mm | `10.0` |
| 1 inch | `2.54` |

This is the most common source of errors. A value of `50` means 50 cm (half a meter)!

---

## Project Structure

```
ClaudeFusion360MCP/
├── README.md
├── LICENSE
├── mcp-server/
│   ├── fusion360_mcp_server.py    # MCP server (run by Claude Desktop)
│   └── resources/                 # MCP resource guides
├── fusion-addin/
│   ├── FusionMCP.py               # Fusion 360 add-in (hot-reload enabled)
│   ├── FusionMCP.manifest         # Add-in manifest
│   ├── handlers/                  # 79 tool handlers across 12 modules
│   └── helpers/                   # Shared utilities (coordinates, errors, selection)
└── docs/
    ├── SKILL.md                   # Claude Project instructions
    ├── SPATIAL_AWARENESS.md       # 3D coordinate system and verification
    ├── TOOL_REFERENCE.md          # Complete API reference (79 tools)
    └── KNOWN_ISSUES.md            # Common pitfalls and solutions
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`TOOL_REFERENCE.md`](docs/TOOL_REFERENCE.md) | Complete API reference for all 79 tools with parameters, examples, and return values |
| [`KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) | 16 documented pitfalls with root causes and solutions |
| [`SKILL.md`](docs/SKILL.md) | Claude Project instructions -- paste into Project settings for best results |
| [`SPATIAL_AWARENESS.md`](docs/SPATIAL_AWARENESS.md) | Coordinate system rules, XZ plane inversion, verification protocols |

---

## Troubleshooting

### "Timeout after 45s" Error
- Fusion 360 is not running, OR the FusionMCP add-in is not started
- **Fix:** Open Fusion 360 > Utilities > Add-Ins > Run FusionMCP

### Claude doesn't see the Fusion 360 tools
- MCP server path is wrong in config, or Python can't find the `mcp` package
- **Fix:** Verify path uses forward slashes, run `pip install mcp`

### Dimensions are way too big/small
- You're using millimeters instead of centimeters
- **Fix:** Divide all mm values by 10

### Code changes not taking effect after editing add-in files
- Python caches modules in memory even after clearing `__pycache__`
- **Fix (v0.5.0+):** Toggle the add-in off/on in Fusion (Shift+S > Add-Ins). No full restart needed.
- **Fix (before v0.5.0):** Fully restart Fusion 360.

### Add-in won't install
- Folder structure is wrong
- **Fix:** The add-in folder must contain both `.py` and `.manifest` files

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## License

MIT License - see LICENSE file.

---

## Credits

- MCP Server & Add-in developed with Claude AI (Anthropic)
- Uses the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- Built for [Autodesk Fusion 360](https://www.autodesk.com/products/fusion-360/)
