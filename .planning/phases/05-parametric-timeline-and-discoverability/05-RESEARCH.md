# Phase 5: Parametric, Timeline, and Discoverability - Research

**Researched:** 2026-03-15
**Domain:** Fusion 360 UserParameters API, Timeline API, FastMCP resources/prompts, docstring enrichment
**Confidence:** HIGH

## Summary

Phase 5 covers three distinct domains: (1) parametric design via Fusion 360's UserParameters API, (2) timeline navigation via the Timeline/TimelineObject API, and (3) AI discoverability via FastMCP resource endpoints, prompt templates, and docstring enrichment. All three domains are well-documented and follow established patterns in this project.

The parametric and timeline work follows the exact same handler + MCP tool pattern used in all prior phases: new Python handler modules in `fusion-addin/handlers/`, new `@mcp.tool()` definitions in the MCP server, and registration in `HANDLER_MAP`. The discoverability work introduces two new MCP primitives (`@mcp.resource()` and `@mcp.prompt`) that are greenfield in this codebase, plus a bulk docstring update across all 73 existing `@mcp.tool()` functions.

**Primary recommendation:** Implement in three waves: (1) parametric + timeline handlers/tools, (2) MCP resources + prompts (new infrastructure), (3) bulk docstring enrichment (touches every tool but is mechanical).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- create_parameter accepts name + expression + unit (e.g., `create_parameter('width', '5', 'cm')`)
- Expressions can reference other parameters: `create_parameter('height', 'width * 2', 'cm')`
- set_parameter also accepts expressions (not just numeric values): `set_parameter('height', '2 * width')`
- Tool responses that return dimensions should show parameter linkage when driven by parameters: "distance: 5.0 (from 'height')"
- Consistent with Phase 2's separate-tools-per-type decision: create_parameter and set_parameter as distinct tools
- get_timeline returns feature list with indices: index, feature type, name, status (healthy/error/suppressed)
- edit_at_timeline moves the timeline marker and warns about scope: "Features after position N are now suppressed. Use edit_at_timeline(-1) to return to end."
- Add a new create_marker tool for user-named timeline snapshots (e.g., `create_marker('before_fillets')`)
- Markers are stored in-memory by the add-in (not persistent across Fusion sessions)
- undo_to_marker rolls back to a named marker's timeline position
- TIME-03 requires create_marker as a supporting tool
- Per-domain category resources: 'tools/sketch', 'tools/3d-features', 'tools/assembly', 'tools/utility', 'guides/coordinates', 'guides/workflows'
- Resource content lives in separate markdown files (in a resources/ or docs/ directory), loaded by MCP server at startup
- Coordinate system guide covers: all units in cm, the three planes (XY/XZ/YZ), XZ Y-axis inversion behavior
- Workflow guides are higher-level patterns with reasoning, not exact tool sequences
- Prompt templates: box/enclosure, cylinder, gear (spur), simple hinge assembly
- Rich docstrings model after create_sketch's current docstring applied to all 50+ tools
- Every tool gets: 1-2 sentence description, typed parameter list with descriptions, 2-3 usage examples

