# Technology Stack

**Project:** ClaudeFusion360MCP
**Researched:** 2026-03-13

## Recommended Stack

### MCP Server Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.10+ | MCP server runtime | Minimum required by both `mcp` and `fastmcp` packages. The MCP server runs outside Fusion 360 so it can use any modern Python. | HIGH |
| `mcp` (official SDK) | 1.26.0 | MCP protocol implementation | The project already uses `from mcp.server.fastmcp import FastMCP` which ships inside the official `mcp` package. This is the right choice -- it provides the FastMCP decorator API without pulling in the separate standalone `fastmcp` package. Upgrading from the current implicit version to 1.26.0 gets stdio/SSE transport improvements and better tool schema generation. | HIGH |

**Do NOT switch to standalone `fastmcp` 3.x.** The standalone `fastmcp` package (v3.1.0 from PyPI) is a separate project by Prefect/jlowin that has diverged from the SDK-bundled version. The project currently imports `from mcp.server.fastmcp import FastMCP` (the SDK-bundled version), which is simpler, has no extra dependencies, and is fully sufficient for this use case. Switching would require changing all imports and adds unnecessary dependency surface. Keep the SDK-bundled FastMCP.

### Fusion 360 Add-in Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| CPython (embedded) | 3.12.4 | Fusion 360's built-in Python interpreter | Ships with Fusion 360; cannot be changed. All add-in code must be compatible with 3.12.4. This was upgraded from 3.9.7 in a recent Fusion release. | HIGH |
| `adsk.core` | Ships with Fusion 360 | Application framework, UI, ValueInput, Points, Vectors | No version choice -- use whatever ships with installed Fusion 360. | HIGH |
| `adsk.fusion` | Ships with Fusion 360 | All CAD operations: sketches, features, components, joints | The entire modeling API. No alternative exists. | HIGH |

### Communication Layer

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| File-system IPC | N/A | Command/response transport between MCP server and add-in | Already proven in this project. JSON files in `~/fusion_mcp_comm/`. Simple, debuggable, no network stack. The add-in runs inside Fusion's process and cannot easily host an HTTP server. Other Fusion MCP projects (AuraFriday, ArchimedesCrypto) also use file-based IPC for the same reason. Keep it. | HIGH |
| JSON | N/A | Serialization format | Standard library `json` module on both sides. No need for msgpack/protobuf -- command payloads are small (< 1KB typically). | HIGH |

