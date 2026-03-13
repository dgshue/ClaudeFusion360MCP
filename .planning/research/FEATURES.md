# Feature Landscape

**Domain:** Fusion 360 MCP Server - AI-driven CAD automation
**Researched:** 2026-03-13

## Current State

The MCP server defines 39 tools but only 9 have working add-in handlers:
- **Working (9):** `create_sketch`, `draw_circle`, `draw_rectangle`, `extrude`, `revolve`, `fillet`, `finish_sketch`, `fit_view`, `get_design_info`
- **Defined but broken (30):** Every other tool returns "Unknown tool" from the add-in dispatcher

Known bugs in working handlers:
- `fillet` ignores `edges` parameter (always fillets ALL edges)
- `create_sketch` ignores `offset` parameter
- `extrude` ignores `profile_index` and `taper_angle` parameters
- `revolve` hardcodes Y axis (no axis selection)
- `get_design_info` doesn't return component count
- Bare `except: pass` blocks swallow errors silently in the monitor thread

## Table Stakes

Features users expect. Missing = tool is incomplete for basic CAD work.

### Tier 1: Fix What's Declared (Close the 30-Tool Gap)

These tools already have MCP server definitions but no add-in handlers. They are the highest priority because users will discover them, call them, and get "Unknown tool" errors.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `draw_line` handler | Basic sketch primitive | Low | Already defined in MCP server |
| `draw_arc` handler | Arcs are fundamental to any non-rectangular design | Low | Already defined |
| `draw_polygon` handler | Common for hex nuts, decorative shapes | Low | Already defined |
| `chamfer` handler | Complement to fillet, equally fundamental | Low | Already defined; model after fillet handler |
| `shell` handler | Hollowing bodies is core for enclosures, containers | Medium | Need face index selection via BRepFaces |
| `draft` handler | Draft angles for manufacturing | Medium | Uses DraftFeatures API |
| `pattern_rectangular` handler | Linear arrays are constant in CAD | Medium | Uses RectangularPatternFeatures |
| `pattern_circular` handler | Radial arrays (bolt circles, etc.) | Medium | Uses CircularPatternFeatures |
| `mirror` handler | Symmetry is used in nearly every design | Medium | Uses MirrorFeatures |
| `get_body_info` handler | Required for selective edge/face operations | Medium | Must enumerate BRepEdges and BRepFaces |
| `measure` handler | Verify dimensions, critical for iterative design | Medium | Use BRepBody.physicalProperties |
| `create_component` handler | Assembly foundation | Medium | Use rootComp.occurrences.addNewComponent |
| `list_components` handler | Query assembly structure | Low | Iterate rootComp.occurrences |
| `delete_component` handler | Clean up assembly | Low | Use occurrence.deleteMe() |
| `move_component` handler | Position parts in assembly | Medium | Use occurrence.transform with Matrix3D |
| `rotate_component` handler | Orient parts | Medium | Matrix3D rotation transforms |
| `check_interference` handler | Verify assembly fit | Medium | Bounding box collision as spec'd |
| `create_revolute_joint` handler | Rotating connections (hinges, pivots) | High | JointInput with RevoluteJointMotion |
| `create_slider_joint` handler | Linear motion connections | High | JointInput with SliderJointMotion |
| `set_joint_angle` handler | Drive revolute joints | Medium | Set RevoluteJointMotion.rotationValue |
| `set_joint_distance` handler | Drive slider joints | Medium | Set SliderJointMotion.slideValue |
| `combine` handler | Boolean ops (cut/join/intersect) | Medium | CombineFeatures API |
| `undo` handler | Error recovery | Low | app.executeTextCommand("Commands.Undo") |
| `delete_body` handler | Clean up bodies | Low | body.deleteMe() |
| `delete_sketch` handler | Clean up sketches | Low | sketch.deleteMe() |
| `export_stl` handler | 3D printing output | Medium | STLExportOptions API |
| `export_step` handler | CAD interchange | Medium | STEPExportOptions API |
| `export_3mf` handler | Modern 3D print format | Medium | ThreeMFExportOptions API |
| `import_mesh` handler | Bring in external geometry | Medium | MeshBody import API |
| Fix `fillet` edges parameter | Already declared but ignored | Low | Filter body.edges by index list |

