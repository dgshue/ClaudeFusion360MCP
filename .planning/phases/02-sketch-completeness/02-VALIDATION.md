---
phase: 2
slug: sketch-completeness
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual testing via MCP batch calls to running Fusion 360 |
| **Config file** | none — Fusion 360 Python add-ins run inside embedded Python |
| **Quick run command** | `batch()` MCP call with tool-specific test sequence |
| **Full suite command** | Manual test script via sequential MCP batch operations |
| **Estimated runtime** | ~30 seconds per tool test sequence |

---

## Sampling Rate

- **After every task commit:** Verify handler loads without import error via quick batch test
- **After every plan wave:** Run full test sequence covering all new tools in that wave
- **Before `/gsd:verify-work`:** All 22 new tools + updated existing tools respond successfully
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INFRA | unit | `batch([create_sketch, draw_line, get_sketch_info])` — verify index returns | N/A W0 | pending |
| 02-01-02 | 01 | 1 | NSKCH-01 | smoke | `batch([create_sketch, draw_spline, get_sketch_info])` | N/A W0 | pending |
| 02-01-03 | 01 | 1 | NSKCH-02 | smoke | `batch([create_sketch, draw_ellipse, get_sketch_info])` | N/A W0 | pending |
| 02-01-04 | 01 | 1 | NSKCH-03 | smoke | `batch([create_sketch, draw_slot, get_sketch_info])` | N/A W0 | pending |
| 02-01-05 | 01 | 1 | NSKCH-04 | smoke | `batch([create_sketch, draw_point, get_sketch_info])` | N/A W0 | pending |
| 02-01-06 | 01 | 1 | NSKCH-05 | smoke | `batch([create_sketch, draw_circle, offset_curves])` | N/A W0 | pending |
| 02-01-07 | 01 | 1 | NSKCH-06 | smoke | `batch([create_sketch, draw_text, get_sketch_info])` | N/A W0 | pending |
| 02-01-08 | 01 | 1 | NSKCH-07 | smoke | `batch([create_sketch, draw_line, set_construction, get_sketch_info])` | N/A W0 | pending |
| 02-01-09 | 01 | 1 | NSKCH-08 | smoke | `batch([extrude box, create_sketch, project_geometry])` | N/A W0 | pending |
| 02-01-10 | 01 | 1 | NSKCH-09 | smoke | `import_svg(filepath, 0, 0, 1.0)` with test SVG | N/A W0 | pending |
| 02-02-01 | 02 | 2 | CNST-01 | smoke | `batch([create_sketch, draw_line, constrain_horizontal])` | N/A W0 | pending |
| 02-02-02 | 02 | 2 | CNST-02 | smoke | `batch([create_sketch, draw_line, constrain_vertical])` | N/A W0 | pending |
| 02-02-03 | 02 | 2 | CNST-03 | smoke | `batch([create_sketch, draw_line x2, constrain_perpendicular])` | N/A W0 | pending |
| 02-02-04 | 02 | 2 | CNST-04 | smoke | `batch([create_sketch, draw_line x2, constrain_parallel])` | N/A W0 | pending |
| 02-02-05 | 02 | 2 | CNST-05 | smoke | `batch([create_sketch, draw_circle, draw_line, constrain_tangent])` | N/A W0 | pending |
| 02-02-06 | 02 | 2 | CNST-06 | smoke | `batch([create_sketch, draw_line x2, constrain_coincident])` | N/A W0 | pending |
| 02-02-07 | 02 | 2 | CNST-07 | smoke | `batch([create_sketch, draw_circle x2, constrain_concentric])` | N/A W0 | pending |
| 02-02-08 | 02 | 2 | CNST-08 | smoke | `batch([create_sketch, draw_line x2, constrain_equal])` | N/A W0 | pending |
| 02-02-09 | 02 | 2 | CNST-09 | smoke | `batch([create_sketch, draw_line x3, constrain_symmetric])` | N/A W0 | pending |
| 02-02-10 | 02 | 2 | DIM-01 | smoke | `batch([create_sketch, draw_line, dimension_distance])` | N/A W0 | pending |
| 02-02-11 | 02 | 2 | DIM-02 | smoke | `batch([create_sketch, draw_circle, dimension_radial])` | N/A W0 | pending |
| 02-02-12 | 02 | 2 | DIM-03 | smoke | `batch([create_sketch, draw_line x2, dimension_angular])` | N/A W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `helpers/sketch_entities.py` — curve/point indexing and semantic labeling utilities
- [ ] Test SVG file for NSKCH-09 validation
- [ ] No automated test framework — all testing is manual via MCP calls to running Fusion 360 instance

*Existing infrastructure covers handler registration and dispatch patterns.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual sketch rendering | All NSKCH-* | Requires Fusion 360 UI inspection | Draw each primitive, visually verify in Fusion canvas |
| Constraint visual feedback | All CNST-* | Constraint icons only visible in Fusion UI | Apply constraint, verify green constraint icon appears |
| Dimension display | All DIM-* | Dimension text position requires UI check | Add dimension, verify value displays correctly |
| SVG fidelity | NSKCH-09 | Visual comparison needed | Import known SVG, compare to expected geometry |
| Text extrudability | NSKCH-06 | Requires testing extrude after text creation | Draw text, attempt extrude, verify 3D result |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
