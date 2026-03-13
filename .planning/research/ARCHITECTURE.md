# Architecture Patterns

**Domain:** Fusion 360 MCP Server (CAD automation via AI)
**Researched:** 2026-03-13

## Recommended Architecture

### Overview

Keep the current two-process, file-IPC architecture but reorganize both sides internally to handle 100+ tool handlers without becoming unmaintainable. The key insight: the MCP server side is already well-structured (one decorated function per tool), so the scaling problem is primarily in the **add-in's dispatch and handler organization**. The secondary challenge is **discoverability** -- helping AI models find and correctly use tools without trial and error.

```
Claude Desktop
    |
    | (MCP protocol - stdio)
    |
MCP Server (Python process)
    |-- Tools (~100+ @mcp.tool functions)
    |-- Resources (@mcp.resource - API reference, tutorials)
    |-- Prompts (@mcp.prompt - workflow templates)
    |
    | (File-system IPC - JSON in ~/fusion_mcp_comm/)
    |
Fusion 360 Add-in (runs inside Fusion process)
    |-- Command Router (single dispatch point)
    |-- Handler Modules (grouped by domain)
         |-- sketch_handlers.py
         |-- feature_handlers.py
         |-- assembly_handlers.py
         |-- query_handlers.py
         |-- utility_handlers.py
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| MCP Server - Tool Layer | Define tool signatures, docstrings, parameter validation; forward to IPC | Claude via MCP protocol, Add-in via file IPC |
| MCP Server - Resource Layer | Serve API reference docs, parameter guides, workflow tutorials as read-only data | Claude via MCP protocol (no IPC needed) |
| MCP Server - Prompt Layer | Provide workflow templates (e.g., "design a box with lid", "create gear") | Claude via MCP protocol (no IPC needed) |
| MCP Server - IPC Bridge | `send_fusion_command()` -- serialize, write, poll, deserialize | File system |
| Fusion Add-in - Router | `execute_command()` -- dispatch tool_name to correct handler module | Handler modules |
| Fusion Add-in - Sketch Handlers | Create sketches, draw geometry, apply constraints, manage dimensions | Fusion 360 API (`adsk.fusion`) |
| Fusion Add-in - Feature Handlers | Extrude, revolve, sweep, loft, hole, thread, fillet, chamfer, shell, draft, patterns | Fusion 360 API |
| Fusion Add-in - Assembly Handlers | Components, joints, motion, interference checking | Fusion 360 API |
| Fusion Add-in - Query Handlers | get_design_info, get_body_info, measure, list_components | Fusion 360 API |
| Fusion Add-in - Utility Handlers | Undo, delete, export, import, fit_view | Fusion 360 API |

### Data Flow

**Tool Invocation (standard path):**

```
Claude --> MCP Server --> JSON file in ~/fusion_mcp_comm/ --> Add-in reads file
  --> Router dispatches to handler --> Handler calls adsk.fusion API
  --> Handler returns result dict --> Add-in writes response JSON
  --> MCP Server polls and reads response --> Returns to Claude
```

**Resource Read (no IPC -- server-side only):**

```
Claude --> MCP Server --> @mcp.resource function executes
  --> Returns markdown/JSON content directly --> Claude receives data
```

**Prompt Request (no IPC -- server-side only):**

```
Claude --> MCP Server --> @mcp.prompt function executes
  --> Returns message template --> Claude uses as conversation guidance
```

**Batch Operation (optimized path):**

```
Claude --> MCP Server batch() --> Single JSON with command array
  --> Add-in processes all commands sequentially in one round-trip
  --> Returns array of results --> MCP Server returns to Claude
