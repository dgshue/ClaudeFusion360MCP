# Phase 3: Advanced 3D Features - Research

**Researched:** 2026-03-15
**Domain:** Fusion 360 API - Sweep, Loft, Hole, Thread, Construction Geometry
**Confidence:** HIGH

## Summary

Phase 3 adds seven new tool+handler pairs for advanced 3D features: sweep, loft, hole, thread, construction plane, construction axis, and construction point. All follow the established handler pattern from Phases 1-2 (handler function in `fusion-addin/handlers/`, MCP tool in `mcp-server/fusion360_mcp_server.py`, registration in `HANDLER_MAP`).

The Fusion 360 API has mature, well-documented support for all seven features. Sweep and loft require profile+path/section references which adds complexity for entity selection. Holes use sketch points for positioning. Threads require querying the ThreadDataQuery for valid thread types. Construction geometry is straightforward with multiple creation modes (offset, angle, through points).

**Primary recommendation:** Group implementation into 3 plans: (1) construction geometry (planes/axes/points - foundational, needed by loft), (2) sweep + loft (profile-path features), (3) hole + thread (manufacturing features). Construction geometry first because loft typically needs offset planes for multi-section profiles.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NFEAT-01 | `sweep` tool and handler for extruding profiles along paths | SweepFeatures API with createInput(profile, path, operation), supports taper/twist angles |
| NFEAT-02 | `loft` tool and handler for blending between 2+ profiles | LoftFeatures API with loftSections.add(), supports isSolid, isClosed, edge alignment |
| NFEAT-03 | `hole` tool and handler for standard/counterbore/countersink holes | HoleFeatures API with createSimpleInput/createCounterboreInput/createCountersinkInput |
| NFEAT-04 | `thread` tool and handler for applying threads to cylindrical faces | ThreadFeatures API with createInput(face, threadInfo), requires ThreadDataQuery for valid specs |
| NFEAT-05 | `construction_plane` tool and handler for offset/angled reference planes | ConstructionPlanes API with setByOffset, setByAngle, setByTwoPlanes, etc. |
| NFEAT-06 | `construction_axis` tool and handler for reference axes | ConstructionAxes API with setByTwoPoints, setByNormalToFace, etc. |
| NFEAT-07 | `construction_point` tool and handler for reference points | ConstructionPoints API with setByPoint, setByEdgeAndFace, etc. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| adsk.fusion | Fusion 360 embedded | All 3D feature creation APIs | Only option for Fusion 360 add-ins |
| adsk.core | Fusion 360 embedded | Point3D, ValueInput, ObjectCollection | Required for geometry/value creation |

### Supporting (existing project infrastructure)
| Library | Purpose | When to Use |
|---------|---------|-------------|
| helpers/bodies.py | get_body, get_sketch, get_occurrence | Body/sketch lookup for all handlers |
| helpers/selection.py | resolve_edges, resolve_faces | Face selection for threads, hole positioning |
| helpers/errors.py | wrap_handler | Error wrapping for all handlers |

### No New Dependencies
All features use existing Fusion 360 API classes. No new libraries needed.

## Architecture Patterns

### Recommended File Structure
```
fusion-addin/handlers/
    feature.py          # ADD: sweep, loft (profile-based features, alongside extrude/revolve)
    construction.py     # NEW: construction_plane, construction_axis, construction_point
    hole_thread.py      # NEW: hole, thread (manufacturing features)
```

Alternative: All in `feature.py`. Given feature.py already has 10 handlers (296 lines), splitting into separate files is cleaner but either works.

### Pattern: Handler + MCP Tool (established)

**Handler side** (fusion-addin/handlers/):
```python
def sweep(design, rootComp, params):
    # 1. Get sketch/profile
    # 2. Get path
    # 3. Create input via API
    # 4. Configure options
    # 5. Add feature
    # 6. Return {"success": True, "feature_name": ...}
```

**MCP tool side** (mcp-server/):
```python
@mcp.tool()
def sweep(profile_index: int = 0, path_sketch_index: int = None,
          path_curve_index: int = 0, taper_angle: float = 0,
          twist_angle: float = 0) -> dict:
    """Sweep a sketch profile along a path curve..."""
    return send_fusion_command("sweep", {...})
```

**Registration** (handlers/__init__.py):
```python
from .feature import sweep, loft  # or from new module
HANDLER_MAP['sweep'] = sweep
```

### Pattern: Path Creation for Sweep
The Fusion API requires a `Path` object for sweep. Key API call:
```python
path = rootComp.features.createPath(sketch_curve)
# sketch_curve is a SketchLine, SketchArc, etc. from the path sketch
```
The path can be open or closed. Connected curves are automatically chained.