### Tier 2: Missing Sketch Primitives

These are sketch operations the Fusion 360 API supports that any serious CAD tool needs, but the MCP server doesn't even define yet.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `draw_spline` | Organic curves, aerodynamic shapes, ergonomic profiles | Medium | SketchFittedSplines.add() with Point3D collection |
| `draw_ellipse` | Common in industrial design | Low | SketchEllipses.add() |
| `draw_slot` | Mechanical features (mounting slots) | Low | Sketch has addCenterPointSlot, addOverallSlot |
| `draw_point` | Reference geometry, spline control | Low | SketchPoints.add() |
| `offset_curves` | Parallel profiles at uniform distance | Medium | Sketch.offset() to create offset curve set |
| `draw_text` | Engrave text, labels on parts | Medium | SketchTexts.add() - can be extruded for emboss |
| `set_construction` | Toggle lines to construction geometry | Low | SketchEntity.isConstruction = True |
| `project_geometry` | Project edges/faces onto sketch plane | Medium | Sketch.project() or Sketch.intersectWithSketchPlane() |
| `import_svg` | Vector art import for logos, decorative features | Medium | Sketch.importSVG() |

### Tier 3: Missing 3D Features

Core modeling operations that the Fusion 360 API exposes but the server lacks entirely.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `sweep` | Extrude profile along path (pipes, rails, channels) | High | SweepFeatures API; needs path + profile |
| `loft` | Blend between 2+ profiles (bottles, airfoils, transitions) | High | LoftFeatures API; needs multiple sections |
| `hole` | Standard, counterbore, countersink holes by spec | Medium | HoleFeatures API; parametric hole standards |
| `thread` | Apply threads to cylindrical faces | Medium | ThreadFeatures API; standard thread data |
| `construction_plane` | Offset/angled reference planes for sketches | Medium | ConstructionPlanes API; critical for lofts |
| `construction_axis` | Reference axes | Low | ConstructionAxes API |
| `construction_point` | Reference points | Low | ConstructionPoints API |

### Tier 4: Sketch Constraints and Dimensions

Without constraints and dimensions, sketches are imprecise. For AI-driven design this is medium priority because the AI can place geometry precisely by coordinates, but for parametric design iteration they become essential.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `add_dimension` (distance) | Lock distances between entities | Medium | SketchDimensions.addDistanceDimension() |
| `add_dimension` (diameter/radius) | Size circles precisely | Low | addDiameterDimension(), addRadialDimension() |
| `add_dimension` (angular) | Lock angles | Medium | addAngularDimension() |
| `add_constraint` (horizontal) | Align entities horizontally | Low | GeometricConstraints.addHorizontal() |
| `add_constraint` (vertical) | Align vertically | Low | GeometricConstraints.addVertical() |
| `add_constraint` (perpendicular) | Right angle relationships | Low | addPerpendicular() |
| `add_constraint` (parallel) | Parallel relationships | Low | addParallel() |
| `add_constraint` (tangent) | Smooth transitions between curves | Low | addTangent() |
| `add_constraint` (coincident) | Lock points together | Low | addCoincident() |
| `add_constraint` (concentric) | Align circles/arcs | Low | addConcentric() |
| `add_constraint` (equal) | Make entities same size | Low | addEqual() |
| `add_constraint` (symmetric) | Mirror about centerline | Low | addSymmetry() |

## Differentiators