```

## Patterns to Follow

### Pattern 1: Domain-Grouped Handler Modules (Add-in Side)

**What:** Split the monolithic `FusionMCP.py` into handler modules grouped by Fusion 360 domain. Each module contains related handler functions.

**When:** Now. The current 9-handler if/elif chain in `execute_command()` will become unreadable at 50+ handlers.

**Why this over a registry/decorator pattern:** The add-in runs inside Fusion 360's embedded Python interpreter, which has constraints. Keep it simple -- plain Python modules with functions, imported and registered in a dict. No metaclasses, no decorators, no dynamic discovery. A flat dict lookup is faster and clearer than a long if/elif chain.

**Example:**

```python
# fusion-addin/handlers/sketch_handlers.py
def create_sketch(design, rootComp, params):
    plane_name = params.get('plane', 'XY')
    # ... implementation
    return {"success": True, "sketch_name": sketch.name}

def draw_circle(design, rootComp, params):
    # ... implementation
    return {"success": True}

def draw_line(design, rootComp, params):
    # ... implementation
    return {"success": True}

# All handlers in this module
HANDLERS = {
    "create_sketch": create_sketch,
    "draw_circle": draw_circle,
    "draw_line": draw_line,
    "draw_arc": draw_arc,
    "draw_polygon": draw_polygon,
    "draw_rectangle": draw_rectangle,
    "draw_spline": draw_spline,
}
```

```python
# fusion-addin/FusionMCP.py (router)
from handlers.sketch_handlers import HANDLERS as SKETCH_HANDLERS
from handlers.feature_handlers import HANDLERS as FEATURE_HANDLERS
from handlers.assembly_handlers import HANDLERS as ASSEMBLY_HANDLERS
from handlers.query_handlers import HANDLERS as QUERY_HANDLERS
from handlers.utility_handlers import HANDLERS as UTILITY_HANDLERS

TOOL_REGISTRY = {}
TOOL_REGISTRY.update(SKETCH_HANDLERS)
TOOL_REGISTRY.update(FEATURE_HANDLERS)
TOOL_REGISTRY.update(ASSEMBLY_HANDLERS)
TOOL_REGISTRY.update(QUERY_HANDLERS)
TOOL_REGISTRY.update(UTILITY_HANDLERS)

def execute_command(command):
    tool_name = command.get('name')
    params = command.get('params', {})
    handler = TOOL_REGISTRY.get(tool_name)
    if handler is None:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    try:
        design = app.activeProduct
        rootComp = design.rootComponent
        return handler(design, rootComp, params)
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
```

### Pattern 2: MCP Resources for Discoverability

**What:** Use `@mcp.resource` decorators to expose API reference documentation, parameter guides, and workflow tutorials as read-only data that Claude can request on demand.

**When:** After core tools work. Resources are the second layer of discoverability (first layer = tool docstrings).

**Why Resources instead of cramming everything into tool docstrings:** Tool descriptions should be concise (LLMs perform better with focused context). Resources provide deep reference that Claude can pull when needed, without bloating every tool call.

**Example:**

```python
# In MCP server
@mcp.resource("fusion://tools/sketch")
def sketch_tools_reference() -> str:
    """Complete reference for all sketch tools with examples."""
    return """
    # Sketch Tools Reference

    ## create_sketch
    Creates a new sketch on a construction plane.
    - plane: "XY" (top/bottom), "XZ" (front/back), "YZ" (left/right)
    - offset: Distance from origin in cm (default 0)

    ## draw_rectangle
    ...

    ## Workflow: Creating a profile for extrusion
    1. create_sketch(plane="XY")
    2. draw_rectangle(x1=-2.5, y1=-2.5, x2=2.5, y2=2.5)
    3. extrude(distance=5)
    """

@mcp.resource("fusion://guides/{topic}")
def workflow_guide(topic: str) -> str:
    """Workflow guides for common CAD tasks."""
    guides = {
        "box-with-lid": "...",
        "gear": "...",
        "enclosure": "...",
    }
    return guides.get(topic, f"No guide found for: {topic}")

