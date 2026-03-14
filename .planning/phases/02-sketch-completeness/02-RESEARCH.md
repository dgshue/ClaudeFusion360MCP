# Phase 2: Sketch Completeness - Research

**Researched:** 2026-03-13
**Domain:** Fusion 360 API -- sketch primitives, geometric constraints, parametric dimensions
**Confidence:** HIGH

## Summary

Phase 2 adds 21 new tools to the MCP server: 9 sketch primitives (draw_spline, draw_ellipse, draw_slot, draw_point, draw_text, offset_curves, set_construction, project_geometry, import_svg), 9 geometric constraints (constrain_horizontal through constrain_symmetric), and 3 dimension tools (dimension_distance, dimension_radial, dimension_angular), plus a get_sketch_info query tool. All tools follow established Phase 1 patterns: handler signature `def handler(design, rootComp, params) -> dict`, coordinate correction via `transform_to_sketch_coords`/`transform_from_sketch_coords`, and `wrap_handler` error wrapping.

The Fusion 360 API provides direct methods for all required operations. Sketch curves are accessed via `sketch.sketchCurves.sketchFittedSplines`, `sketchEllipses`, etc. Constraints live under `sketch.geometricConstraints` with explicit `addHorizontal()`, `addPerpendicular()`, `addTangent()` etc. methods. Dimensions use `sketch.sketchDimensions.addDistanceDimension()`, `addDiameterDimension()`, `addAngularDimension()`, and `addRadialDimension()`.

The critical new infrastructure piece is a sketch entity indexing/labeling helper (`helpers/sketch_entities.py`) that assigns stable integer indices to sketch curves and points, and generates semantic labels analogous to `label_edge()` and `label_face()` in `helpers/selection.py`. Every draw command must return `curve_index` (and `point_index` values for endpoints). Existing Phase 1 draw commands must be updated to also return these indices.

**Primary recommendation:** Build the sketch entity helper first, then update existing draw commands to return indices, then add new primitives, then constraints/dimensions, then get_sketch_info last (it depends on all the labeling infrastructure).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Index-based referencing for both curves and points (consistent with Phase 1 edge/face selection)
- Every draw command returns the index of the created entity (curve_index and point indices for endpoints)
- Existing Phase 1 draw tools (draw_line, draw_circle, draw_rectangle, draw_arc, draw_polygon) must be updated to also return entity indices
- Constraints and dimensions reference entities by numeric index
- Support point_index in addition to curve_index for constraints that need point references (coincident, symmetric)
- Two-entity constraint parameters: use two separate parameters curve_index and curve_index_2 (not an array)
- Dimension value is required at creation time (not optional/auto-measured)
- Constraints: separate tools per constraint type (9 tools)
- Dimensions: separate tools per dimension type (3 tools)
- Primitives: individual tools per primitive (9 tools)
- Tool naming: constrain_horizontal, constrain_vertical, etc.; dimension_distance, dimension_radial, dimension_angular; draw_spline, draw_ellipse, draw_slot, draw_point, draw_text, offset_curves, set_construction, project_geometry, import_svg
- SVG import: use Fusion 360 native sketch.importSVG() API, accept file path only, import at native SVG dimensions with optional scale parameter
- get_sketch_info: new query tool listing all curves, points, constraints, dimensions with semantic labels and constraint status

