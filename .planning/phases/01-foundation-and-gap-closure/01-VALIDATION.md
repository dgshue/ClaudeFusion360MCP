---
phase: 1
slug: foundation-and-gap-closure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual testing via MCP tool calls in Fusion 360 |
| **Config file** | None — Fusion add-ins can only be tested inside running Fusion 360 |
| **Quick run command** | Call individual MCP tools via Claude/MCP client |
| **Full suite command** | Run batch of all 39 tools sequentially via batch() MCP tool |
| **Estimated runtime** | ~60 seconds (39 tools at ~1.5s each) |

---

## Sampling Rate

- **After every task commit:** Run the specific tools modified/added in that task
- **After every plan wave:** Run batch() with all 39 tools in sequence
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~2 seconds per tool call

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | INFRA-01 | manual | Start add-in, run 10+ sequential tool calls | N/A | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA-02 | manual | Call fillet with invalid edge index, verify error format | N/A | ⬜ pending |
| 1-01-03 | 01 | 1 | INFRA-03 | manual | Call each tool, verify no "Unknown tool" responses | N/A | ⬜ pending |
| 1-01-04 | 01 | 1 | INFRA-04 | manual | create_sketch(XZ), draw_circle(0, 5, 1), verify circle at world Z=5 | N/A | ⬜ pending |
| 1-01-05 | 01 | 1 | INFRA-05 | manual | get_body_info() shows semantic labels, fillet(edges=["top_edge"]) works | N/A | ⬜ pending |
| 1-02-01 | 02 | 1 | FIX-01..05 | manual | Test each fixed handler with previously-ignored params | N/A | ⬜ pending |
| 1-02-02 | 02 | 1 | SKTCH-01..03 | manual | draw_line, draw_arc, draw_polygon in active sketch | N/A | ⬜ pending |
| 1-03-01 | 03 | 2 | FEAT-01..07 | manual | Create body, apply each feature operation | N/A | ⬜ pending |
| 1-03-02 | 03 | 2 | QUERY-01..02 | manual | get_body_info with labels, measure returns dimensions | N/A | ⬜ pending |
| 1-03-03 | 03 | 2 | COMP-01..06 | manual | Create, list, move, rotate, delete, interference check | N/A | ⬜ pending |
| 1-03-04 | 03 | 2 | JOINT-01..04 | manual | Create joints, drive joint motion | N/A | ⬜ pending |
| 1-03-05 | 03 | 2 | UTIL-01..03 | manual | Undo, delete_body, delete_sketch | N/A | ⬜ pending |
| 1-03-06 | 03 | 2 | IO-01..04 | manual | Export STL/STEP/3MF, import mesh | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `test_all_tools.json` — batch command file for regression testing all 39 tools in sequence
- [ ] Test data directory with sample mesh file for import_mesh testing

*Note: No automated test framework is practical — Fusion 360 add-ins can only be tested inside the running application.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Threading stability | INFRA-01 | Requires running Fusion 360 | Start add-in, run 10+ tool calls, verify no crashes |
| Coordinate correction | INFRA-04 | Requires visual verification in Fusion | Draw on XZ, verify geometry matches world-space expectations |
| Semantic labels | INFRA-05 | Requires Fusion body to exist | Create box, call get_body_info, verify face/edge labels |
| Export file validity | IO-01..03 | Output files need external validation | Export, open in slicer/CAD tool |
| Mesh import | IO-04 | Requires mesh file and Fusion 360 | Import STL, verify mesh body appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 2s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