@mcp.resource("fusion://coordinate-system")
def coordinate_system_reference() -> str:
    """Fusion 360 coordinate system rules including XZ plane inversion."""
    return """
    # Coordinate System
    - All units: centimeters (cm)
    - XZ plane: Y values are NEGATED (Autodesk design decision)
    - Always verify orientation with get_design_info() after sketch creation
    """
```

### Pattern 3: MCP Prompts for Workflow Templates

**What:** Use `@mcp.prompt` to provide pre-built workflow sequences that Claude can follow for common CAD tasks.

**When:** After resources are in place. Prompts are the highest-level discoverability layer.

**Example:**

```python
@mcp.prompt
def design_enclosure(width: float, height: float, depth: float, wall_thickness: float) -> str:
    """Guide for designing a hollow enclosure with lid."""
    return f"""Design an enclosure with these dimensions:
    - Width: {width}cm, Height: {height}cm, Depth: {depth}cm
    - Wall thickness: {wall_thickness}cm

    Steps:
    1. Create base box: create_sketch(plane="XY"), draw_rectangle, extrude
    2. Shell the box: shell(thickness={wall_thickness}, faces_to_remove=[top_face])
    3. Create lid as separate component
    4. Add alignment features (lips/grooves)
    5. Verify with measure() and check_interference()
    """
```

### Pattern 4: Consistent Handler Signature

**What:** Every handler function takes `(design, rootComp, params)` and returns a dict with `success` key. No exceptions to this pattern.

**When:** From the start. This is already the pattern in the existing 9 handlers.

**Why:** Uniform interface means the router never needs special cases. New handlers are trivially pluggable.

```python
# Every handler follows this contract:
def handler_name(design, rootComp, params) -> dict:
    """
    Args:
        design: adsk.fusion.Design - the active design
        rootComp: adsk.fusion.Component - root component
        params: dict - tool parameters from MCP

    Returns:
        {"success": True, ...result_fields} on success
        {"success": False, "error": "message"} on failure
    """
```

### Pattern 5: Server-Side Tool Grouping via Sections

**What:** Organize the MCP server's tool definitions into logical file sections or separate modules. The current single-file approach with comment-delimited sections works up to ~40-50 tools. Beyond that, split into modules.

**When:** When the server exceeds ~50 tool definitions. Currently at 39, so this is approaching.

**Two approaches depending on scale:**

**Option A (50-80 tools): Keep single file, use clear section headers** -- This is the current approach and works fine for the near term.

**Option B (80+ tools): Split into tool modules:**

```python
# mcp-server/tools/sketch_tools.py
from mcp_server.core import mcp, send_fusion_command

@mcp.tool()
def create_sketch(plane: str, offset: float = 0) -> dict:
    """Create a new sketch..."""
    return send_fusion_command("create_sketch", {"plane": plane, "offset": offset})

