# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-16
**Phases:** 5 | **Plans:** 17 | **Requirements:** 83/83

### What Was Built
- Complete MCP-to-Fusion 360 bridge: 79 tools covering sketches, 3D features, assemblies, parametric design, and timeline
- CustomEvent-based architecture eliminating threading violations
- AI discoverability layer: MCP resource endpoints, prompt templates, enriched docstrings
- Domain-organized handler modules with dict-based dispatch

### What Worked
- Wave-based parallel execution — phases 1-2 had high plan counts but executed efficiently with parallel agents
- Fix-before-expand strategy — closing the 30-tool gap first gave a stable foundation for new features
- Domain handler module pattern — clean separation made it easy to add handlers incrementally
- Semantic selection helpers (resolve_edges, resolve_faces) — reused across many handlers

### What Was Inefficient
- Some ROADMAP.md plan checkboxes and progress table entries got out of sync across phases (manual tracking drift)
- Phase 1 was overloaded (39 requirements in one phase) — could have been split for cleaner tracking
- SUMMARY.md one_liner fields were often null, requiring manual extraction of accomplishments

### Patterns Established
- Handler pattern: each handler is a function taking `(args, app, design)`, returning a dict
- Semantic selection: `resolve_edges(body, spec)` and `resolve_faces(body, spec)` for flexible geometry selection
- Coordinate correction: `detect_sketch_plane()` + `correct_for_xz_plane()` for transparent XZ inversion
- Entity indexing: `sketch_entities.py` provides consistent curve/point labeling
- Face-based sketches skip coordinate correction (face-local coordinates)
- Construction geometry uses `createByReal` for distances, `createByString` with `deg` suffix for angles

### Key Lessons
1. CustomEvent pattern is essential — Fusion 360 crashes silently without it; must be first priority in any Fusion add-in
2. Two-runtime isolation (system Python vs embedded Python) means no shared libraries — keep IPC boundary clean
3. Parameter annotation should be additive/non-breaking — wrap in try/except so failures don't block the main operation
4. Domain handler modules scale well — going from 9 to 79 handlers stayed manageable

### Cost Observations
- Model mix: primarily opus for execution, sonnet for verification
- Execution was highly parallel — Wave 1 plans ran concurrently in most phases
- Average plan execution: 2-4 minutes per plan

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 5 | 17 | Established handler pattern, parallel execution |

### Top Lessons (Verified Across Milestones)

1. Fix foundations before expanding — threading and error handling must come first
2. Domain-organized modules scale better than monolithic files