### Claude's Discretion
- Exact resource file directory structure (resources/ vs docs/)
- FastMCP resource/prompt API patterns and registration approach
- Marker storage implementation details in the add-in
- How to handle parameter deletion or renaming
- Exact workflow guide content for each pattern
- How deeply to document each tool's edge cases in docstrings

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PARAM-01 | `create_parameter` tool and handler for creating named user parameters | Fusion 360 UserParameters.add API with ValueInput.createByString for expressions |
| PARAM-02 | `set_parameter` tool and handler for updating parameter values | UserParameter.expression property for string expressions, .value for numeric |
| TIME-01 | `get_timeline` tool and handler to retrieve design timeline with feature history | Timeline.count, Timeline.item(index), TimelineObject properties (name, index, healthState, isSuppressed) |
| TIME-02 | `edit_at_timeline` tool and handler to roll back to a specific timeline position | Timeline.markerPosition setter, or TimelineObject.rollTo(beforeOrAfter) |
| TIME-03 | `undo_to_marker` tool and handler to undo back to a named timeline marker | In-memory marker dict + Timeline.markerPosition; also needs create_marker supporting tool |
| DISC-01 | MCP Resource endpoints serving tool reference docs per domain category | FastMCP @mcp.resource() with static URIs returning markdown content |
| DISC-02 | MCP Resource endpoint serving coordinate system guide | Static @mcp.resource() loading from markdown file |
| DISC-03 | MCP Resource endpoints serving workflow guides | Static @mcp.resource() loading from markdown files |
| DISC-04 | MCP Prompt templates for common CAD workflows | FastMCP @mcp.prompt decorator with parameterized functions |
| DISC-05 | All MCP tools have rich docstrings with parameter descriptions and usage examples | Bulk update of all 73 @mcp.tool() functions following create_sketch pattern |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| adsk.fusion (UserParameters) | Fusion 360 built-in | Create/modify named parameters with expressions | Native Fusion API, no alternatives |
| adsk.fusion (Timeline) | Fusion 360 built-in | Navigate design history, roll back marker | Native Fusion API, no alternatives |
| adsk.core (ValueInput) | Fusion 360 built-in | Create parameter values from strings/reals | Required by UserParameters.add |
| FastMCP (@mcp.resource) | Current installed | Register MCP resource endpoints | Already used for @mcp.tool() in project |
| FastMCP (@mcp.prompt) | Current installed | Register MCP prompt templates | Already used for @mcp.tool() in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib.Path | stdlib | Load markdown resource files from disk | Resource content loading at startup |
| json | stdlib | Serialize parameter/timeline data | Handler response formatting |

### Alternatives Considered
None -- all decisions are locked. Fusion API is the only option for parametric/timeline; FastMCP is the only option for resources/prompts.

## Architecture Patterns

### Recommended Project Structure
```
fusion-addin/
  handlers/
    parametric.py       # create_parameter, set_parameter handlers
    timeline.py         # get_timeline, edit_at_timeline, create_marker, undo_to_marker handlers
    __init__.py         # Updated with new imports and HANDLER_MAP entries

mcp-server/
  fusion360_mcp_server.py  # New @mcp.tool() + @mcp.resource() + @mcp.prompt + docstring updates
  resources/
    tools/
      sketch.md           # Tool reference for sketch domain
      3d-features.md      # Tool reference for 3D features domain
      assembly.md         # Tool reference for assembly domain
      utility.md          # Tool reference for utility/query/io domain
    guides/
      coordinates.md      # Coordinate system guide (DISC-02)
      workflows.md        # Workflow patterns guide (DISC-03)
```

### Pattern 1: Fusion UserParameters API
**What:** Create and modify named user parameters with expression support
**When to use:** PARAM-01, PARAM-02
**Example:**
```python
# Source: Autodesk Fusion 360 API Reference - UserParameters.add
import adsk.core
import adsk.fusion

def create_parameter(design, rootComp, params):
    name = params.get('name')
    expression = params.get('expression', '0')
    unit = params.get('unit', 'cm')
    comment = params.get('comment', '')

    userParams = design.userParameters
    # Check for duplicate name
    existing = userParams.itemByName(name)
    if existing:
        return {"success": False, "error": f"Parameter '{name}' already exists. Use set_parameter to update."}

    # ValueInput.createByString preserves the expression string
    value = adsk.core.ValueInput.createByString(expression)
    param = userParams.add(name, value, unit, comment)

    if param is None:
        return {"success": False, "error": f"Failed to create parameter '{name}'. Check expression and units."}

    return {
        "success": True,
        "parameter": name,
        "expression": param.expression,
        "value": param.value,
        "unit": param.unit
    }
```

```python
# Source: Autodesk forums + API reference - UserParameter.expression property
def set_parameter(design, rootComp, params):
    name = params.get('name')
    expression = params.get('expression')

    userParams = design.userParameters
    param = userParams.itemByName(name)
    if param is None:
        return {"success": False, "error": f"Parameter '{name}' not found. Use create_parameter first."}

    # Setting expression triggers model regeneration
    param.expression = expression

    return {
        "success": True,
        "parameter": name,
        "expression": param.expression,
        "value": param.value,
        "unit": param.unit
    }
```

