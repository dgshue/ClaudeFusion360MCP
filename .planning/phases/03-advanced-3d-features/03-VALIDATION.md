---
phase: 3
slug: advanced-3d-features
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual testing in Fusion 360 (no headless test runtime) |
| **Config file** | none |
| **Quick run command** | Call MCP tool via Claude, verify in Fusion 360 |
| **Full suite command** | Run through all success criteria scenarios manually |
| **Estimated runtime** | ~5 minutes per manual scenario |

---

## Sampling Rate

- **After every task commit:** Manual smoke test of implemented handler via MCP tool call
- **After every plan wave:** Run through all success criteria scenarios
- **Before `/gsd:verify-work`:** Full suite must be verified
- **Max feedback latency:** ~60 seconds per tool call round-trip

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | NFEAT-05 | manual-only | Create offset plane, verify in Fusion 360 | N/A | ⬜ pending |
| 3-01-02 | 01 | 1 | NFEAT-06 | manual-only | Create construction axis, verify in Fusion 360 | N/A | ⬜ pending |
| 3-01-03 | 01 | 1 | NFEAT-07 | manual-only | Create construction point, verify in Fusion 360 | N/A | ⬜ pending |
| 3-02-01 | 02 | 2 | NFEAT-01 | manual-only | Sweep profile along path, verify geometry | N/A | ⬜ pending |
| 3-02-02 | 02 | 2 | NFEAT-02 | manual-only | Loft between profiles, verify transitions | N/A | ⬜ pending |
| 3-03-01 | 03 | 2 | NFEAT-03 | manual-only | Create holes (all types), verify dimensions | N/A | ⬜ pending |
| 3-03-02 | 03 | 2 | NFEAT-04 | manual-only | Apply thread, verify specs | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No automated test framework applicable — Fusion 360 embedded Python runtime only.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sweep creates geometry along path | NFEAT-01 | Fusion 360 API runs only inside Fusion runtime, no headless mode | Create profile sketch + path sketch, call sweep tool, verify solid body in Fusion |
| Loft blends between profiles | NFEAT-02 | Same — requires visual geometry inspection | Create 2+ sketches on different planes, call loft, verify smooth transition |
| Hole creates correct type | NFEAT-03 | Same — requires dimension inspection in Fusion | Create face, call hole with each type, measure dimensions |
| Thread applies to cylinder | NFEAT-04 | Same — thread representation is visual | Create cylinder, apply thread, verify thread spec in properties |
| Construction plane at offset | NFEAT-05 | Same — plane visibility requires Fusion UI | Create offset plane, create sketch on it, verify offset |
| Construction axis created | NFEAT-06 | Same — axis visibility requires Fusion UI | Create axis, verify orientation |
| Construction point created | NFEAT-07 | Same — point visibility requires Fusion UI | Create point, verify coordinates |

---

## Validation Sign-Off

- [x] All tasks have manual verification procedures
- [x] Sampling continuity: every task has a manual smoke test
- [x] Wave 0: no automated infrastructure needed
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