### Claude's Discretion
- Exact semantic label vocabulary for sketch curves
- Internal sketch entity helper implementation details
- How to handle degenerate cases (zero-length lines, overlapping constraints)
- Spline fitting algorithm parameters
- Text font handling and available fonts

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NSKCH-01 | draw_spline tool/handler for fitted splines | sketch.sketchCurves.sketchFittedSplines.add(ObjectCollection of Point3D) |
| NSKCH-02 | draw_ellipse tool/handler | sketch.sketchCurves.sketchEllipses.add(centerPoint, majorAxisPoint, point) |
| NSKCH-03 | draw_slot tool/handler | sketch.addCenterPointSlot(centerPoint, endPoint, width) |
| NSKCH-04 | draw_point tool/handler | sketch.sketchPoints.add(Point3D) |
| NSKCH-05 | offset_curves tool/handler | sketch.offset(curves, directionPoint, distance) |
| NSKCH-06 | draw_text tool/handler | sketch.sketchTexts.createInput2(text, height) + setAsMultiLine() + add() |
| NSKCH-07 | set_construction tool/handler | sketchCurve.isConstruction = True/False |
| NSKCH-08 | project_geometry tool/handler | sketch.project(entity) or sketch.project2(entity, isLinked) |
| NSKCH-09 | import_svg tool/handler | sketch.importSVG(fullFilename, xPosition, yPosition, scale) |
| CNST-01 | constrain_horizontal | sketch.geometricConstraints.addHorizontal(line) |
| CNST-02 | constrain_vertical | sketch.geometricConstraints.addVertical(line) |
| CNST-03 | constrain_perpendicular | sketch.geometricConstraints.addPerpendicular(line1, line2) |
| CNST-04 | constrain_parallel | sketch.geometricConstraints.addParallel(line1, line2) |
| CNST-05 | constrain_tangent | sketch.geometricConstraints.addTangent(curve1, curve2) |
| CNST-06 | constrain_coincident | sketch.geometricConstraints.addCoincident(point, curveOrPoint) |
| CNST-07 | constrain_concentric | sketch.geometricConstraints.addConcentric(arc1, arc2) |
| CNST-08 | constrain_equal | sketch.geometricConstraints.addEqual(curve1, curve2) |
| CNST-09 | constrain_symmetric | sketch.geometricConstraints.addSymmetry(point1, point2, symmetryLine) |
| DIM-01 | dimension_distance | sketch.sketchDimensions.addDistanceDimension(pt1, pt2, orientation, textPt) |
| DIM-02 | dimension_radial (diameter/radius) | addDiameterDimension(curve, textPt) or addRadialDimension(curve, textPt) |
| DIM-03 | dimension_angular | sketch.sketchDimensions.addAngularDimension(line1, line2, textPt) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| adsk.fusion | Fusion 360 current | All sketch/constraint/dimension API calls | Only option for Fusion 360 add-in |
| adsk.core | Fusion 360 current | Point3D, ObjectCollection, ValueInput, Vector3D | Core geometry types |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math | Python stdlib | Angle calculations, point geometry for ellipse/arc | Always available |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sketchFittedSplines | sketchControlPointSplines | Fitted splines pass through points (more intuitive for MCP callers); control point splines approximate |
| addDiameterDimension | addRadialDimension | Both available; expose as sub-options via a `type` parameter ("diameter" vs "radius") in dimension_radial |
| sketch.project | sketch.project2 | project2 adds isLinked parameter; prefer project2 for future-proofing |

## Architecture Patterns

### Recommended Project Structure
```
fusion-addin/
  handlers/
    sketch.py              # Existing + updated draw commands (return indices)
    sketch_primitives.py   # New: draw_spline, draw_ellipse, draw_slot, draw_point, draw_text
    sketch_ops.py          # New: offset_curves, set_construction, project_geometry, import_svg
    sketch_constraints.py  # New: all 9 constrain_* handlers
    sketch_dimensions.py   # New: all 3 dimension_* handlers
    sketch_query.py        # New: get_sketch_info handler
    __init__.py            # Updated: register ~22 new handlers
  helpers/
    sketch_entities.py     # New: curve/point indexing + semantic labeling
    coordinates.py         # Existing (unchanged)
    bodies.py              # Existing (unchanged)
    selection.py           # Existing (unchanged, but pattern to replicate)
    errors.py              # Existing (unchanged)
  mcp-server/
    fusion360_mcp_server.py  # Add ~22 new @mcp.tool() definitions
```