### Pattern 2: Fusion Timeline API
**What:** Read timeline features, move the marker, roll back
**When to use:** TIME-01, TIME-02, TIME-03
**Example:**
```python
# Source: Autodesk Fusion 360 API Reference - Timeline, TimelineObject
import adsk.fusion

def get_timeline(design, rootComp, params):
    timeline = design.timeline
    features = []
    for i in range(timeline.count):
        item = timeline.item(i)
        features.append({
            "index": item.index,
            "name": item.name,
            "is_suppressed": item.isSuppressed,
            "is_rolled_back": item.isRolledBack,
            "health_state": _health_state_str(item.healthState),
            "is_group": item.isGroup
        })
    return {
        "success": True,
        "marker_position": timeline.markerPosition,
        "count": timeline.count,
        "features": features
    }

def _health_state_str(state):
    """Convert FeatureHealthStates enum to string."""
    mapping = {
        adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState: "healthy",
        adsk.fusion.FeatureHealthStates.WarningFeatureHealthState: "warning",
        adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState: "error",
        adsk.fusion.FeatureHealthStates.SuppressedFeatureHealthState: "suppressed",
        adsk.fusion.FeatureHealthStates.RolledBackFeatureHealthState: "rolled_back",
    }
    return mapping.get(state, "unknown")

def edit_at_timeline(design, rootComp, params):
    position = params.get('position')
    timeline = design.timeline

    # Special case: -1 means return to end
    if position == -1:
        timeline.moveToEnd()
        return {"success": True, "marker_position": timeline.markerPosition,
                "message": "Returned to end of timeline. All features active."}

    if position < 0 or position > timeline.count:
        return {"success": False, "error": f"Position {position} out of range (0-{timeline.count})."}

    timeline.markerPosition = position
    suppressed_count = timeline.count - position

    return {
        "success": True,
        "marker_position": timeline.markerPosition,
        "message": f"Timeline moved to position {position}. {suppressed_count} features after this position are now suppressed. Use edit_at_timeline(position=-1) to return to end."
    }
```

### Pattern 3: In-Memory Marker Storage
**What:** Named timeline snapshots stored in add-in module state
**When to use:** TIME-03 (create_marker + undo_to_marker)
**Example:**
```python
# Module-level dict in timeline.py -- not persistent across Fusion sessions
_markers = {}

def create_marker(design, rootComp, params):
    name = params.get('name')
    timeline = design.timeline
    position = timeline.markerPosition
    _markers[name] = position
    return {
        "success": True,
        "marker": name,
        "position": position,
        "total_markers": len(_markers)
    }

def undo_to_marker(design, rootComp, params):
    name = params.get('name')
    if name not in _markers:
        available = list(_markers.keys())
        return {"success": False, "error": f"Marker '{name}' not found. Available markers: {available}"}

    target_position = _markers[name]
    timeline = design.timeline
    current = timeline.markerPosition
    timeline.markerPosition = target_position

    return {
        "success": True,
        "marker": name,
        "from_position": current,
        "to_position": target_position,
        "message": f"Rolled back from position {current} to marker '{name}' at position {target_position}."
    }
```

### Pattern 4: FastMCP Resource Registration
**What:** Serve markdown documentation via MCP resource endpoints
**When to use:** DISC-01, DISC-02, DISC-03
**Example:**
```python
# Source: FastMCP official docs - https://gofastmcp.com/servers/resources
from pathlib import Path

RESOURCES_DIR = Path(__file__).parent / "resources"

@mcp.resource("docs://tools/sketch")
def tools_sketch() -> str:
    """Tool reference documentation for sketch operations."""
    return (RESOURCES_DIR / "tools" / "sketch.md").read_text()

@mcp.resource("docs://tools/3d-features")
def tools_3d_features() -> str:
    """Tool reference documentation for 3D feature operations."""
    return (RESOURCES_DIR / "tools" / "3d-features.md").read_text()

@mcp.resource("docs://guides/coordinates")
def guide_coordinates() -> str:
    """Coordinate system guide: units, planes, XZ inversion."""
    return (RESOURCES_DIR / "guides" / "coordinates.md").read_text()
```