Features that set this MCP server apart from competitors. Not expected but high value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Batch operations (existing) | 5-10x faster for multi-step workflows; already implemented in MCP server | Low | Already defined, handler exists but needs verification |
| `create_parameter` / `set_parameter` | Parametric design - change one value, whole model updates. This is the killer feature competitors lack | Medium | UserParameters API; enables true parametric workflows |
| `get_timeline` / `edit_at_timeline` | Roll back design history, insert/modify features at any point | High | Timeline API; powerful but complex |
| MCP Resource endpoints | Serve API docs, tutorials, examples as MCP resources so AI can self-teach | Medium | FastMCP @mcp.resource(); no competitor does this well |
| Workflow skills/guides | "How to make a finger joint", "Design a gear" as structured prompts | Low | @mcp.prompt() definitions; encode domain expertise |
| `capture_screenshot` | Visual feedback - see what was built without switching to Fusion | Medium | Viewport.saveAsImageFile(); AI gets visual confirmation |
| `create_named_selection` | Save edge/face selections by name for reuse across operations | Medium | Custom tracking via attributes or named groups |
| `set_appearance` | Apply materials/colors to bodies/faces | Medium | Appearance API; visual differentiation of parts |
| `section_analysis` | Cross-section views for inspection | Medium | SectionAnalysis API |
| `mass_properties` | Center of mass, moments of inertia for engineering analysis | Low | PhysicalProperties from BRepBody |
| Rigid joint handler | Ground/fix components in assemblies | Medium | Joint with RigidJointMotion |
| Cylindrical joint handler | Rotation + translation (pistons, screws) | High | CylindricalJointMotion |
| Pin-slot joint handler | Pin in slot motion | High | PinSlotJointMotion |
| `create_sketch_on_face` | Sketch directly on body faces (not just planes) | Medium | Sketches.add(face) where face is BRepFace |

## Anti-Features

Features to explicitly NOT build. Adding these would add complexity without value for the use case.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| CAM/Toolpath generation | Out of scope per PROJECT.md; massive API surface (280+ classes in adsk.cam); personal tooling doesn't need CNC programming | Export STEP/STL and use dedicated CAM software |
| Sheet metal features | Specialized domain with complex rules (bend radius, K-factor); defer per PROJECT.md | Model as solid bodies; convert in Fusion UI if needed |
| T-spline/form editing | Completely different modeling paradigm; adsk.fusion.FormFeature is complex and brittle | Use standard solid modeling; T-splines are for organic shapes rarely needed in functional parts |
| Mesh editing operations | Low-level mesh manipulation (sculpting, remeshing) is a rabbit hole | Import meshes as-is; do mesh work in dedicated tools |
| Simulation/FEA | Stress analysis, thermal, modal - entirely separate domain | Use Fusion's built-in simulation UI |
| Rendering | Raytracing, scene setup, lighting - not part of modeling workflow | Use Fusion's render workspace directly |
| Multi-document management | Opening/closing/saving documents adds state complexity | Assume one active design; user manages documents |
| Real-time collaboration | Multi-user editing is out of scope | Personal tooling only |
| Custom UI panels in Fusion | Building Fusion UI is a distraction from the MCP tool value | All interaction through MCP tools |
| Arbitrary Python execution | Security risk; hard to debug; unpredictable side effects | Expose specific, well-tested tool operations |

## Feature Dependencies