### Pattern: Multi-Section Loft
Loft sections are added one at a time to the loft input:
```python
loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
loftInput.loftSections.add(profile0)  # from sketch on plane 1
loftInput.loftSections.add(profile1)  # from sketch on offset plane
loftInput.isSolid = True
```
Profiles must come from different sketches on different planes.

### Pattern: Hole Positioning via Sketch Points
Holes are positioned using sketch points, not x/y/z coordinates directly:
```python
holeInput = holes.createSimpleInput(adsk.core.ValueInput.createByString('5 mm'))
ptColl = adsk.core.ObjectCollection.create()
ptColl.add(sketch_point)  # SketchPoint object
holeInput.setPositionBySketchPoints(ptColl)
holeInput.setDistanceExtent(adsk.core.ValueInput.createByReal(depth))
```

### Pattern: Thread Data Query
Threads require querying valid thread specifications:
```python
threadFeats = rootComp.features.threadFeatures
threadDataQuery = threadFeats.threadDataQuery
threadTypes = threadDataQuery.allThreadTypes  # e.g., "ISO Metric profile"
allSizes = threadDataQuery.allSizes(threadType)
allDesignations = threadDataQuery.allDesignations(threadType, size)
threadInfo = threadFeats.createThreadInfo(isInternal, threadType, designation, threadClass)
```

### Anti-Patterns to Avoid
- **Hardcoding thread specifications:** Always use ThreadDataQuery to validate thread type/size/designation combinations
- **Assuming profile sketch is path sketch:** Sweep requires profile and path from DIFFERENT sketches
- **Creating loft profiles on same plane:** Each loft section must be on a distinct plane
- **Using coordinates for hole position:** Holes require SketchPoint objects, not raw coordinates

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path creation | Manual curve chaining | `rootComp.features.createPath(curve)` | Auto-chains connected curves |
| Thread specs | Hardcoded thread tables | `ThreadDataQuery` | Fusion maintains thread database |
| Hole types | Manual cylinder+counterbore geometry | `HoleFeatures.createCounterboreInput()` | Handles all geometry automatically |
| Construction plane math | Matrix3D plane calculations | `ConstructionPlaneInput.setByOffset()` | API handles all transform math |

## Common Pitfalls

### Pitfall 1: Sweep Path Must Be in Different Sketch Than Profile
**What goes wrong:** Putting profile and path in the same sketch causes sweep to fail
**Why it happens:** Fusion requires separate sketch contexts for profile and path geometry
**How to avoid:** Handler must accept separate sketch references for profile and path
**Warning signs:** "Failed to create sweep" with no further detail

### Pitfall 2: Loft Section Order Matters
**What goes wrong:** Sections added in wrong order create twisted or self-intersecting geometry
**Why it happens:** Loft connects sections in the order they are added
**How to avoid:** Accept sketch indices as ordered list, validate they are on distinct planes

### Pitfall 3: Thread Face Must Be Cylindrical
**What goes wrong:** Applying thread to non-cylindrical face throws exception
**Why it happens:** Threads can only be applied to cylindrical BRepFace geometry
**How to avoid:** Validate face geometry type before creating thread input

### Pitfall 4: Hole Depth vs. Through-All
**What goes wrong:** Hole doesn't penetrate body or goes too deep
**Why it happens:** Hole depth is from the sketch plane, not from the face
**How to avoid:** Support both distance extent and "through all" (`setAllExtent()`) modes

### Pitfall 5: Construction Plane Offset Units
**What goes wrong:** Offset values interpreted incorrectly
**Why it happens:** `ValueInput.createByString("10 cm")` vs `createByReal(10)` -- createByReal uses internal units (cm)
**How to avoid:** Use `createByReal()` consistently since project uses cm throughout

### Pitfall 6: Hole Requires Active Sketch Points
**What goes wrong:** Holes fail when using sketch points from a finished/non-active sketch
**Why it happens:** Sketch points need to be accessible; the sketch containing them should exist
**How to avoid:** Handler should create a sketch on the target face, add points, then create holes

## Code Examples

