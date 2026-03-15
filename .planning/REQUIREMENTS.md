# Requirements: ClaudeFusion360MCP

**Defined:** 2026-03-13
**Core Value:** Every MCP tool must work end-to-end with no "Unknown tool" dead ends

## v1 Requirements

### Foundation & Infrastructure

- [x] **INFRA-01**: Add-in uses CustomEvent pattern so all Fusion API calls execute on main thread (no threading violations)
- [x] **INFRA-02**: All bare `except: pass` blocks replaced with proper error propagation that returns actionable error messages
- [x] **INFRA-03**: Add-in restructured into domain handler modules (sketch, feature, assembly, query, utility) with dict-based dispatch
- [x] **INFRA-04**: Coordinate transformation layer handles XZ plane Y-axis inversion transparently
- [x] **INFRA-05**: Face/edge semantic selection helpers identify geometry by position/properties rather than fragile indices

### Bug Fixes (Existing Handlers)

- [x] **FIX-01**: `fillet` handler respects `edges` parameter for selective edge filleting
- [x] **FIX-02**: `extrude` handler respects `profile_index` and `taper_angle` parameters
- [x] **FIX-03**: `revolve` handler supports configurable axis selection (not hardcoded Y)
- [x] **FIX-04**: `create_sketch` handler respects `offset` parameter for offset sketch planes
- [x] **FIX-05**: `get_design_info` handler returns component count

### Missing Sketch Handlers (Close Gap)

- [x] **SKTCH-01**: `draw_line` handler draws lines between two points in active sketch
- [x] **SKTCH-02**: `draw_arc` handler draws arcs by center/start/end points
- [x] **SKTCH-03**: `draw_polygon` handler draws regular polygons by center/radius/sides

### Missing 3D Feature Handlers (Close Gap)

- [x] **FEAT-01**: `chamfer` handler applies chamfers to selected edges
- [x] **FEAT-02**: `shell` handler hollows bodies with selectable faces to remove
- [x] **FEAT-03**: `draft` handler applies draft angles to selected faces
- [x] **FEAT-04**: `pattern_rectangular` handler creates linear arrays of bodies/features
- [x] **FEAT-05**: `pattern_circular` handler creates radial arrays of bodies/features
- [x] **FEAT-06**: `mirror` handler mirrors bodies across selected plane
- [x] **FEAT-07**: `combine` handler performs boolean operations (cut/join/intersect)

### Missing Query Handlers (Close Gap)

- [x] **QUERY-01**: `get_body_info` handler returns detailed body info with edge/face indices
- [x] **QUERY-02**: `measure` handler returns volume, surface area, bounding box, edge length, face area

### Missing Component Handlers (Close Gap)

- [x] **COMP-01**: `create_component` handler creates new components in design
- [x] **COMP-02**: `list_components` handler returns all components with positions and bounding boxes
- [x] **COMP-03**: `delete_component` handler removes components by name or index
- [x] **COMP-04**: `move_component` handler positions components via Matrix3D translation
- [x] **COMP-05**: `rotate_component` handler orients components via Matrix3D rotation
- [x] **COMP-06**: `check_interference` handler detects collisions between components

### Missing Joint Handlers (Close Gap)

- [x] **JOINT-01**: `create_revolute_joint` handler creates rotating connections between components
- [x] **JOINT-02**: `create_slider_joint` handler creates linear motion connections
- [x] **JOINT-03**: `set_joint_angle` handler drives revolute joint rotation
- [x] **JOINT-04**: `set_joint_distance` handler drives slider joint position

### Missing Utility Handlers (Close Gap)

- [x] **UTIL-01**: `undo` handler undoes specified number of operations
- [x] **UTIL-02**: `delete_body` handler removes bodies from design
- [x] **UTIL-03**: `delete_sketch` handler removes sketches from design

### Missing Export/Import Handlers (Close Gap)

- [x] **IO-01**: `export_stl` handler exports bodies to STL format
- [x] **IO-02**: `export_step` handler exports bodies to STEP format
- [x] **IO-03**: `export_3mf` handler exports bodies to 3MF format
- [x] **IO-04**: `import_mesh` handler imports STL/OBJ/3MF mesh files

### New Sketch Primitives

