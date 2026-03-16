---
phase: 05
slug: parametric-timeline-and-discoverability
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual integration testing (Fusion 360 required) |
| **Config file** | none — no automated test framework in project |
| **Quick run command** | Manual: start Fusion 360 + add-in, connect MCP client, run tools |
| **Full suite command** | Manual: exercise all new tools + verify resources/prompts visible |
| **Estimated runtime** | ~5 minutes manual testing |

---

## Sampling Rate

- **After every task commit:** Manual smoke test of new/changed tools via MCP client
- **After every plan wave:** Full manual test of all phase tools
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~60 seconds per tool test

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | PARAM-01 | manual | MCP: `create_parameter(name="width", expression="5", unit="cm")` | N/A | ⬜ pending |
| 05-01-02 | 01 | 1 | PARAM-02 | manual | MCP: `set_parameter(name="width", expression="10")` then verify | N/A | ⬜ pending |
| 05-02-01 | 02 | 1 | TIME-01 | manual | MCP: `get_timeline()` after creating geometry | N/A | ⬜ pending |
| 05-02-02 | 02 | 1 | TIME-02, TIME-03 | manual | MCP: `create_marker(name="test")`, changes, `undo_to_marker(name="test")` | N/A | ⬜ pending |
| 05-03-01 | 03 | 2 | DISC-01, DISC-02, DISC-03 | manual | MCP client lists resources, reads each | N/A | ⬜ pending |
| 05-03-02 | 03 | 2 | DISC-04 | manual | MCP client lists prompts, invokes with params | N/A | ⬜ pending |
| 05-03-03 | 03 | 2 | DISC-05 | code review | Verify all @mcp.tool() have rich docstrings | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `fusion-addin/handlers/parametric.py` — new handler module for PARAM-01/02
- [ ] `fusion-addin/handlers/timeline.py` — new handler module for TIME-01/02/03
- [ ] `mcp-server/resources/` directory with markdown content files for DISC-01/02/03
- [ ] No automated test infrastructure exists; all testing is manual via Fusion 360

*No automated test framework — project relies on manual integration testing through Fusion 360.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Parameter expression evaluation | PARAM-01 | Requires live Fusion 360 model regeneration | Create param with expression, verify model updates |
| Parameter cross-references | PARAM-02 | Requires live dependent parameters | Create width param, create height = "width * 2", update width, verify height changes |
| Timeline feature listing | TIME-01 | Requires real design history | Create geometry, call get_timeline, verify features listed |
| Timeline rollback | TIME-02 | Requires real timeline state | Create features, roll back, verify suppression |
| Named marker undo | TIME-03 | Requires live timeline + marker state | Create marker, add features, undo to marker |
| MCP resource visibility | DISC-01-03 | Requires MCP client connection | Connect client, list resources, read each |
| Prompt template invocation | DISC-04 | Requires MCP client with prompt support | List prompts, invoke with arguments |
| Rich docstrings visible | DISC-05 | Requires MCP client tool listing | list_tools shows full descriptions |

---

## Validation Sign-Off

- [ ] All tasks have manual verification instructions
- [ ] Sampling continuity: manual smoke test after each task commit
- [ ] Wave 0 covers all new handler modules and resource directory
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s per tool test
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