### Pattern 5: FastMCP Prompt Templates
**What:** Parameterized prompt templates for common CAD workflows
**When to use:** DISC-04
**Example:**
```python
# Source: FastMCP official docs - https://gofastmcp.com/servers/prompts

@mcp.prompt
def box_enclosure(width: str = "10", depth: str = "8", height: str = "5",
                  wall_thickness: str = "0.2", fillet_radius: str = "0.3") -> str:
    """Generate a step-by-step guide for creating a box enclosure with lid."""
    return f"""Create a box enclosure with these dimensions:
- Width: {width} cm, Depth: {depth} cm, Height: {height} cm
- Wall thickness: {wall_thickness} cm, Fillet radius: {fillet_radius} cm

Step-by-step:
1. Use create_sketch(plane="XY")
2. Use draw_rectangle(x1=0, y1=0, x2={width}, y2={depth})
3. Use finish_sketch()
4. Use extrude(distance={height})
5. Use shell(thickness={wall_thickness}, face="top_face", body_index=0)
6. Use fillet(radius={fillet_radius}, body_index=0)

Shell before fillet because filleting changes edge topology, making face selection harder.
The top_face removal creates the open-top enclosure."""
```

### Anti-Patterns to Avoid
- **ValueInput.createByReal for expressions:** Use createByString when the input is an expression string. createByReal is for pre-computed numeric values in internal units (cm/radians).
- **Persistent marker storage:** Context says markers are in-memory only. Do NOT write markers to files or design attributes. They reset when the add-in restarts.
- **Inline resource content:** Context says resource content lives in separate markdown files. Do NOT embed long documentation strings directly in Python code.
- **Timeline.deleteAllAfterMarker:** This destructive method exists but should NEVER be called. edit_at_timeline only moves the marker, it does not delete features.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Expression evaluation | Custom math parser | Fusion's ValueInput.createByString | Fusion handles parameter references, units, complex expressions natively |
| Timeline position tracking | Manual index tracking | Timeline.markerPosition property | API provides read/write access to the marker position |
| Health state detection | Custom feature validation | TimelineObject.healthState enum | API reports healthy/warning/error/suppressed states |
| MCP resource serving | Custom HTTP endpoints | FastMCP @mcp.resource() decorator | Built into the MCP protocol, clients discover resources automatically |
| Prompt templates | Custom prompt string builders | FastMCP @mcp.prompt decorator | MCP clients can list and invoke prompts with typed arguments |

**Key insight:** Both Fusion 360 and FastMCP provide first-class APIs for everything this phase needs. The handlers are thin wrappers around native APIs.

## Common Pitfalls

### Pitfall 1: ValueInput.createByString vs createByReal confusion
**What goes wrong:** Using createByReal with a string value, or createByString with internal units
**Why it happens:** The two methods have different semantics. createByReal takes a double in internal units (cm). createByString takes a string expression that Fusion evaluates.
**How to avoid:** Always use createByString when the source is a user-provided expression string. The expression can be a plain number ("5"), a unit expression ("5 in"), or a parameter reference ("width * 2").
**Warning signs:** Parameters created with wrong values, unit mismatches

### Pitfall 2: Timeline.markerPosition is 0-indexed from beginning
**What goes wrong:** Off-by-one errors when setting marker position
**Why it happens:** markerPosition=0 means before all features (beginning), markerPosition=count means after all features (end). It is a position BETWEEN items, not an item index.
**How to avoid:** Use -1 convention in the tool API to mean "end" (map to timeline.moveToEnd()). Validate 0 <= position <= timeline.count.
**Warning signs:** Features unexpectedly suppressed or not suppressed

### Pitfall 3: FeatureHealthStates enum access
**What goes wrong:** Comparing healthState to wrong values or strings
**Why it happens:** healthState returns an enum from adsk.fusion.FeatureHealthStates, not a string
**How to avoid:** Map the enum values to strings in the handler before returning to MCP
**Warning signs:** Health state always shows "unknown"

### Pitfall 4: Parameter name collisions with model parameters
**What goes wrong:** Trying to create a parameter with a name that matches an existing model parameter
**Why it happens:** Fusion has both user parameters and model parameters. Names must be unique across both.
**How to avoid:** Check userParams.itemByName(name) before adding. Return a clear error if the name exists.
**Warning signs:** "Parameter already exists" errors

### Pitfall 5: Resource file loading at import time
**What goes wrong:** Server crashes if resource markdown files are missing when the MCP server starts
**Why it happens:** Reading files at module import time with no error handling
**How to avoid:** Load files lazily inside the resource function, or add existence checks with clear error messages
**Warning signs:** MCP server fails to start

### Pitfall 6: Docstring update breaks tool signatures
**What goes wrong:** Accidentally changing function parameter names or types while updating docstrings
**Why it happens:** The bulk docstring update touches all 73 tools, easy to introduce typos
**How to avoid:** Docstring-only changes. Do not modify function signatures, parameter names, or body logic.
**Warning signs:** Tools stop working after docstring update