### Pattern 1: Sketch Entity Indexing
**What:** A helper that converts between integer indices and actual sketch curve/point objects
**When to use:** Every constraint, dimension, and query tool that references sketch entities
**Example:**
```python
# helpers/sketch_entities.py
def get_sketch_curve(sketch, curve_index):
    """Get a SketchCurve by index from the sketch's curves collection."""
    curves = sketch.sketchCurves
    if curve_index < 0 or curve_index >= curves.count:
        raise ValueError(
            f"Curve index {curve_index} out of range. Sketch has {curves.count} curves (0-{curves.count - 1}). "
            f"Use get_sketch_info() to see available curves."
        )
    return curves.item(curve_index)

def get_sketch_point(sketch, point_index):
    """Get a SketchPoint by index from the sketch's points collection."""
    points = sketch.sketchPoints
    if point_index < 0 or point_index >= points.count:
        raise ValueError(
            f"Point index {point_index} out of range. Sketch has {points.count} points (0-{points.count - 1}). "
            f"Use get_sketch_info() to see available points."
        )
    return points.item(point_index)

def get_curve_index(sketch, curve):
    """Find the index of a given SketchCurve in the sketch's curves collection."""
    for i in range(sketch.sketchCurves.count):
        if sketch.sketchCurves.item(i) == curve:
            return i
    return -1
```

### Pattern 2: Draw Handler Returns Entity Indices
**What:** Every draw handler returns `curve_index` (and start/end point indices) in addition to existing return data
**When to use:** All draw_* handlers (existing and new)
**Example:**
```python
def draw_line(design, rootComp, params):
    sketch = get_sketch(rootComp)
    x1, y1 = transform_to_sketch_coords(params['x1'], params['y1'], sketch)
    x2, y2 = transform_to_sketch_coords(params['x2'], params['y2'], sketch)
    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)

    # Find curve index by searching curves collection
    curve_index = get_curve_index(sketch, line)

    rx1, ry1 = transform_from_sketch_coords(p1.x, p1.y, sketch)
    rx2, ry2 = transform_from_sketch_coords(p2.x, p2.y, sketch)
    return {
        "success": True,
        "curve_index": curve_index,
        "start_point_index": find_point_index(sketch, line.startSketchPoint),
        "end_point_index": find_point_index(sketch, line.endSketchPoint),
        "line_length": line.length,
        "start": [rx1, ry1],
        "end": [rx2, ry2]
    }
```

### Pattern 3: Constraint Handler
**What:** Each constraint handler resolves entity indices, calls the appropriate geometricConstraints method
**When to use:** All 9 constrain_* handlers
**Example:**
```python
def constrain_perpendicular(design, rootComp, params):
    sketch = get_sketch(rootComp)
    curve1 = get_sketch_curve(sketch, params['curve_index'])
    curve2 = get_sketch_curve(sketch, params['curve_index_2'])
    constraint = sketch.geometricConstraints.addPerpendicular(curve1, curve2)
    return {"success": True, "constraint_type": "perpendicular"}
```

### Pattern 4: Dimension Handler
**What:** Each dimension handler resolves entity indices, creates the dimension with required value
**When to use:** All 3 dimension_* handlers
**Example:**
```python
def dimension_distance(design, rootComp, params):
    sketch = get_sketch(rootComp)
    # Can dimension between two points or a line
    if 'point_index' in params and 'point_index_2' in params:
        pt1 = get_sketch_point(sketch, params['point_index'])
        pt2 = get_sketch_point(sketch, params['point_index_2'])
    elif 'curve_index' in params:
        curve = get_sketch_curve(sketch, params['curve_index'])
        pt1 = curve.startSketchPoint
        pt2 = curve.endSketchPoint

    orientation = adsk.fusion.DimensionOrientations.AlignedDimensionOrientation
    textPt = adsk.core.Point3D.create(0, 0, 0)  # Auto-position
    dim = sketch.sketchDimensions.addDistanceDimension(pt1, pt2, orientation, textPt)
    dim.parameter.value = params['value']  # Set the dimension value (cm)
    return {"success": True, "dimension_type": "distance", "value": params['value']}
```