# mcp-server/fusion360_mcp_server.py (main)
from tools import sketch_tools, feature_tools, assembly_tools  # registers tools via import
```

**Recommendation:** Start with Option A. Only refactor to Option B if the file becomes genuinely hard to navigate. The current comment-section approach is readable.

## Anti-Patterns to Avoid

### Anti-Pattern 1: One Tool Per API Endpoint

**What:** Creating an MCP tool for every single Fusion 360 API method (e.g., `addByCenterRadius`, `addByThreePoints` as separate tools).

**Why bad:** Block's engineering team found that 30+ granular tools confuse LLMs during tool selection. LLMs perform better with fewer, more capable tools with clear parameters.

**Instead:** Group related operations. For example, a single `draw_arc` tool with a `method` parameter ("center_radius", "three_point", "tangent") rather than three separate tools. Keep the tool count manageable (aim for 60-80 well-designed tools rather than 150+ granular ones).

### Anti-Pattern 2: Stateful Server

**What:** Caching Fusion 360 state in the MCP server (e.g., tracking which sketch is active, counting bodies).

**Why bad:** The server and add-in communicate asynchronously. Cached state will drift from reality when the user manually modifies the design in Fusion's GUI.

**Instead:** Keep the server stateless. Always query current state from the add-in via `get_design_info()`, `get_body_info()`, etc.

### Anti-Pattern 3: Dynamic Tool Registration

**What:** Using metaprogramming or config files to dynamically generate MCP tool definitions at runtime.

**Why bad:** Tool definitions are also documentation. LLMs need rich, human-written docstrings with examples. Auto-generated descriptions are worse than hand-crafted ones. Also makes the codebase harder to grep and understand.

**Instead:** Write each tool definition explicitly with a thoughtful docstring. The MCP tool definition IS the documentation.

### Anti-Pattern 4: Deep Abstraction Layers in the Add-in

**What:** Creating OOP hierarchies, abstract base classes, or command pattern frameworks in the Fusion 360 add-in.

**Why bad:** The add-in runs in Fusion's embedded Python. Debugging is difficult (no debugger attachment). Simple functions with flat control flow are dramatically easier to troubleshoot via error messages. The PROJECT.md explicitly calls for simplicity.

**Instead:** Plain functions in modules. Dict-based dispatch. No inheritance. No abstract classes.

### Anti-Pattern 5: Mixing Read and Write in One Tool

**What:** A tool that both queries state AND modifies the design (e.g., `auto_fillet` that finds edges and fillets them).

**Why bad:** Makes it hard for the AI to reason about side effects. Tools that mix reads and writes violate the principle of least surprise and make error recovery harder.

**Instead:** Separate query tools (get_body_info to find edges) from mutation tools (fillet to apply fillets). Let the AI chain them.

## Scalability Considerations

| Concern | Current (9 tools) | At 50 tools | At 100+ tools |
|---------|-------------------|-------------|---------------|
| Add-in dispatch | if/elif chain | Dict lookup (required) | Dict lookup + handler modules (required) |
| MCP server file | Single file, sections | Single file still OK | Consider splitting into tool modules |
| Tool discoverability | Tool docstrings only | Add resources for reference | Resources + prompts + tool categories |
| Batch performance | Works fine | Works fine | May need parallel execution or chunking |
| File IPC | No issues | No issues | No issues (one file per command) |
| Handler testing | Manual only | Need structured test patterns | Need automated smoke tests |

## MCP Primitives Usage Plan

The MCP protocol provides three primitives. Use all three strategically:

| Primitive | Purpose in This Project | Count Estimate |
|-----------|------------------------|----------------|
| **Tools** | Callable operations that modify or query Fusion 360 | 60-80 tools |
| **Resources** | Read-only reference docs (tool guides, coordinate rules, API reference) | 10-15 resources |
| **Prompts** | Workflow templates for common CAD tasks | 5-10 prompts |

**Resource categories to implement:**
- `fusion://tools/{category}` -- Reference docs per tool group (sketch, features, assembly, etc.)
- `fusion://guides/{topic}` -- Step-by-step workflow guides
- `fusion://coordinate-system` -- Coordinate system rules and XZ plane inversion
- `fusion://units` -- Unit conversion reference
- `fusion://examples/{name}` -- Complete example workflows

**Prompt categories to implement:**
- Common shapes (box, cylinder, enclosure, gear)
- Assembly patterns (lid/base, hinge, snap-fit)
- Workflow sequences (sketch-extrude-fillet, multi-body boolean)

## Suggested Build Order

Dependencies flow top-to-bottom. Each step enables the next.

