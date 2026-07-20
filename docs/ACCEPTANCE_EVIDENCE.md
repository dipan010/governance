# Acceptance evidence matrix

Reproduce at any time with:

```bash
backend/.venv/bin/python scripts/validate_acceptance.py
```

Latest run: **9/9 PASS** (2026-07-20). Evidence below is taken from that
run plus the generated samples in `docs/samples/`.

| AC | Criterion | Result | Evidence |
|---|---|---|---|
| AC-1 | ≥ 5 non-compliance records processed | PASS | `ingested=5 errors=0`; worklist shows POL-001..POL-005 (`docs/samples/screenshot-worklist.png`) |
| AC-2 | Core agent + ≥ 2 focused agents | PASS | POL-001 signals `storage_public_network_access, storage_firewall_default_allow, private_endpoint_gap, source_drift_likely`; POL-002 signals `broad_source_cidr, sensitive_port_exposed, priority_drift` |
| AC-3 | Every record has score, owner or owner gap, route, verification query | PASS | acceptance script checks all 5 via `GET /api/violations/{id}` |
| AC-4 | Ranking differs from raw severity sorting | PASS | raw = `[POL-002, POL-001, POL-004, POL-005, POL-003]`, ranked = `[POL-001, POL-002, POL-004, POL-003, POL-005]` |
| AC-5 | One ticket/change route | PASS | `docs/samples/POL-002-ticket.md` (owner Web Frontline, blockers listed) |
| AC-6 | One source PR/comment route | PASS | `docs/samples/POL-001-pr_comment_preview.md` (source fix table, expected after-state, TEMPORARY warning) |
| AC-7 | One remediation dry-run after approval | PASS | POL-003 artifact returns 403 before approval, 200 after; `docs/samples/POL-003-remediation_dry_run.md` states "make NO live change" |
| AC-8 | One blocked/exception unsafe action | PASS | `docs/samples/POL-005-blocked_card.md` cites "RULES.md 2.7: missing owner blocks auto-action" + safe alternative; `docs/samples/POL-004-exception_request.md` carries owner/justification/compensating control/expiry |
| AC-9 | Before/after verification for at least one case | PASS | POL-001: close 409 before proof → verify `Enabled → Disabled` Compliant → close 200; audit packet `local://evidence_packets/POL-001/verification.completed-*.json`; full trail in `docs/samples/POL-001-audit-trail.json` |

## Definition-of-done cross-check (spec section 22)

| Item | Status |
|---|---|
| Five findings ingested and normalized | done (AC-1) |
| Storage and NSG focused agents emit signals | done (AC-2) |
| Scores and ranking are explainable | done — per-factor points on every card |
| Raw severity and agent-ranked views differ | done (AC-4) |
| Every finding has a route | done (AC-3) |
| One ticket generated | done (AC-5) |
| One PR/comment generated | done (AC-6) |
| One remediation dry-run after approval | done (AC-7) |
| One unsafe action blocked or routed to exception | done (AC-8: both) |
| At least one before/after verification succeeds | done (AC-9) |
| Every changing action has approval, side effects, rollback/next action | done — approval payloads carry all three |
| Audit packet exists for each route | done — artifact/blocked/exception/verification events per finding; verification carries packet files |
| Prompt state file updated for every prompt execution | done — `state.json` has a run per prompt; enforced by `tests/test_state_tracker.py` |

## Samples

- `docs/samples/screenshot-worklist.png` — live dashboard, agent-ranked
- `docs/samples/screenshot-pol001-card.png` — POL-001 finding card
- `docs/samples/POL-001-pr_comment_preview.md`, `POL-001-ticket.md`
- `docs/samples/POL-002-ticket.md`
- `docs/samples/POL-003-remediation_dry_run.md`
- `docs/samples/POL-004-exception_request.md`
- `docs/samples/POL-005-blocked_card.md`
- `docs/samples/POL-001-audit-trail.json`, `dashboard-summary.json`
