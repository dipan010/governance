# Testing and quality gates

## Commands

From the repo root (`make <target>`), or run them directly:

| Gate | Command |
|---|---|
| Backend lint | `cd backend && .venv/bin/ruff format --check . && .venv/bin/ruff check .` |
| Backend typecheck | `cd backend && .venv/bin/mypy app tests` (strict, pydantic plugin) |
| Backend test | `cd backend && .venv/bin/pytest` |
| Frontend lint | `cd frontend && npm run lint` |
| Frontend typecheck | `cd frontend && npm run typecheck` |
| Frontend test | `cd frontend && npm test` |
| Build | `cd frontend && npm run build` |
| Acceptance | `backend/.venv/bin/python scripts/validate_acceptance.py` |

CI runs the same gates on every push/PR (`.github/workflows/*-ci.yml`),
plus a migration up/down/up reversibility check.

## Backend test inventory

| Area | File |
|---|---|
| Canonical schema + fixtures | `tests/test_evidence_schema.py` |
| Normalizer (core policy agent) | `tests/test_core_policy_agent.py` |
| Ingestion/worklist API contract | `tests/test_findings_api.py` |
| Enrichment (owner/source confidence, no secret leaks) | `tests/test_enrichment_agent.py` |
| Storage Firewall agent detection | `tests/test_storage_firewall_agent.py` |
| NSG Drift agent detection | `tests/test_nsg_drift_agent.py` |
| Scoring, bands, blockers, actionability, sorting | `tests/test_scoring.py` |
| Routing planner + exception validation | `tests/test_routing_planner.py` |
| Approval gate + hackathon production stop | `tests/test_approval_gate.py` |
| Source drift + PR/comment preview | `tests/test_source_drift_agent.py`, `tests/test_pr_comment_composer.py` |
| Artifacts + templates + gate enforcement | `tests/test_artifact_composer.py` |
| Verification + proof-gated closure | `tests/test_verification_engine.py` |
| Audit store, masking, append-only | `tests/test_audit_store.py` |
| Dashboard summary | `tests/test_dashboard.py` |
| State tracker consistency | `tests/test_state_tracker.py` |
| Health/version | `tests/test_health.py` |

## Frontend test inventory

`frontend/src/test/components.test.tsx` covers: summary metrics rendering,
raw-vs-ranked sort toggle, blocker filtering, all eleven required filters,
the POL-001 critical card (route, score factors, verification query), the
disabled artifact button without approval (and enabled after approval),
closure disabled without verification proof, and the POL-005 blocked card
with the owner gap.

## Acceptance script

`scripts/validate_acceptance.py` boots the real FastAPI app against a
throwaway SQLite database, replays the entire demo flow from the fixtures,
and prints a PASS/FAIL matrix for acceptance criteria AC-1..AC-9
(see `docs/REQUIREMENTS_LOCK.md` section 10). Non-zero exit on any failure.

## Security-focused tests

- Secret masking: audit payloads and evidence packets
  (`test_audit_store.py`), connector leak check (`test_enrichment_agent.py`).
- Approval enforcement: dry-run refused without approval; runtime apply and
  source push refused even with approval (`test_approval_gate.py`,
  `test_artifact_composer.py`).
- Append-only audit: update and delete both raise (`test_audit_store.py`).

## Known gaps (recorded as drawbacks)

- Dependency vulnerability scanning (pip-audit / npm audit) is not wired
  into CI yet.
- Bicep templates are not compiled in CI (needs the `bicep` CLI step).