### Pattern 5: Semantic Curve Labeling
**What:** Generate human-readable labels for sketch curves, analogous to label_edge() for body edges
**When to use:** get_sketch_info handler, draw command responses
**Example:**
```python
def label_curve(curve, index):
    """Generate semantic label for a sketch curve."""
    if isinstance(curve, adsk.fusion.SketchLine):
        length = round(curve.length, 2)
        # Check if horizontal or vertical
        sp, ep = curve.startSketchPoint.geometry, curve.endSketchPoint.geometry
        if abs(sp.y - ep.y) < 0.001:
            return f"Curve {index} (line, horizontal, {length}cm)"
        elif abs(sp.x - ep.x) < 0.001:
            return f"Curve {index} (line, vertical, {length}cm)"
        return f"Curve {index} (line, {length}cm)"
    elif isinstance(curve, adsk.fusion.SketchCircle):
        radius = round(curve.radius, 2)
        return f"Curve {index} (circle, radius {radius}cm)"
    elif isinstance(curve, adsk.fusion.SketchArc):
        radius = round(curve.radius, 2)
        sweep = round(math.degrees(curve.endAngle - curve.startAngle), 1)
        return f"Curve {index} (arc, radius {radius}cm, {sweep}deg)"
    elif isinstance(curve, adsk.fusion.SketchEllipse):
        major = round(curve.majorRadius, 2)
        minor = round(curve.minorRadius, 2)
        return f"Curve {index} (ellipse, {major}x{minor}cm)"
    elif isinstance(curve, adsk.fusion.SketchFittedSpline):
        points = curve.fitPoints.count
        return f"Curve {index} (spline, {points} points)"
    # Fallback
    const = " construction" if curve.isConstruction else ""
    return f"Curve {index} ({type(curve).__name__}{const})"
```

### Anti-Patterns to Avoid
- **Returning curve objects instead of indices:** MCP callers work across JSON boundaries -- they cannot hold object references. Always return integer indices.
- **Using sketch.sketchCurves.count-1 as the index for newly created curves:** The count may include construction geometry or system-generated curves. Instead, search for the exact curve object after creation.
- **Applying coordinate correction to constraint/dimension operations:** Constraints and dimensions operate on existing sketch entities (already in sketch-local coordinates). Only apply coordinate correction on draw commands that accept world-space input coordinates.
- **Creating a monolithic sketch.py with 30+ handlers:** Split into logical files (primitives, constraints, dimensions, query) for maintainability.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Offset curves | Manual parallel line computation | sketch.offset(curves, dirPoint, distance) | Handles connected curves, arcs, splines correctly |
| Slot geometry | Lines + arcs assembled manually | sketch.addCenterPointSlot(center, end, width) | Returns proper constrained slot geometry with construction lines |
| SVG parsing | Custom SVG path parser | sketch.importSVG(filename, x, y, scale) | Handles all SVG path types, transforms, embedded fonts |
| Connected curve finding | Manual graph traversal | sketch.findConnectedCurves(curve) | Built-in for offset input collection |
| Text along path | Manual character placement | sketchTexts.createInput2() + setAsAlongPath() | Handles font metrics, kerning, path following |

**Key insight:** The Fusion 360 API provides surprisingly complete sketch operations. The primary engineering challenge is not reimplementing geometry algorithms, but building the index-based referencing layer and semantic labeling infrastructure that makes these APIs accessible through a JSON-based MCP protocol.

## Common Pitfalls

### Pitfall 1: Sketch Curve Index Instability
**What goes wrong:** Curve indices can shift when entities are added, deleted, or constraints are applied (the internal collection may reorder)
**Why it happens:** Fusion 360's sketch curve collection is not guaranteed to maintain insertion order
**How to avoid:** Return the curve index immediately after creation by searching the collection for the exact object reference. Document that indices are valid within a single sketch editing session.
**Warning signs:** Tests pass with simple sketches but fail with complex multi-entity sketches