```
1. Add-in Restructure (handler modules + dict dispatch)
   |-- No new features, just reorganize existing 9 handlers
   |-- Enables: all subsequent handler additions
   |
2. Fix Existing Bugs (fillet edge selection, error handling, batch errors)
   |-- Quality foundation before adding more tools
   |-- Enables: reliable base for new handlers
   |
3. Implement Sketch Handlers (draw_line, draw_arc, draw_polygon, spline, constraints)
   |-- Sketches are prerequisite for all 3D features
   |-- Enables: sweep (needs path), loft (needs profiles)
   |
4. Implement Feature Handlers (shell, draft, patterns, mirror, sweep, loft, hole, thread)
   |-- Core 3D operations, most requested features
   |-- Depends on: working sketch tools for profiles/paths
   |
5. Implement Assembly Handlers (move_component, rotate_component, joints)
   |-- Multi-body/component operations
   |-- Depends on: feature handlers to create bodies
   |
6. Implement Query/Utility Handlers (measure, get_body_info, export, import, undo)
   |-- Supporting operations
   |-- Can partially parallel with steps 3-5
   |
7. Add MCP Resources (tool reference, coordinate guides, workflow docs)
   |-- Discoverability layer
   |-- Depends on: knowing final tool inventory (after steps 3-6)
   |
8. Add MCP Prompts (workflow templates)
   |-- Highest-level guidance
   |-- Depends on: resources and stable tool set
```

**Critical dependency:** Step 1 (restructure) must happen first because adding 50+ handlers to the current if/elif chain is not viable. Steps 3-6 can partially overlap but sketch tools should lead since other features depend on sketch profiles.

## Fusion 360 API Feature Coverage Map

For reference, here is the full set of Fusion 360 feature types available through `adsk.fusion`, mapped to implementation priority:

| Feature Type | API Class | Priority | In Scope |
|--------------|-----------|----------|----------|
| Extrude | ExtrudeFeature | Exists | Yes |
| Revolve | RevolveFeature | Exists | Yes |
| Fillet | FilletFeature | Exists (buggy) | Yes -- fix |
| Chamfer | ChamferFeature | High | Yes |
| Shell | ShellFeature | High | Yes |
| Draft | DraftFeature | Medium | Yes |
| Sweep | SweepFeature | High | Yes |
| Loft | LoftFeature | High | Yes |
| Hole | HoleFeature | High | Yes |
| Thread | ThreadFeature | Medium | Yes |
| Coil | CoilFeature | Medium | Yes |
| Rib/Web | RibFeature, WebFeature | Low | Yes |
| Rectangular Pattern | RectangularPatternFeature | High | Yes |
| Circular Pattern | CircularPatternFeature | High | Yes |
| Mirror | MirrorFeature | High | Yes |
| Combine | CombineFeature | High | Yes |
| Split Body | SplitBodyFeature | Low | Yes |
| Split Face | SplitFaceFeature | Low | Yes |
| Scale | ScaleFeature | Low | Yes |
| Offset Faces | OffsetFacesFeature | Low | Yes |
| Move | MoveFeature | Medium | Yes |
| Pipe | PipeFeature | Low | Defer |
| Thicken | ThickenFeature | Low | Defer |
| Replace Face | ReplaceFaceFeature | Low | Defer |
| Sheet Metal (Flange, etc.) | FlangeFeature | N/A | Out of scope |
| T-Spline (Form) | FormFeature | N/A | Out of scope |
| Mesh | MeshFeature | N/A | Out of scope |

## Sources

- [FastMCP GitHub - v3.1.0](https://github.com/jlowin/fastmcp) -- Current FastMCP version and capabilities (HIGH confidence)
- [FastMCP Resources Documentation](https://gofastmcp.com/servers/resources) -- @mcp.resource decorator patterns (HIGH confidence)
- [FastMCP Prompts Documentation](https://gofastmcp.com/servers/prompts) -- @mcp.prompt decorator patterns (HIGH confidence)
- [Block's Playbook for Designing MCP Servers](https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers) -- Tool consolidation best practices (HIGH confidence)
- [Fusion 360 Feature Object API Reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Feature.htm) -- Complete feature type list (HIGH confidence)
- [Fusion 360 API Getting Started](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BasicConcepts_UM.htm) -- API structure and patterns (HIGH confidence)
- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture) -- Protocol architecture (HIGH confidence)

---

*Architecture research: 2026-03-13*