- [x] **NSKCH-01**: `draw_spline` tool and handler for fitted splines through point collections
- [x] **NSKCH-02**: `draw_ellipse` tool and handler for ellipses
- [x] **NSKCH-03**: `draw_slot` tool and handler for center-point and overall slots
- [x] **NSKCH-04**: `draw_point` tool and handler for reference/construction points
- [x] **NSKCH-05**: `offset_curves` tool and handler for parallel profiles at uniform distance
- [x] **NSKCH-06**: `draw_text` tool and handler for sketch text (extrudable for embossing)
- [x] **NSKCH-07**: `set_construction` tool and handler to toggle entities to construction geometry
- [x] **NSKCH-08**: `project_geometry` tool and handler to project edges/faces onto sketch plane
- [x] **NSKCH-09**: `import_svg` tool and handler for vector art import into sketches

### Sketch Constraints

- [x] **CNST-01**: `add_constraint` tool and handler for horizontal constraints
- [x] **CNST-02**: `add_constraint` tool and handler for vertical constraints
- [x] **CNST-03**: `add_constraint` tool and handler for perpendicular constraints
- [x] **CNST-04**: `add_constraint` tool and handler for parallel constraints
- [x] **CNST-05**: `add_constraint` tool and handler for tangent constraints
- [x] **CNST-06**: `add_constraint` tool and handler for coincident constraints
- [x] **CNST-07**: `add_constraint` tool and handler for concentric constraints
- [x] **CNST-08**: `add_constraint` tool and handler for equal constraints
- [x] **CNST-09**: `add_constraint` tool and handler for symmetric constraints

### Sketch Dimensions

- [x] **DIM-01**: `add_dimension` tool and handler for distance dimensions
- [x] **DIM-02**: `add_dimension` tool and handler for diameter/radius dimensions
- [x] **DIM-03**: `add_dimension` tool and handler for angular dimensions

### New 3D Features

- [x] **NFEAT-01**: `sweep` tool and handler for extruding profiles along paths
- [x] **NFEAT-02**: `loft` tool and handler for blending between 2+ profiles
- [ ] **NFEAT-03**: `hole` tool and handler for standard/counterbore/countersink holes
- [ ] **NFEAT-04**: `thread` tool and handler for applying threads to cylindrical faces
- [x] **NFEAT-05**: `construction_plane` tool and handler for offset/angled reference planes
- [x] **NFEAT-06**: `construction_axis` tool and handler for reference axes
- [x] **NFEAT-07**: `construction_point` tool and handler for reference points

### Assembly Enhancement

- [ ] **ASSM-01**: `create_rigid_joint` tool and handler for fixed connections
- [ ] **ASSM-02**: `create_cylindrical_joint` tool and handler for rotation + translation motion
- [ ] **ASSM-03**: `create_pin_slot_joint` tool and handler for pin-in-slot motion
- [ ] **ASSM-04**: `create_planar_joint` tool and handler for planar sliding motion
- [ ] **ASSM-05**: `create_ball_joint` tool and handler for spherical rotation
- [ ] **ASSM-06**: `create_sketch_on_face` tool and handler for sketching directly on body faces

### Parametric Design

- [ ] **PARAM-01**: `create_parameter` tool and handler for creating named user parameters
- [ ] **PARAM-02**: `set_parameter` tool and handler for updating parameter values (model updates automatically)

### Timeline

- [ ] **TIME-01**: `get_timeline` tool and handler to retrieve design timeline with feature history
- [ ] **TIME-02**: `edit_at_timeline` tool and handler to roll back to a specific timeline position for editing
- [ ] **TIME-03**: `undo_to_marker` tool and handler to undo back to a named timeline marker

### Discoverability

- [ ] **DISC-01**: MCP Resource endpoints serving tool reference documentation per domain category
- [ ] **DISC-02**: MCP Resource endpoint serving coordinate system guide (units, XZ inversion, conventions)
- [ ] **DISC-03**: MCP Resource endpoints serving workflow guides (common shapes, assembly patterns)
- [ ] **DISC-04**: MCP Prompt templates for common CAD workflows (box, cylinder, enclosure, gear, etc.)
- [ ] **DISC-05**: All MCP tools have rich docstrings with parameter descriptions and usage examples

## v2 Requirements

### Advanced Features

- **ADV-01**: capture_screenshot for visual feedback
- **ADV-03**: set_appearance for materials/colors
- **ADV-04**: section_analysis for cross-section views
- **ADV-05**: mass_properties for center of mass and moments of inertia
- **ADV-06**: create_named_selection for reusable edge/face selections

## Out of Scope