### Pitfall 2: SketchPoint Sharing Between Curves
**What goes wrong:** When two lines share an endpoint, they reference the same SketchPoint object. Point indices may not be what the caller expects.
**Why it happens:** Fusion 360 automatically merges coincident sketch points
**How to avoid:** Document that point_index references shared points. get_sketch_info should show which curves share each point. The sketchPoints collection includes the origin point at index 0.
**Warning signs:** point_index returns unexpected values; constraints applied to wrong entities

### Pitfall 3: Coordinate Correction on Non-Draw Operations
**What goes wrong:** Applying transform_to_sketch_coords on constraint/dimension parameters produces wrong results
**Why it happens:** Constraints reference existing sketch entities which are already in sketch-local space
**How to avoid:** Only apply coordinate correction in draw_* and import_* handlers that accept world-space coordinate inputs. Constraint/dimension handlers work entirely in index space.
**Warning signs:** Constraints applied to wrong geometry on XZ plane sketches

### Pitfall 4: DimensionOrientations for Distance Dimensions
**What goes wrong:** Distance dimension displays incorrectly or constrains wrong degree of freedom
**Why it happens:** Using AlignedDimensionOrientation when HorizontalDimensionOrientation or VerticalDimensionOrientation would be correct
**How to avoid:** Default to AlignedDimensionOrientation (measures actual distance between points). Optionally expose orientation parameter for callers who need axis-aligned dimensions.
**Warning signs:** Dimension value doesn't match expected measurement

### Pitfall 5: Text Position Point for Dimensions
**What goes wrong:** Dimension text overlaps geometry or is placed off-screen
**Why it happens:** addDistanceDimension/addAngularDimension require a textPoint parameter for display position
**How to avoid:** Auto-calculate a reasonable text position offset from the measured entities (e.g., midpoint + perpendicular offset). The text position affects only display, not the constraint value.
**Warning signs:** Dimensions are created but appear to be "missing" in the UI

### Pitfall 6: Importing SVG with Coordinate Correction
**What goes wrong:** SVG imports at wrong position on XZ plane sketches
**Why it happens:** importSVG takes xPosition/yPosition which need coordinate correction
**How to avoid:** Apply transform_to_sketch_coords to the position parameters of importSVG
**Warning signs:** SVG content mirrored or offset on XZ plane

## Code Examples

### Fitted Spline Creation
```python
# Source: Autodesk Fusion 360 API - SketchSplineThroughPoints Sample
points = adsk.core.ObjectCollection.create()
points.add(adsk.core.Point3D.create(0, 0, 0))
points.add(adsk.core.Point3D.create(5, 1, 0))
points.add(adsk.core.Point3D.create(6, 4, 0))
spline = sketch.sketchCurves.sketchFittedSplines.add(points)
```

### Ellipse Creation
```python
# Source: Autodesk Fusion 360 API - SketchEllipses.add
# Parameters: centerPoint (Point3D), majorAxisPoint (Point3D), point on ellipse (Point3D)
center = adsk.core.Point3D.create(0, 0, 0)
major_pt = adsk.core.Point3D.create(5, 0, 0)  # major axis endpoint
minor_pt = adsk.core.Point3D.create(0, 3, 0)  # point on ellipse defining minor axis
ellipse = sketch.sketchCurves.sketchEllipses.add(center, major_pt, minor_pt)
```

### Center Point Slot
```python
# Source: Autodesk Fusion 360 API - Sketch.addCenterPointSlot
center = adsk.core.Point3D.create(0, 0, 0)
end_pt = adsk.core.Point3D.create(5, 0, 0)
width = adsk.core.ValueInput.createByReal(2.0)  # slot width in cm
result = sketch.addCenterPointSlot(center, end_pt, width)
# Returns: [startArc, endArc, line1, line2, constructionLine, ...]
```

