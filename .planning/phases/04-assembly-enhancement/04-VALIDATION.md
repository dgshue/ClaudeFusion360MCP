---
phase: 4
slug: assembly-enhancement
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual UAT in Fusion 360 (no automated test infrastructure) |
| **Config file** | none |
| **Quick run command** | Manual: create components, apply joint, verify in Fusion 360 |
| **Full suite command** | Manual: end-to-end assembly workflow (all joint types + sketch-on-face) |
| **Estimated runtime** | ~120 seconds (manual verification) |

---

## Sampling Rate

- **After every task commit:** Manual spot-check: create joint, verify motion in Fusion 360
- **After every plan wave:** Run full assembly workflow test
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | ASSM-01 | manual | N/A - test in Fusion 360 | N/A | ⬜ pending |
| 04-01-02 | 01 | 1 | ASSM-02 | manual | N/A - test in Fusion 360 | N/A | ⬜ pending |
| 04-01-03 | 01 | 1 | ASSM-03 | manual | N/A - test in Fusion 360 | N/A | ⬜ pending |
| 04-01-04 | 01 | 1 | ASSM-04 | manual | N/A - test in Fusion 360 | N/A | ⬜ pending |
| 04-01-05 | 01 | 1 | ASSM-05 | manual | N/A - test in Fusion 360 | N/A | ⬜ pending |
| 04-02-01 | 02 | 1 | ASSM-06 | manual | N/A - test in Fusion 360 | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. This project uses manual testing in Fusion 360 (Fusion API cannot be unit tested outside the application).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rigid joint locks components | ASSM-01 | Requires Fusion 360 runtime | Create 2 components, apply rigid joint, verify no relative motion |
| Cylindrical joint rotation + translation | ASSM-02 | Requires Fusion 360 runtime | Create cylindrical joint, drive angle and distance, verify both DOF |
| Pin-slot joint motion | ASSM-03 | Requires Fusion 360 runtime | Create pin-slot joint, drive rotation and slide, verify constrained motion |
| Planar joint 2D sliding | ASSM-04 | Requires Fusion 360 runtime | Create planar joint, verify unconstrained sliding on plane |
| Ball joint spherical rotation | ASSM-05 | Requires Fusion 360 runtime | Create ball joint, verify rotation in all directions |
| Sketch on body face | ASSM-06 | Requires Fusion 360 runtime | Create sketch on face, draw geometry, verify face frame in get_sketch_info |

---

## Validation Sign-Off

- [x] All tasks have manual verify instructions
- [x] Sampling continuity: manual spot-check after each task
- [x] Wave 0 covers all MISSING references (none needed)
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