## Code Examples

### Gold Standard Docstring (create_sketch -- the template for DISC-05)
```python
# Source: mcp-server/fusion360_mcp_server.py lines 93-112
@mcp.tool()
def create_sketch(plane: str = "XY", offset: float = 0, body_index: int = None, face: str = None) -> dict:
    """
    Create a new sketch and enter edit mode.

    By default creates sketch on a construction plane (XY, XZ, or YZ).
    Optionally sketch on a body face by providing body_index + face params.
    When face is provided, the plane param is ignored.

    Args:
        plane: Construction plane name (XY, XZ, YZ). Ignored if face is provided.
        offset: Offset distance from plane (cm). Only for construction planes.
        body_index: Body to sketch on (0 = first body). Required with face.
        face: Face selector - semantic name ('top_face', 'bottom_face') or integer index. Use get_body_info() to see faces.

    Examples:
        create_sketch(plane="XY")                          # Horizontal at origin
        create_sketch(plane="XZ", offset=5)                # Vertical, 5cm forward
        create_sketch(body_index=0, face="top_face")       # Sketch on body's top face
        create_sketch(body_index=0, face="0")              # Sketch on face index 0
    """
```

### Minimal Docstring (what most tools currently have -- needs enrichment)
```python
# Source: mcp-server/fusion360_mcp_server.py
@mcp.tool()
def draw_rectangle(x1: float, y1: float, x2: float, y2: float) -> dict:
    """Draw a rectangle in the active sketch (units: cm)"""
```

### Target Docstring (what DISC-05 transforms the above into)
```python
@mcp.tool()
def draw_rectangle(x1: float, y1: float, x2: float, y2: float) -> dict:
    """
    Draw a rectangle from two opposite corner points in the active sketch.

    Creates a four-line rectangle. The resulting profile can be extruded,
    revolved, or used as a path for sweep operations.

    Args:
        x1: First corner X coordinate (cm)
        y1: First corner Y coordinate (cm)
        x2: Opposite corner X coordinate (cm)
        y2: Opposite corner Y coordinate (cm)

    Examples:
        draw_rectangle(x1=-5, y1=-5, x2=5, y2=5)     # 10x10 cm centered
        draw_rectangle(x1=0, y1=0, x2=3, y2=2)        # 3x2 cm from origin
    """
```

### Handler Registration Pattern
```python
# Source: fusion-addin/handlers/__init__.py -- add these entries
from .parametric import create_parameter, set_parameter
from .timeline import get_timeline, edit_at_timeline, create_marker, undo_to_marker

HANDLER_MAP = {
    # ... existing entries ...

    # Parametric design (Phase 5)
    'create_parameter': create_parameter,
    'set_parameter': set_parameter,

    # Timeline navigation (Phase 5)
    'get_timeline': get_timeline,
    'edit_at_timeline': edit_at_timeline,
    'create_marker': create_marker,
    'undo_to_marker': undo_to_marker,
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline docstrings only | @mcp.resource() + @mcp.prompt for discoverability | FastMCP 2.x | AI models can discover tools and workflows via MCP protocol |
| Parameter.value (double) | Parameter.expression (string) | Always available | Expressions with parameter references enable parametric design |
| Manual undo counting | Timeline.markerPosition | Always available | Precise rollback to specific positions in design history |

**Current docstring status across 73 tools:**
- ~46 tools have `Args:` sections (most Phase 2+ tools)
- ~8 tools have `Examples:` sections
- ~19 tools have one-line docstrings only
- Target: ALL 73 tools have description + Args + Examples

## Open Questions

1. **What happens when setting markerPosition to the same position it's already at?**
   - What we know: The API accepts it without error
   - What's unclear: Whether it triggers an unnecessary recompute
   - Recommendation: Check current position first and skip if already there

2. **Can UserParameters.add handle parameter-referencing expressions at creation time?**
   - What we know: The API docs say ValueInput.createByString "is used as-is for the expression"
   - What's unclear: Whether referencing another user parameter in the initial expression works immediately
   - Recommendation: Test with a simple case; if not, create with numeric value then set expression

3. **Does FastMCP @mcp.resource require parentheses or not?**
   - What we know: FastMCP docs show `@mcp.resource("uri")` with parentheses and URI argument
   - What's unclear: Whether `@mcp.resource` without parentheses works (like @mcp.prompt does)
   - Recommendation: Always use `@mcp.resource("uri")` with explicit URI

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual integration testing (Fusion 360 required) |
| Config file | none -- no automated test framework in project |
| Quick run command | Manual: start Fusion 360 + add-in, connect MCP client, run tools |
| Full suite command | Manual: exercise all new tools + verify resources/prompts visible |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PARAM-01 | create_parameter creates named param with expression | manual | MCP: `create_parameter(name="width", expression="5", unit="cm")` | N/A |
| PARAM-02 | set_parameter updates expression, model regenerates | manual | MCP: `set_parameter(name="width", expression="10")` then verify geometry | N/A |
| TIME-01 | get_timeline lists features with index/name/health | manual | MCP: `get_timeline()` after creating geometry | N/A |
| TIME-02 | edit_at_timeline moves marker, suppresses features | manual | MCP: `edit_at_timeline(position=2)` then `get_timeline()` | N/A |
| TIME-03 | undo_to_marker returns to named marker position | manual | MCP: `create_marker(name="test")`, make changes, `undo_to_marker(name="test")` | N/A |
| DISC-01 | Resource endpoints serve tool docs per domain | manual | MCP client lists resources, reads each one | N/A |
| DISC-02 | Coordinate system guide resource accessible | manual | MCP client reads `docs://guides/coordinates` | N/A |
| DISC-03 | Workflow guide resources accessible | manual | MCP client reads `docs://guides/workflows` | N/A |
| DISC-04 | Prompt templates invocable with parameters | manual | MCP client lists prompts, invokes `box_enclosure(width="12")` | N/A |
| DISC-05 | All tools have rich docstrings visible to MCP | manual | MCP client `list_tools()` shows full descriptions | N/A |