### Development Tools

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| VS Code | Latest | Development IDE | Fusion 360 has built-in VS Code debugging support for Python add-ins (auto-installs `ms-python.python` extension). Use it for both server and add-in development. | HIGH |
| `uv` | Latest | Python package manager | Faster than pip, better dependency resolution, reproducible installs. Use for the MCP server side (the add-in uses Fusion's embedded Python and has no pip). | MEDIUM |
| `mypy` or `pyright` | Latest | Type checking | The Fusion 360 API has type stubs. Type checking catches parameter errors before runtime, which matters because add-in errors are hard to debug (they happen inside Fusion's process). | MEDIUM |

### Supporting Libraries (MCP Server Side Only)

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `pydantic` | 2.x (ships with `mcp`) | Parameter validation | Already a transitive dependency of the `mcp` package. Use Pydantic models for complex tool parameters (e.g., batch commands, joint definitions) to get automatic validation and schema generation in MCP tool descriptions. | HIGH |
| `pathlib` | stdlib | File path handling | Already in use. Continue using for all file operations. | HIGH |
| `math` | stdlib | Angle conversions, geometry calculations | Already in use. Fusion API uses radians internally. | HIGH |

### Libraries NOT Needed

| Library | Why Not |
|---------|---------|
| `fastmcp` (standalone, v3.x) | The SDK-bundled `mcp.server.fastmcp` is sufficient. Standalone adds complexity, different API surface, and unnecessary dependencies for this project's needs. |
| `asyncio` / `aiofiles` | The MCP server's communication is inherently synchronous (write file, poll for response). Adding async would complicate the code without benefit since Fusion 360 processes commands sequentially anyway. |
| `requests` / `httpx` | No HTTP communication. File-system IPC is the transport. |
| `SQLite` / any database | No persistent state needed. Fusion 360 maintains all design state. |
| `logging` (elaborate setup) | Keep error reporting simple via JSON responses. Add basic `logging` module usage for the MCP server's own debug output, but don't over-engineer it. |
| `pytest` | Testing against Fusion 360's API requires Fusion 360 running. Unit tests for the MCP server parameter validation are useful but the add-in handlers cannot be tested outside Fusion. Manual testing via Claude is the primary validation path. |

## Fusion 360 API Surface (What to Use)

This is the critical "stack" for the add-in side. These are not installable libraries but API namespaces that must be understood for implementation.

### Sketch API (`adsk.fusion.Sketch`)

| API Object | Key Methods | Purpose |
|------------|-------------|---------|
| `SketchCurves` | `.sketchLines`, `.sketchCircles`, `.sketchArcs`, `.sketchEllipses`, `.sketchFittedSplines` | All curve creation |
| `SketchPoints` | `.add()` | Point creation for splines and construction |
| `GeometricConstraints` | `addCoincident`, `addParallel`, `addPerpendicular`, `addTangent`, `addEqual`, `addHorizontal`, `addVertical`, `addConcentric`, `addCollinear`, `addMidPoint`, `addSymmetry`, `addSmooth`, `addOffset2` | 23 constraint types total |
| `SketchDimensions` | `addDistanceDimension`, `addRadialDimension`, `addDiameterDimension`, `addAngularDimension`, `addConcentricCircleDimension`, `addOffsetDimension`, `addEllipseMajorRadiusDimension`, `addEllipseMinorRadiusDimension` | Parametric dimensioning |
| `SketchTexts` | `.add()` | Text in sketches |
| Sketch methods | `importSVG`, `project2`, `offset`, `findConnectedCurves`, `setConstructionState` | Utility operations |

### 3D Feature API (`adsk.fusion`)

| API Object | Key Methods | Purpose |
|------------|-------------|---------|
| `ExtrudeFeatures` | `.addSimple()`, `.createInput()` + `.add()` | Extrusion (already partially implemented) |
| `RevolveFeatures` | `.createInput()` + `.add()` | Revolution (already partially implemented) |
| `SweepFeatures` | `.createInput()` + `.add()` | Sweep along path |
| `LoftFeatures` | `.createInput()` + `.add()` | Loft between profiles |
| `HoleFeatures` | `.createInput()` + `.add()` | Holes (simple, counterbore, countersink) |
| `ThreadFeatures` | `.createInput()` + `.add()` | Thread creation |
| `RibFeatures` | `.createInput()` + `.add()` | Structural ribs |
| `WebFeatures` | `.createInput()` + `.add()` | Web features |
| `CoilFeatures` | `.createInput()` + `.add()` | Springs and coils |
| `EmbossFeatures` | `.createInput()` + `.add()` | Surface embossing |
| `FilletFeatures` | `.createInput()` + `.add()` | Fillets (already partially implemented) |
| `ChamferFeatures` | `.createInput()` + `.add()` | Chamfers |
| `ShellFeatures` | `.createInput()` + `.add()` | Shell/hollow |
| `DraftFeatures` | `.createInput()` + `.add()` | Draft angles |
| `RectangularPatternFeatures` | `.createInput()` + `.add()` | Linear patterns |
| `CircularPatternFeatures` | `.createInput()` + `.add()` | Circular patterns |
| `MirrorFeatures` | `.createInput()` + `.add()` | Mirror operations |

### Assembly/Joint API (`adsk.fusion`)

| API Object | Key Methods | Purpose |
|------------|-------------|---------|
| `Occurrences` | `.addNewComponent()`, `.addByInsert()` | Component creation |
| `JointOrigins` | `.createInput()` + `.add()` | Joint origin definition |
| `Joints` | `.createInput()` + `.add()` | Joint creation (rigid, revolute, slider, cylindrical, pin-slot, planar, ball) |
| `AsBuiltJoints` | `.createInput()` + `.add()` | As-built joint creation |
| `JointMotion` | `.rotationValue`, `.slideValue` | Drive joint positions |
| `InterferenceInput` | `.createInput()` + `.checkInterference()` | Collision detection |

### Measurement API

| API Object | Key Methods | Purpose |
|------------|-------------|---------|
| `MeasureManager` | `.measureMinimumDistance()`, `.measureAngle()`, `.measurePosition()` | Distance, angle, position measurement |
| `BRepBody` | `.physicalProperties` | Volume, area, center of mass |

## Architecture Implications for Stack

### Two Python Runtimes -- Critical Constraint

The MCP server runs in a system Python (3.10+), while the add-in runs in Fusion 360's embedded Python (3.12.4). These are separate processes. This means:

1. **No shared libraries** -- the add-in cannot import `mcp` or `pydantic`. It only has access to `adsk.*` and Python stdlib.
2. **No shared state** -- all communication goes through JSON files. Objects cannot be passed by reference.
3. **No pip in Fusion** -- the add-in cannot install packages. Everything must use stdlib or `adsk.*`.

### ValueInput Pattern -- Use It

Many Fusion 360 API methods require `adsk.core.ValueInput` rather than raw numbers. The pattern is:

```python
value = adsk.core.ValueInput.createByReal(distance_in_cm)
# or for expressions:
value = adsk.core.ValueInput.createByString("5 mm")
```

Use `createByReal` consistently since all dimensions are in centimeters (the project's established convention).

### ObjectCollection Pattern -- Required for Multi-Select

Operations like patterns, lofts, and multi-edge fillets require `adsk.core.ObjectCollection`:

```python
edges = adsk.core.ObjectCollection.create()
edges.add(edge1)
edges.add(edge2)
```

### Thread-Safety -- Critical for Add-in

The add-in's monitoring thread reads commands but Fusion 360 API calls must happen on Fusion's main thread. The current code works because Fusion's Python API handles thread marshaling internally for simple operations, but complex multi-step operations (like creating a loft with guide rails) should be wrapped carefully. Use `app.activeProduct` access as the thread-safety checkpoint.

## Installation

```bash
# MCP Server (system Python)
pip install mcp>=1.26.0

# Or with uv (recommended)
uv pip install mcp>=1.26.0

# No installation needed for add-in -- copy to Fusion 360 add-ins directory:
# Windows: %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\FusionMCP\
# macOS:   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/FusionMCP/
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| MCP framework | `mcp` SDK (bundled FastMCP) | Standalone `fastmcp` 3.x | Adds unnecessary dependency; current import pattern works fine |
| Transport | File-system IPC | HTTP/WebSocket | Add-in cannot easily host HTTP server inside Fusion's process |
| Serialization | JSON (stdlib) | MessagePack, Protobuf | Over-engineering; payloads are tiny, human-readability aids debugging |
| Package mgmt | `uv` | `pip` | `pip` works but `uv` is faster; either is fine |
| Add-in language | Python | C++ | Python is simpler, sufficient for all needed operations, matches existing codebase |

## Version Compatibility Matrix

| Component | Min Version | Tested Version | Notes |
|-----------|-------------|----------------|-------|
| Python (MCP server) | 3.10 | 3.12+ | Required by `mcp` package |
| Python (Fusion add-in) | 3.12.4 | 3.12.4 | Embedded in Fusion 360, not configurable |
| `mcp` package | 1.26.0 | 1.26.0 | Latest stable |
| Fusion 360 | Latest | Latest | API surface evolves; use current release |
| Claude Desktop | Latest | Latest | MCP client |

## Sources

- [mcp on PyPI](https://pypi.org/project/mcp/) -- version 1.26.0, Jan 2026
- [fastmcp on PyPI](https://pypi.org/project/fastmcp/) -- version 3.1.0, Mar 2026 (NOT recommended for this project)
- [Fusion 360 Python 3.12.4 upgrade](https://github.com/cryinkfly/Autodesk-Fusion-360-for-Linux/issues/490)
- [Fusion 360 API Reference](http://autodeskfusion360.github.io/)
- [GeometricConstraints API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GeometricConstraints.htm)
- [Sketch Object API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch.htm)
- [SketchFittedSpline API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchFittedSpline.htm)
- [FastMCP vs MCP SDK discussion](https://github.com/modelcontextprotocol/python-sdk/issues/1068)
- [Fusion 360 MCP implementations](https://github.com/AuraFriday/Fusion-360-MCP-Server) -- reference architecture
- [Fusion 360 API What's New](https://help.autodesk.com/view/fusion360/ENU/?contextId=APIWhatsNew)

---

*Stack research: 2026-03-13*