```
Core Infrastructure:
  fix_error_handling --> all_other_features (bare except blocks must go first)
  batch_handler --> all_tools (batch dispatches to individual handlers)

Sketch Layer:
  create_sketch --> draw_* (all sketch geometry requires active sketch)
  draw_* --> finish_sketch --> extrude/revolve/sweep/loft (features consume sketch profiles)
  draw_spline --> draw_point (splines use point collections)
  set_construction --> draw_* (toggle existing entities)
  project_geometry --> create_sketch (needs active sketch)

Feature Layer:
  construction_plane --> create_sketch (sketches on offset planes for lofts)
  construction_plane + create_sketch (x2+) --> loft (loft needs profiles on different planes)
  draw_* + finish_sketch --> sweep (needs both profile sketch and path sketch)
  extrude/revolve --> shell, draft, fillet, chamfer (modifiers need existing bodies)
  extrude/revolve --> pattern_rectangular, pattern_circular, mirror (patterns need bodies)
  extrude/revolve --> combine (boolean ops need 2+ bodies)
  get_body_info --> fillet(edges), chamfer(edges), shell(faces), draft(faces) (selective operations need index discovery)

Assembly Layer:
  create_component --> move_component, rotate_component (positioning needs components)
  create_component (x2) --> create_*_joint (joints need 2 components)
  create_revolute_joint --> set_joint_angle (drive needs existing joint)
  create_slider_joint --> set_joint_distance (drive needs existing joint)
  list_components --> check_interference (need to know what exists)

Export Layer:
  extrude/revolve (bodies exist) --> export_stl, export_step, export_3mf
  import_mesh --> get_body_info (inspect imported geometry)

Inspection Layer:
  get_body_info --> measure (need indices for targeted measurement)
  get_design_info --> all_operations (situational awareness)
```

## MVP Recommendation

### Phase 1: Fix What's Broken (Close the Gap)
Implement all 30 missing handlers for already-declared MCP tools. This is the single highest-value activity because:
1. Users already discover these tools
2. "Unknown tool" errors destroy trust
3. The MCP server API design is already done
4. Most handlers are Low-Medium complexity

Priority order within Phase 1:
1. **Fix error handling** - Replace bare `except: pass` with proper error propagation
2. **Sketch primitives** - `draw_line`, `draw_arc`, `draw_polygon` (unlock more geometry)
3. **Fix existing handler bugs** - fillet edges, create_sketch offset, extrude profile_index/taper_angle, revolve axis
4. **Remaining 3D features** - `chamfer`, `shell`, `draft`, `combine`
5. **Patterns** - `pattern_rectangular`, `pattern_circular`, `mirror`
6. **Inspection** - `get_body_info`, `measure`
7. **Components** - `create_component`, `list_components`, `delete_component`, `move_component`, `rotate_component`, `check_interference`
8. **Joints** - `create_revolute_joint`, `create_slider_joint`, `set_joint_angle`, `set_joint_distance`
9. **Utilities** - `undo`, `delete_body`, `delete_sketch`
10. **Import/Export** - `export_stl`, `export_step`, `export_3mf`, `import_mesh`

### Phase 2: Expand Sketch Coverage
Add missing sketch primitives: `draw_spline`, `draw_ellipse`, `draw_slot`, `draw_point`, `offset_curves`, `draw_text`, `set_construction`, `project_geometry`

### Phase 3: Expand 3D Features
Add `sweep`, `loft`, `hole`, `thread`, `construction_plane`, `construction_axis`, `construction_point`

### Phase 4: Parametric & Discoverability
Add `create_parameter`/`set_parameter`, MCP resource endpoints, workflow skills/guides, `capture_screenshot`

Defer: Sketch constraints/dimensions (Phase 5) - the AI can place geometry precisely by coordinates; constraints become important only for parametric iteration workflows.

## Sources

- [Fusion 360 API Documentation](http://autodeskfusion360.github.io/) - HIGH confidence
- [Fusion 360 API Reference Manual](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC) - HIGH confidence
- [Sketch Object API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch.htm) - HIGH confidence
- [Loft Feature API Sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/LoftFeatureSample_Sample.htm) - HIGH confidence
- [Sweep with Guide Rail Sample](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-%7B11E9EECC-1641-4BF0-8C81-BDD178CF8C3A%7D) - HIGH confidence
- [Joint Types Reference](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-8818AE31-958A-4A59-989B-9875A174C67A) - HIGH confidence
- [AuraFriday Fusion 360 MCP Server](https://github.com/AuraFriday/Fusion-360-MCP-Server) - competitor reference
- [Joe Spencer fusion-mcp-server](https://github.com/Joe-Spencer/fusion-mcp-server) - competitor reference (only 3 tools)
- [9 MCP Servers for CAD](https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai/) - market landscape

---

*Feature landscape audit: 2026-03-13*