| Feature | Reason |
|---------|--------|
| CAM/Toolpath generation | Massive API surface (280+ classes); use dedicated CAM software |
| Sheet metal features | Specialized domain with complex rules; defer to future milestone |
| T-spline/form editing | Different modeling paradigm; rarely needed for functional parts |
| Mesh editing operations | Use dedicated mesh tools; import meshes as-is |
| Simulation/FEA | Separate domain; use Fusion's built-in simulation |
| Rendering | Not part of modeling workflow; use Fusion's render workspace |
| Multi-document management | Adds state complexity; user manages documents |
| Arbitrary Python execution | Security risk; expose specific, tested operations |
| Network-based communication | File IPC works reliably; keep it simple |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 1 | Complete |
| INFRA-04 | Phase 1 | Complete |
| INFRA-05 | Phase 1 | Complete |
| FIX-01 | Phase 1 | Complete |
| FIX-02 | Phase 1 | Complete |
| FIX-03 | Phase 1 | Complete |
| FIX-04 | Phase 1 | Complete |
| FIX-05 | Phase 1 | Complete |
| SKTCH-01 | Phase 1 | Complete |
| SKTCH-02 | Phase 1 | Complete |
| SKTCH-03 | Phase 1 | Complete |
| FEAT-01 | Phase 1 | Complete |
| FEAT-02 | Phase 1 | Complete |
| FEAT-03 | Phase 1 | Complete |
| FEAT-04 | Phase 1 | Complete |
| FEAT-05 | Phase 1 | Complete |
| FEAT-06 | Phase 1 | Complete |
| FEAT-07 | Phase 1 | Complete |
| QUERY-01 | Phase 1 | Complete |
| QUERY-02 | Phase 1 | Complete |
| COMP-01 | Phase 1 | Complete |
| COMP-02 | Phase 1 | Complete |
| COMP-03 | Phase 1 | Complete |
| COMP-04 | Phase 1 | Complete |
| COMP-05 | Phase 1 | Complete |
| COMP-06 | Phase 1 | Complete |
| JOINT-01 | Phase 1 | Complete |
| JOINT-02 | Phase 1 | Complete |
| JOINT-03 | Phase 1 | Complete |
| JOINT-04 | Phase 1 | Complete |
| UTIL-01 | Phase 1 | Complete |
| UTIL-02 | Phase 1 | Complete |
| UTIL-03 | Phase 1 | Complete |
| IO-01 | Phase 1 | Complete |
| IO-02 | Phase 1 | Complete |
| IO-03 | Phase 1 | Complete |
| IO-04 | Phase 1 | Complete |
| NSKCH-01 | Phase 2 | Complete |
| NSKCH-02 | Phase 2 | Complete |
| NSKCH-03 | Phase 2 | Complete |
| NSKCH-04 | Phase 2 | Complete |
| NSKCH-05 | Phase 2 | Complete |
| NSKCH-06 | Phase 2 | Complete |
| NSKCH-07 | Phase 2 | Complete |
| NSKCH-08 | Phase 2 | Complete |
| NSKCH-09 | Phase 2 | Complete |
| CNST-01 | Phase 2 | Complete |
| CNST-02 | Phase 2 | Complete |
| CNST-03 | Phase 2 | Complete |
| CNST-04 | Phase 2 | Complete |
| CNST-05 | Phase 2 | Complete |
| CNST-06 | Phase 2 | Complete |
| CNST-07 | Phase 2 | Complete |
| CNST-08 | Phase 2 | Complete |
| CNST-09 | Phase 2 | Complete |
| DIM-01 | Phase 2 | Complete |
| DIM-02 | Phase 2 | Complete |
| DIM-03 | Phase 2 | Complete |
| NFEAT-01 | Phase 3 | Complete |
| NFEAT-02 | Phase 3 | Complete |
| NFEAT-03 | Phase 3 | Pending |
| NFEAT-04 | Phase 3 | Pending |
| NFEAT-05 | Phase 3 | Complete |
| NFEAT-06 | Phase 3 | Complete |
| NFEAT-07 | Phase 3 | Complete |
| ASSM-01 | Phase 4 | Pending |
| ASSM-02 | Phase 4 | Pending |
| ASSM-03 | Phase 4 | Pending |
| ASSM-04 | Phase 4 | Pending |
| ASSM-05 | Phase 4 | Pending |
| ASSM-06 | Phase 4 | Pending |
| PARAM-01 | Phase 5 | Pending |
| PARAM-02 | Phase 5 | Pending |
| TIME-01 | Phase 5 | Pending |
| TIME-02 | Phase 5 | Pending |
| TIME-03 | Phase 5 | Pending |
| DISC-01 | Phase 5 | Pending |
| DISC-02 | Phase 5 | Pending |
| DISC-03 | Phase 5 | Pending |
| DISC-04 | Phase 5 | Pending |
| DISC-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 83 total
- Mapped to phases: 83
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after roadmap creation*
