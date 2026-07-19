# Implementation State — Policy Compliance and Drift Detection Agent

Current prompt: P04
Current status: Implemented
Last updated: 2026-07-19
Next trigger phrase: `START P05 ENRICHMENT`

---

## P00 — Project contract bootstrap

- Status: Implemented
- Implemented: rules file, implementation spec, state tracker, prompt runbook
- Created: RULES.md, IMPLEMENTATION_SPEC.md, IMPLEMENTATION_STATE.md, PROMPT_RUNBOOK.md, state.json
- Changed: none
- Result: Repo bootstrapped with project contract; ready for requirements lock
- Drawbacks:
  - Ticketing system not finalized
  - Approver identities not finalized
- Validation: Contract files present in repo root
- Next trigger phrase: `START P01 REQUIREMENTS LOCK`

## P01 — Requirements lock

- Status: Implemented
- Implemented: requirements lock covering purpose, audience, MVP target, cloud scope, primary outcome, use case portfolio, build priority, required agent suite, personas and decisions, acceptance criteria, selected focused agents, out-of-scope, assumptions/open questions, misimplementation warnings
- Created: docs/REQUIREMENTS_LOCK.md
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: Scope locked. Storage Firewall and NSG Drift are the two MVP focused agents; backbone (ingest, scorer, routing, approval, verification, audit) is P0 and not deferred; acceptance criteria AC-1..AC-9 map one-to-one to implementation proof; extra agents (Key Vault, Database Firewall, IP Governance, Exception/Trend) explicitly deferred. No code changed.
- Drawbacks:
  - Ticketing system (ServiceNow vs Jira) not finalized — mock payload will cover both
  - Approver identities not finalized — role names used until provided
  - Azure hosting choice deferred to P16
  - Azure OpenAI availability for demo drafts unconfirmed
- Validation:
  - [x] MVP keeps Storage Firewall and NSG as focused agents (section 11)
  - [x] Required backbone is not deferred (section 7, P0 list)
  - [x] Acceptance criteria map one-to-one to implementation proof (section 10)
  - [x] Out-of-scope section defers extra agents until backbone is working (section 12)
  - [x] State file records result and drawback (this entry)
- Next trigger phrase: `START P02 SCHEMA AND FIXTURES`

## P02 — Canonical schema and fixtures

- Status: Implemented
- Implemented: canonical evidence schema (Pydantic v2, camelCase aliases, schema version 1.0.0), explicit enums for severity/environment/route/status/blocker/approval/verification, five demo findings POL-001..POL-005 with raw Azure Policy-shaped evidence, resource inventory, owner map, repo map, before/after verification states, schema validation tests
- Created:
  - backend/app/domain/enums.py
  - backend/app/domain/evidence_schema.py
  - backend/tests/test_evidence_schema.py
  - data/fixtures/policy_findings.json
  - data/fixtures/resource_inventory.json
  - data/fixtures/owner_map.csv
  - data/fixtures/repo_map.json
  - data/fixtures/before_after_state.json
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: 16/16 pytest tests pass. POL-001 (storage public access, prod, restricted, source drift), POL-002 (NSG 0.0.0.0/0 to port 22), POL-003 (Key Vault purge protection, dry-run candidate), POL-004 (PostgreSQL broad CIDR, exception candidate), POL-005 (public IP, missing owner, blocked candidate).
- Drawbacks:
  - Tests were run in a scratch virtualenv (pydantic 2.13, pytest 9.1); backend/pyproject.toml with pinned deps arrives in P03
  - Environment provides Python 3.12 via python3.12 binary; system default python3 is 3.11 — P03 tooling must pin 3.12
- Validation:
  - [x] All five findings have policyId, resourceId, complianceState, failureReason, evaluatedAt
  - [x] At least one finding has missing owner (POL-005 absent from owner_map.csv)
  - [x] At least two findings have repo mappings (POL-001 storage, POL-003 key vault)
  - [x] POL-001 has before and after state (Enabled/Allow → Disabled/Deny)
  - [x] Tests validate required fields and enum values (16 passed)
- Next trigger phrase: `START P03 BACKEND SCAFFOLD`

## P03 — Backend scaffold