### Sampling Rate
- **Per task commit:** Manual smoke test of new/changed tools via MCP client
- **Per wave merge:** Full manual test of all phase tools
- **Phase gate:** All 10 requirements exercised manually before verify

### Wave 0 Gaps
- [ ] `fusion-addin/handlers/parametric.py` -- new handler module
- [ ] `fusion-addin/handlers/timeline.py` -- new handler module
- [ ] `mcp-server/resources/` directory with all markdown content files
- [ ] No automated test infrastructure exists; all testing is manual via Fusion 360

## Sources

### Primary (HIGH confidence)
- [Autodesk Fusion 360 API - UserParameters.add](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserParameters_add.htm) - Method signature, ValueInput parameter
- [Autodesk Fusion 360 API - Timeline](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Timeline.htm) - Timeline properties (count, markerPosition) and methods (item, moveToEnd, moveToBeginning)
- [Autodesk Fusion 360 API - TimelineObject](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TimelineObject.htm) - TimelineObject properties (index, name, healthState, isSuppressed, isRolledBack) and rollTo method
- [FastMCP Resources Docs](https://gofastmcp.com/servers/resources) - @mcp.resource() decorator API with URI templates
- [FastMCP Prompts Docs](https://gofastmcp.com/servers/prompts) - @mcp.prompt decorator API with Message return types

### Secondary (MEDIUM confidence)
- [Autodesk Forums - UserParameter expression](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/how-to-perform-operations-on-user-parameters/td-p/11933764) - param.expression property for setting values
- [Autodesk Fusion 360 API - Parameter.value](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Parameter_value.htm) - value property in database units
- [Autodesk Fusion 360 API - TimelineObject.rollTo](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TimelineObject_rollTo.htm) - rollTo(beforeOrAfter) boolean parameter

### Tertiary (LOW confidence)
- FeatureHealthStates enum values (HealthyFeatureHealthState, WarningFeatureHealthState, ErrorFeatureHealthState, SuppressedFeatureHealthState, RolledBackFeatureHealthState) -- from forum examples and API pattern, not directly verified on official enum reference page

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Native Fusion API + FastMCP, both well-documented with official references
- Architecture: HIGH - Follows exact same handler + MCP tool pattern used in phases 1-4
- Pitfalls: HIGH - Based on direct API documentation analysis and known project patterns
- Discoverability (resources/prompts): HIGH - FastMCP docs are current and explicit
- Docstring enrichment: HIGH - Mechanical pattern matching against gold standard template

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable APIs, low churn risk)
