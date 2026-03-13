# Roadmap: ClaudeFusion360MCP

## Overview

This roadmap transforms a half-working Fusion 360 MCP server (39 tools declared, 9 working, several buggy) into a complete, reliable AI-driven CAD automation system. The path follows the natural dependency chain of CAD work: fix the broken foundation, then complete sketch tools (the basis of all geometry), then add advanced 3D features (which consume sketches), then assembly operations (which consume bodies), and finally parametric design and discoverability (which document and enhance the stable tool set).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation and Gap Closure** - Fix threading, error handling, and coordinate bugs; restructure add-in; implement all 30 missing handlers for declared tools
- [ ] **Phase 2: Sketch Completeness** - Add new sketch primitives, geometric constraints, and sketch dimensions for full sketch API coverage
- [ ] **Phase 3: Advanced 3D Features** - Add sweep, loft, hole, thread, and construction geometry tools
- [ ] **Phase 4: Assembly Enhancement** - Add remaining joint types and sketch-on-face capability
- [ ] **Phase 5: Parametric, Timeline, and Discoverability** - Add parametric design, timeline manipulation, MCP resources, prompts, and rich tool docs

## Phase Details

### Phase 1: Foundation and Gap Closure
**Goal**: Every currently-declared MCP tool executes without errors, on a stable foundation with correct threading, error reporting, and coordinate handling
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, FIX-01, FIX-02, FIX-03, FIX-04, FIX-05, SKTCH-01, SKTCH-02, SKTCH-03, FEAT-01, FEAT-02, FEAT-03, FEAT-04, FEAT-05, FEAT-06, FEAT-07, QUERY-01, QUERY-02, COMP-01, COMP-02, COMP-03, COMP-04, COMP-05, COMP-06, JOINT-01, JOINT-02, JOINT-03, JOINT-04, UTIL-01, UTIL-02, UTIL-03, IO-01, IO-02, IO-03, IO-04
**Success Criteria** (what must be TRUE):
  1. User can call any of the 39 currently-declared MCP tools and receive either a successful result or a clear, actionable error message (no "Unknown tool" responses, no silent failures)
  2. Fusion 360 remains stable during extended tool usage sessions with no silent crashes from threading violations
  3. User can create a sketch on the XZ plane and all coordinates match world-space expectations (no surprise Y-axis inversions)
  4. User can query body geometry and select specific edges/faces for operations like fillet and chamfer by semantic description (top face, longest edge) rather than fragile indices
  5. User can export designs to STL, STEP, and 3MF formats and import mesh files
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD
- [ ] 01-03: TBD

### Phase 2: Sketch Completeness
**Goal**: Users have a complete sketch toolkit enabling complex profiles for advanced 3D features like sweep paths, loft sections, and precise parametric geometry
**Depends on**: Phase 1
**Requirements**: NSKCH-01, NSKCH-02, NSKCH-03, NSKCH-04, NSKCH-05, NSKCH-06, NSKCH-07, NSKCH-08, NSKCH-09, CNST-01, CNST-02, CNST-03, CNST-04, CNST-05, CNST-06, CNST-07, CNST-08, CNST-09, DIM-01, DIM-02, DIM-03
**Success Criteria** (what must be TRUE):
  1. User can draw any sketch primitive (splines, ellipses, slots, points, text) and use them as extrusion profiles or sweep paths
  2. User can apply geometric constraints (horizontal, vertical, perpendicular, parallel, tangent, coincident, concentric, equal, symmetric) between sketch entities
  3. User can add parametric dimensions (distance, diameter/radius, angular) that drive sketch geometry
  4. User can convert sketch entities to construction geometry, project body edges onto sketch planes, and offset existing curves
  5. User can import SVG files into sketches for complex profile creation
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Advanced 3D Features
**Goal**: Users can create complex 3D geometry beyond basic extrude/revolve, including swept and lofted shapes, precision holes, threads, and reference geometry
**Depends on**: Phase 2
**Requirements**: NFEAT-01, NFEAT-02, NFEAT-03, NFEAT-04, NFEAT-05, NFEAT-06, NFEAT-07
**Success Criteria** (what must be TRUE):
  1. User can sweep a profile along a sketch path to create complex shapes like pipes, channels, and curved extrusions
  2. User can loft between two or more sketch profiles to create smooth transitions between cross-sections
  3. User can create standard, counterbore, and countersink holes with correct dimensions, and apply threads to cylindrical faces
  4. User can create offset and angled construction planes, reference axes, and reference points for use in subsequent sketch and feature operations
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Assembly Enhancement
**Goal**: Users can build multi-component assemblies with the full range of mechanical joint types for articulated and constrained designs
**Depends on**: Phase 3
**Requirements**: ASSM-01, ASSM-02, ASSM-03, ASSM-04, ASSM-05, ASSM-06
**Success Criteria** (what must be TRUE):
  1. User can connect components with any mechanical joint type (rigid, cylindrical, pin-slot, planar, ball) appropriate to the design intent
  2. User can create sketches directly on body faces for in-context modeling of mating features
  3. User can build a multi-component assembly (e.g., a simple hinge or bracket) using components, joints, and motion driving from Phases 1-4 combined
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Parametric, Timeline, and Discoverability
**Goal**: Users can drive designs with named parameters, navigate design history, and AI models can self-discover tools and workflows without external documentation
**Depends on**: Phase 4
**Requirements**: PARAM-01, PARAM-02, TIME-01, TIME-02, TIME-03, DISC-01, DISC-02, DISC-03, DISC-04, DISC-05
**Success Criteria** (what must be TRUE):
  1. User can create named parameters and update their values, with the model regenerating automatically to reflect changes
  2. User can view the design timeline, roll back to any point in history for editing, and undo to a named marker
  3. An AI model connecting via MCP can discover all available tools, their parameters, and usage examples through resource endpoints and rich docstrings without any external documentation
  4. An AI model can access workflow guides and prompt templates for common CAD tasks (enclosures, gears, assemblies) through MCP protocol primitives
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Gap Closure | 0/3 | Not started | - |
| 2. Sketch Completeness | 0/2 | Not started | - |
| 3. Advanced 3D Features | 0/1 | Not started | - |
| 4. Assembly Enhancement | 0/1 | Not started | - |
| 5. Parametric, Timeline, and Discoverability | 0/1 | Not started | - |