- Status: Implemented
- Implemented: FastAPI app factory, pydantic-settings config (env/Key Vault ready, no committed secrets), JSON logging with secret-key masking helper, role model with require_role dependency (deny-by-default outside local/test), SQLAlchemy 2.x engine/session with FastAPI dependency, declarative base with naming conventions, health and version endpoints, Makefile task commands, quality tooling (ruff, mypy strict with pydantic plugin, pytest)
- Created:
  - backend/pyproject.toml (Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pytest, ruff, mypy)
  - backend/Makefile (install, format, lint, typecheck, test, run)
  - backend/app/main.py
  - backend/app/core/config.py
  - backend/app/core/logging.py
  - backend/app/core/security.py
  - backend/app/db/session.py
  - backend/app/db/models.py
  - backend/app/api/health.py
  - backend/tests/test_health.py
- Changed: backend/tests/test_evidence_schema.py (typed helpers for mypy strict), IMPLEMENTATION_STATE.md, state.json
- Result: Backend starts with uvicorn; GET /health returns {"status":"ok"}; GET /api/version returns app and schema version. ruff format+check pass, mypy strict passes (17 files), pytest 18/18 pass. No business logic implemented.
- Drawbacks:
  - Alembic is installed but migrations are not initialized yet — deferred until first tables exist (P04)
  - Local default database is SQLite; Azure Database for PostgreSQL is the deployment target (P16)
  - Auth resolves to admin in local/test only and denies elsewhere; real Entra ID auth wired at P16
  - Upstream starlette deprecation warning about httpx test client (not our code)
- Validation:
  - [x] Backend starts locally (uvicorn, verified with live requests)
  - [x] /health returns ok
  - [x] pytest passes (18/18)
  - [x] ruff passes (format + lint)
  - [x] typecheck passes (mypy strict)
- Next trigger phrase: `START P04 INGEST NORMALIZER`

## P04 — Ingestion and normalization

- Status: Implemented
- Implemented: Core Policy Compliance Agent (deterministic normalization of policy and Defender records into canonical schema), stable violation IDs (findingRef honored, else deterministic hash of policy+resource+evaluation time with case-insensitive resource identity), missing-evidence flagging (resource identity, policy id, compliance state, failure reason, evaluated at, severity, plus enrichment gaps: owner, repo map, verification query), append-only raw findings store, idempotent violation upsert, ingestion/worklist/detail APIs, Alembic initialized with reversible first migration
- Created:
  - backend/app/agents/core_policy_agent.py
  - backend/app/api/findings.py
  - backend/app/repositories/violations_repo.py
  - backend/app/domain/validation.py
  - backend/tests/conftest.py
  - backend/tests/test_core_policy_agent.py
  - backend/tests/test_findings_api.py
  - backend/alembic.ini, backend/migrations/ (env.py + initial revision 29c2ac0e6597)
- Changed: backend/app/db/models.py (raw_findings, violations tables), backend/app/main.py (findings router, lifespan create_all for local/test), IMPLEMENTATION_STATE.md, state.json
- Result: POST /api/ingest/policy ingests all five fixtures (verified live: ingested=5, errors=0); GET /api/violations returns POL-001..POL-005; GET /api/violations/POL-001 returns canonical evidence plus byte-identical raw evidence. Invalid records return structured warnings and are kept, not discarded. Migration upgrade/downgrade/upgrade verified. ruff, mypy strict (26 files), pytest 31/31 pass.
- Drawbacks:
  - Ingest endpoints authorize via the local/test role stub; real identity arrives at P16
  - Worklist has no filters/sorting yet (arrives with scoring P08 and frontend P15)
  - Owner/repo/verification flags are set for all findings at ingest by design; enrichment (P05) clears the ones it can fill
- Validation:
  - [x] Five fixtures ingest successfully (API test + live server run)
  - [x] Invalid record returns structured error or warning (warning with codes; unparseable body → 422)
  - [x] Raw evidence is preserved (append-only raw_findings, byte-identical round-trip test)
  - [x] Normalized object matches canonical schema (round-trip validation test)
  - [x] State file records files changed and result (this entry)
- Next trigger phrase: `START P05 ENRICHMENT`