### Sweep Feature
```python
# Source: Autodesk Fusion 360 API docs - Sweep Feature Sample
def sweep(design, rootComp, params):
    # Get profile from profile sketch
    profile_sketch = rootComp.sketches.item(params.get('profile_sketch_index',
                                            rootComp.sketches.count - 1))
    profile = profile_sketch.profiles.item(params.get('profile_index', 0))

    # Get path from path sketch
    path_sketch_idx = params.get('path_sketch_index')
    path_sketch = rootComp.sketches.item(path_sketch_idx)
    path_curve = path_sketch.sketchCurves.item(params.get('path_curve_index', 0))
    path = rootComp.features.createPath(path_curve)

    sweeps = rootComp.features.sweepFeatures
    sweep_input = sweeps.createInput(
        profile, path,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    taper = params.get('taper_angle', 0)
    if taper != 0:
        sweep_input.taperAngle = adsk.core.ValueInput.createByString(f"{taper} deg")

    twist = params.get('twist_angle', 0)
    if twist != 0:
        sweep_input.twistAngle = adsk.core.ValueInput.createByString(f"{twist} deg")

    feat = sweeps.add(sweep_input)
    return {"success": True, "feature_name": feat.name}
```

### Loft Feature
```python
# Source: Autodesk Fusion 360 API docs - Loft Feature Sample
def loft(design, rootComp, params):
    sketch_indices = params['sketch_indices']  # List of sketch indices
    profile_indices = params.get('profile_indices', [0] * len(sketch_indices))

    loftFeats = rootComp.features.loftFeatures
    loftInput = loftFeats.createInput(
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    for i, sk_idx in enumerate(sketch_indices):
        sketch = rootComp.sketches.item(sk_idx)
        prof_idx = profile_indices[i] if i < len(profile_indices) else 0
        profile = sketch.profiles.item(prof_idx)
        loftInput.loftSections.add(profile)

    loftInput.isSolid = params.get('is_solid', True)
    loftInput.isClosed = params.get('is_closed', False)

    feat = loftFeats.add(loftInput)
    return {"success": True, "feature_name": feat.name}
```

### Construction Plane (Offset)
```python
# Source: Autodesk Fusion 360 API docs - Construction Plane Sample
def construction_plane(design, rootComp, params):
    planes = rootComp.constructionPlanes
    plane_input = planes.createInput()

    mode = params.get('mode', 'offset')
    if mode == 'offset':
        # Get base plane
        base_plane_name = params.get('plane', 'XY').upper()
        plane_map = {
            'XY': rootComp.xYConstructionPlane,
            'XZ': rootComp.xZConstructionPlane,
            'YZ': rootComp.yZConstructionPlane
        }
        base = plane_map.get(base_plane_name, rootComp.xYConstructionPlane)
        offset = adsk.core.ValueInput.createByReal(params.get('offset', 1.0))
        plane_input.setByOffset(base, offset)
    elif mode == 'angle':
        # Angle from plane around an axis
        # plane_input.setByAngle(linearEntity, angle, planarEntity)
        pass

    plane = planes.add(plane_input)
    return {"success": True, "name": plane.name}
```

### Hole Feature
```python
# Source: Autodesk Fusion 360 API docs - Hole Feature Sample
def hole(design, rootComp, params):
    hole_type = params.get('type', 'simple')  # simple, counterbore, countersink
    diameter = adsk.core.ValueInput.createByReal(params['diameter'])

    holes = rootComp.features.holeFeatures

    if hole_type == 'simple':
        hole_input = holes.createSimpleInput(diameter)
    elif hole_type == 'counterbore':
        cb_diameter = adsk.core.ValueInput.createByReal(params['counterbore_diameter'])
        cb_depth = adsk.core.ValueInput.createByReal(params['counterbore_depth'])
        hole_input = holes.createCounterboreInput(diameter, cb_diameter, cb_depth)
    elif hole_type == 'countersink':
        cs_diameter = adsk.core.ValueInput.createByReal(params['countersink_diameter'])
        cs_angle = adsk.core.ValueInput.createByString(f"{params['countersink_angle']} deg")
        hole_input = holes.createCountersinkInput(diameter, cs_diameter, cs_angle)

    # Position by sketch points or face point
    # ... (see Architecture Patterns)

    depth = adsk.core.ValueInput.createByReal(params['depth'])
    hole_input.setDistanceExtent(depth)
    feat = holes.add(hole_input)
    return {"success": True, "feature_name": feat.name}
```