### Sketch Text
```python
# Source: Autodesk Fusion 360 API - SketchText Sample
texts = sketch.sketchTexts
input = texts.createInput2('Hello World', 0.5)  # text, height in cm
input.setAsMultiLine(
    adsk.core.Point3D.create(0, 0, 0),       # corner1
    adsk.core.Point3D.create(10, 2, 0),       # corner2
    adsk.core.HorizontalAlignments.LeftHorizontalAlignment,
    adsk.core.VerticalAlignments.TopVerticalAlignment,
    0  # angle
)
# Optional: input.fontName = 'Arial'
texts.add(input)
```

### Offset Curves
```python
# Source: Autodesk Fusion 360 API - Sketch Fillet and Offset Sample
# First find connected curves
curves = sketch.findConnectedCurves(sketch.sketchCurves.item(0))
dirPoint = adsk.core.Point3D.create(0, 0.5, 0)  # offset direction
offsetCurves = sketch.offset(curves, dirPoint, 0.25)  # distance in cm
```

### Construction Geometry Toggle
```python
# Source: Autodesk Fusion 360 API - SketchLine.isConstruction
curve = sketch.sketchCurves.item(curve_index)
curve.isConstruction = True  # or False to revert
```

### Project Geometry
```python
# Source: Autodesk Fusion 360 API - Sketch.project
# Project a body edge onto the sketch plane
edge = body.edges.item(0)
projected = sketch.project(edge)  # returns ObjectCollection of sketch entities
```

### SVG Import
```python
# Source: Autodesk Fusion 360 API - Sketch.importSVG
success = sketch.importSVG(
    "C:/path/to/file.svg",  # full file path
    0.0,    # x position (cm)
    0.0,    # y position (cm)
    1.0     # scale factor
)
```

### Geometric Constraints
```python
# Source: Autodesk Fusion 360 API - GeometricConstraints
gc = sketch.geometricConstraints

# Single-entity constraints
gc.addHorizontal(line)              # CNST-01
gc.addVertical(line)                # CNST-02

# Two-entity constraints
gc.addPerpendicular(line1, line2)   # CNST-03
gc.addParallel(line1, line2)        # CNST-04
gc.addTangent(curve1, curve2)       # CNST-05
gc.addCoincident(point, curve)      # CNST-06 -- point to curve or point to point
gc.addConcentric(arc1, arc2)        # CNST-07
gc.addEqual(curve1, curve2)         # CNST-08
gc.addSymmetry(entity1, entity2, symmetryLine)  # CNST-09
```

### Sketch Dimensions
```python
# Source: Autodesk Fusion 360 API - SketchDimensions
dims = sketch.sketchDimensions

# Distance dimension (DIM-01)
dim = dims.addDistanceDimension(
    point1, point2,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    textPoint  # Point3D for text position
)
dim.parameter.value = 5.0  # set value in cm

# Diameter dimension (DIM-02)
dim = dims.addDiameterDimension(circle_or_arc, textPoint)
# or: dims.addRadialDimension(circle_or_arc, textPoint)

# Angular dimension (DIM-03)
dim = dims.addAngularDimension(line1, line2, textPoint)
```