### Thread Feature
```python
# Source: Autodesk Fusion 360 API docs - Thread Feature Sample
def thread(design, rootComp, params):
    body = get_body(rootComp, params.get('body_index'))
    face = resolve_faces(body, [params['face']])[0]

    threadFeats = rootComp.features.threadFeatures
    threadType = params.get('thread_type', 'ISO Metric profile')
    size = params.get('size', '6')
    designation = params.get('designation', 'M6x1.0')
    threadClass = params.get('thread_class', '6g')
    isInternal = params.get('is_internal', False)

    threadInfo = threadFeats.createThreadInfo(
        isInternal, threadType, designation, threadClass
    )

    faces = adsk.core.ObjectCollection.create()
    faces.add(face)
    threadInput = threadFeats.createInput(faces, threadInfo)
    threadInput.isFullLength = params.get('full_length', True)

    feat = threadFeats.add(threadInput)
    return {"success": True, "feature_name": feat.name}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HoleFeatures.createInput | createSimpleInput/createCounterboreInput/createCountersinkInput | Recent API | Type-specific creation methods are clearer |
| Manual thread geometry | ThreadFeatures + ThreadDataQuery | Stable | Built-in thread database with standard specs |

## Open Questions

1. **Hole positioning UX**
   - What we know: API requires SketchPoint objects for positioning
   - What's unclear: Should the handler auto-create a sketch on a face, or require the user to provide sketch points?
   - Recommendation: Accept (x, y, face_index) and auto-create sketch + point internally. This is much simpler for the AI caller.

2. **Thread type discovery**
   - What we know: ThreadDataQuery can list all types/sizes/designations
   - What's unclear: Should we expose a query tool for thread types?
   - Recommendation: Accept common parameters (thread_type, designation, thread_class) with sensible defaults (ISO Metric). Add a `list_thread_types` query tool only if needed later.

3. **Sweep path from multiple sketches**
   - What we know: createPath can chain connected curves in one sketch
   - What's unclear: Can path span curves across sketches?
   - Recommendation: Keep it simple -- path from single sketch. User can draw full path in one sketch.

4. **Construction geometry input modes**
   - What we know: API supports many creation modes (offset, angle, two planes, through points, etc.)
   - What's unclear: Which modes are most useful for MCP callers?
   - Recommendation: Start with offset mode (most common). Add angle mode. Defer exotic modes.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual testing in Fusion 360 (no automated test framework) |
| Config file | none |
| Quick run command | Manual: call MCP tool via Claude, verify in Fusion 360 |
| Full suite command | Manual: run through all success criteria scenarios |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NFEAT-01 | Sweep profile along path | manual-only | Call sweep tool, verify geometry in Fusion | N/A |
| NFEAT-02 | Loft between 2+ profiles | manual-only | Call loft tool with multiple sketch indices | N/A |
| NFEAT-03 | Hole (simple/counterbore/countersink) | manual-only | Call hole tool with each type | N/A |
| NFEAT-04 | Thread on cylindrical face | manual-only | Create cylinder, apply thread | N/A |
| NFEAT-05 | Construction plane (offset/angle) | manual-only | Create offset plane, sketch on it | N/A |
| NFEAT-06 | Construction axis | manual-only | Create axis, use in pattern | N/A |
| NFEAT-07 | Construction point | manual-only | Create point, verify position | N/A |

**Justification for manual-only:** Fusion 360 API can only execute inside the Fusion 360 runtime. No headless test mode exists. All verification requires visual inspection in the Fusion 360 UI.

### Sampling Rate
- **Per task commit:** Manual smoke test of the implemented handler via MCP tool call
- **Per wave merge:** Run through all success criteria scenarios
- **Phase gate:** All 4 success criteria verified manually

### Wave 0 Gaps
None -- no automated test infrastructure applicable (Fusion 360 embedded Python runtime only).

## Sources

### Primary (HIGH confidence)
- [Sweep Feature API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SweepFeatureSample_Sample.htm) - Official Autodesk sample
- [Loft Feature API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/LoftFeatureSample_Sample.htm) - Official Autodesk sample
- [Hole Feature API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/HoleFeatureSample_Sample.htm) - Official Autodesk sample
- [Thread Feature API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ThreadFeatureSample_Sample.htm) - Official Autodesk sample
- [Construction Plane API Sample](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-c4edd2d2-aea3-11e5-98bc-f8b156d7cd97) - Official Autodesk sample
- [ThreadFeatures.createInput Method](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ThreadFeatures_createInput.htm) - API reference
- [ThreadFeatures.createThreadInfo Method](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ThreadFeatures_createThreadInfo.htm) - API reference

### Secondary (MEDIUM confidence)
- Existing project codebase (Phases 1-2) - established patterns for handler/tool/registration

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using only built-in Fusion 360 API, same as all prior phases
- Architecture: HIGH - follows exact same handler+tool+registration pattern from Phases 1-2
- Pitfalls: HIGH - verified against official API samples and project experience
- API details: MEDIUM - some hole/thread parameter combinations need runtime validation

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (Fusion 360 API is stable, changes infrequently)