### Sketch Constraint Status Query
```python
# Sketch-level constraint status
# sketch.constraintStatus is not directly available but can be inferred:
# - Count fully constrained curves vs total
# - Each sketchCurve has isFullyConstrained property
for i in range(sketch.sketchCurves.count):
    curve = sketch.sketchCurves.item(i)
    is_constrained = curve.isFullyConstrained  # bool
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| sketch.project() | sketch.project2() | Recent API | project2 adds isLinked parameter (linked projections update when source changes) |
| geometricConstraints.addOffset() | geometricConstraints.addOffset2() | Recent API | addOffset is RETIRED; use addOffset2 with OffsetConstraintInput |
| sketchTexts.createInput() | sketchTexts.createInput2() | Recent API | createInput2 supports multi-line text, along-path text |

**Deprecated/outdated:**
- `geometricConstraints.addOffset()` -- RETIRED, replaced by `addOffset2()`. However for simple offset curves, `sketch.offset()` is the simpler approach.
- `sketch.project()` -- replaced by `project2()` which supports linked/unlinked option. `project()` still works.

## Open Questions

1. **Curve index stability across constraint application**
   - What we know: Curves are accessed via sketch.sketchCurves.item(i); the collection order may change
   - What's unclear: Whether adding a constraint reorders the curves collection
   - Recommendation: After creating curves, immediately capture their index. For get_sketch_info, always enumerate fresh. Document that indices are session-stable.

2. **addSymmetry exact parameter types**
   - What we know: Takes entityOne, entityTwo, symmetryLine -- likely (SketchPoint, SketchPoint, SketchLine) or (SketchCurve, SketchCurve, SketchLine)
   - What's unclear: Exact accepted entity types (points vs curves vs mixed)
   - Recommendation: Test both point-based and curve-based symmetry. Support both via parameter overloading (accept curve_index OR point_index for each entity).

3. **Text font availability in Fusion 360**
   - What we know: createInput2 accepts fontName property; 'Artifakt Element' is default Fusion font
   - What's unclear: Full list of available fonts across platforms
   - Recommendation: Make fontName optional, default to system font. Document that available fonts depend on OS installation.

4. **Slot return value indexing**
   - What we know: addCenterPointSlot returns [startArc, endArc, line1, line2, constructionLine, ...]
   - What's unclear: How these map to sketchCurves indices
   - Recommendation: After slot creation, find all returned entities in the curves collection and return their indices.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual testing in Fusion 360 (no unit test framework for add-in) |
| Config file | none -- Fusion 360 Python add-ins run inside Fusion's embedded Python |
| Quick run command | `batch()` MCP call with test sequence |
| Full suite command | Manual test script via MCP batch operations |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NSKCH-01 | draw_spline creates fitted spline | smoke | `batch([create_sketch, draw_spline, get_sketch_info])` | N/A Wave 0 |
| NSKCH-02 | draw_ellipse creates ellipse | smoke | `batch([create_sketch, draw_ellipse, get_sketch_info])` | N/A Wave 0 |
| NSKCH-03 | draw_slot creates slot geometry | smoke | `batch([create_sketch, draw_slot, get_sketch_info])` | N/A Wave 0 |
| NSKCH-04 | draw_point creates reference point | smoke | `batch([create_sketch, draw_point, get_sketch_info])` | N/A Wave 0 |
| NSKCH-05 | offset_curves creates parallel profile | smoke | `batch([create_sketch, draw_circle, offset_curves])` | N/A Wave 0 |
| NSKCH-06 | draw_text creates extrudable text | smoke | `batch([create_sketch, draw_text, extrude])` | N/A Wave 0 |
| NSKCH-07 | set_construction toggles construction flag | smoke | `batch([create_sketch, draw_line, set_construction, get_sketch_info])` | N/A Wave 0 |
| NSKCH-08 | project_geometry projects edge onto sketch | smoke | Create body, then `batch([create_sketch, project_geometry])` | N/A Wave 0 |
| NSKCH-09 | import_svg imports vector art | smoke | `import_svg(filepath, ...)` with test SVG file | N/A Wave 0 |
| CNST-01 | constrain_horizontal makes line horizontal | smoke | `batch([create_sketch, draw_line, constrain_horizontal])` | N/A Wave 0 |
| CNST-02 | constrain_vertical makes line vertical | smoke | `batch([create_sketch, draw_line, constrain_vertical])` | N/A Wave 0 |
| CNST-03 | constrain_perpendicular between two lines | smoke | `batch([create_sketch, draw_line x2, constrain_perpendicular])` | N/A Wave 0 |
| CNST-04 | constrain_parallel between two lines | smoke | `batch([create_sketch, draw_line x2, constrain_parallel])` | N/A Wave 0 |
| CNST-05 | constrain_tangent between curve and line | smoke | `batch([create_sketch, draw_circle, draw_line, constrain_tangent])` | N/A Wave 0 |
| CNST-06 | constrain_coincident point to curve | smoke | `batch([create_sketch, draw_line x2, constrain_coincident])` | N/A Wave 0 |
| CNST-07 | constrain_concentric two circles | smoke | `batch([create_sketch, draw_circle x2, constrain_concentric])` | N/A Wave 0 |
| CNST-08 | constrain_equal two lines same length | smoke | `batch([create_sketch, draw_line x2, constrain_equal])` | N/A Wave 0 |
| CNST-09 | constrain_symmetric across axis | smoke | `batch([create_sketch, draw_line x3, constrain_symmetric])` | N/A Wave 0 |
| DIM-01 | dimension_distance sets linear dimension | smoke | `batch([create_sketch, draw_line, dimension_distance])` | N/A Wave 0 |
| DIM-02 | dimension_radial sets radius/diameter | smoke | `batch([create_sketch, draw_circle, dimension_radial])` | N/A Wave 0 |
| DIM-03 | dimension_angular sets angle between lines | smoke | `batch([create_sketch, draw_line x2, dimension_angular])` | N/A Wave 0 |

### Sampling Rate
- **Per task commit:** Verify handler loads without import error via quick batch test
- **Per wave merge:** Run full test sequence covering all new tools
- **Phase gate:** All 21 new tools + get_sketch_info respond successfully; existing draw tools still return entity indices

### Wave 0 Gaps
- [ ] `helpers/sketch_entities.py` -- curve/point indexing and labeling utilities (must create before any implementation)
- [ ] Test SVG file for NSKCH-09 validation
- [ ] No automated test framework -- all testing is manual via MCP calls to running Fusion 360 instance

## Sources

### Primary (HIGH confidence)
- [Autodesk Fusion 360 API - GeometricConstraints](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GeometricConstraints.htm) -- all constraint method names and parameters
- [Autodesk Fusion 360 API - SketchEllipses.add](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchEllipses_add.htm) -- ellipse creation API
- [Autodesk Fusion 360 API - Sketch.importSVG](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_importSVG.htm) -- SVG import API
- [Autodesk Fusion 360 API - Sketch.addCenterPointSlot](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_addCenterPointSlot.htm) -- slot creation API
- [Autodesk Fusion 360 API - SketchSplineThroughPoints Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchSplineThroughPoints_Sample.htm) -- spline creation
- [Autodesk Fusion 360 API - SketchText Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchTextSample_Sample.htm) -- text creation
- [Autodesk Fusion 360 API - SketchDimensions.addDistanceDimension](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchDimension_addDistanceDimension_Sample.htm) -- dimension creation
- [Autodesk Fusion 360 API - SketchFilletAndOffset Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchFilletAndOffset_Sample.htm) -- offset curves
- [Autodesk Fusion 360 API - Sketch.project](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_project.htm) -- geometry projection
- [Autodesk Fusion 360 API - SketchLine.isConstruction](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchLine_isConstruction.htm) -- construction toggle
- [Autodesk Fusion 360 API - SketchPoint Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SketchPointSample_Sample.htm) -- point creation
- Existing codebase: handlers/sketch.py, helpers/coordinates.py, helpers/selection.py, helpers/bodies.py

### Secondary (MEDIUM confidence)
- [Autodesk Community Forum - offset curves](https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/create-a-parametric-curves-offset-from-python-api/td-p/9391531) -- offset API usage patterns
- [Autodesk Community Forum - dimensioning programmatically](https://forums.autodesk.com/t5/fusion-api-and-scripts/how-to-dimension-sketch-elements-programmatically/td-p/9250980) -- dimension patterns

### Tertiary (LOW confidence)
- addSymmetry exact parameter types -- inferred from API pattern but not verified against official docs page

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Fusion 360 API is the only option; all methods verified against official docs
- Architecture: HIGH -- follows established Phase 1 patterns with clear extension points
- Pitfalls: MEDIUM -- curve index stability needs runtime verification; most pitfalls from official docs review
- API signatures: HIGH for most methods, LOW for addSymmetry parameters

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (Fusion 360 API is stable; updates are infrequent)
