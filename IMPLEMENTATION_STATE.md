# Implementation State — Policy Compliance and Drift Detection Agent

Current prompt: P09
Current status: Implemented
Last updated: 2026-07-19
Next trigger phrase: `START P10 ROUTING`

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

## P05 — Context enrichment

- Status: Implemented
- Implemented: five fixture-backed connectors behind Protocol interfaces (swappable for Azure Resource Graph, CMDB, repo map, Defender, verification sources), deterministic EnrichmentAgent filling resource facts (environment, tags, location, criticality), risk signals (data classification, internet exposure, identity impact, dependency count), remediation eligibility, ownership with explicit confidence (High exact match / Medium app-tag inference / Low none), repo mapping with source confidence and deterministic source-drift detection (current vs expected source values), Defender severity + regulatory control overlay, history (first/last seen, previous fix, recurrence), verification query + before-state attachment; enrichment wired into ingest pipeline; missing-evidence flags cleared only when evidence is actually found
- Created:
  - backend/app/connectors/resource_inventory.py
  - backend/app/connectors/owner_map.py
  - backend/app/connectors/repo_map.py
  - backend/app/connectors/defender.py
  - backend/app/connectors/verification_source.py
  - backend/app/agents/enrichment_agent.py
  - backend/tests/test_enrichment_agent.py
  - data/fixtures/defender_assessments.json
- Changed: backend/app/api/findings.py (enrichment in ingest path), backend/app/core/config.py (fixtures_dir setting), backend/app/domain/enums.py (shared coerce_enum), backend/app/agents/core_policy_agent.py (use shared helper), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — POL-001 enriches as Production / Restricted / internet-exposed / Payments Platform owner (High confidence) / repo-mapped with sourceDriftLikely=true and verification query attached; POL-005 keeps missing_owner and missing_repo_map flags with Low owner confidence and Unknown downtime risk (safety-blocker candidate). ruff, mypy strict (34 files), pytest 39/39 pass.
- Drawbacks:
  - Defender assessments fixture added (not in original P02 list) to give the Defender connector a real data source
  - POL-005 intentionally has no Defender assessment, exercising severity fallback to raw evidence
  - Deployment/pipeline history uses inventory fixture fields; Activity Log connector not modeled separately
- Validation:
  - [x] POL-001 enriches as production, restricted, internet exposed, owner mapped, repo mapped
  - [x] POL-005 remains missing owner and becomes safety-blocker candidate (Low owner confidence, Unknown downtime risk)
  - [x] Enrichment confidence is explicit (owner and source confidence asserted for all findings)
  - [x] No connector leaks secrets (mask_sensitive over enriched dumps is a no-op)
- Next trigger phrase: `START P06 STORAGE AGENT`

## P06 — Storage Firewall Compliance Agent

- Status: Implemented
- Implemented: shared focused-signal model (SignalDetection with backing evidence fact and source runtime/source/inventory, FocusedAgentResult with blocker candidates, idempotent merge into finding card data), Storage Firewall Compliance Agent with four deterministic detection rules (publicNetworkAccess Enabled → storage_public_network_access; networkAcls.defaultAction Allow → storage_firewall_default_allow; Restricted data without private endpoint → private_endpoint_gap; drifted public-access source property → source_drift_likely), applies_to guard scoping the agent to Microsoft.Storage/storageAccounts, pipeline wiring after enrichment
- Created:
  - backend/app/domain/focused_signals.py
  - backend/app/agents/storage_firewall_agent.py
  - backend/tests/test_storage_firewall_agent.py
- Changed: backend/app/api/findings.py (apply_focused_agents step in ingest pipeline), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — POL-001 finding card shows all four storage signals (storage_public_network_access, storage_firewall_default_allow, private_endpoint_gap, source_drift_likely) while decision.riskScore and decision.recommendedPath remain null. Compliant storage emits zero signals; compliant source mapping emits no drift signal. ruff, mypy strict (37 files), pytest 45/45 pass.
- Drawbacks:
  - Focused-agent orchestration lives in the ingest path (api/findings.py); if more agents accumulate, a dedicated pipeline module would be cleaner (NSG agent in P07 reuses the same hook)
  - Signal detections (evidence facts per signal) are computed but only the signal enum is persisted on the card; full detections become useful for artifacts (P12)
- Validation:
  - [x] POL-001 gets storage_public_network_access
  - [x] POL-001 gets source_drift_likely (repo property public_network_access_enabled is 'true', expected 'false')
  - [x] Agent does not calculate final risk score (decision fields stay null; asserted in test)
  - [x] Agent does not choose final route (asserted in test)
- Next trigger phrase: `START P07 NSG AGENT`

## P07 — NSG Drift Management Agent

- Status: Implemented
- Implemented: NSG Drift Management Agent scoped to Microsoft.Network/networkSecurityGroups; per-rule detection on inbound allow rules only (broad source prefix *, 0.0.0.0/0, Internet → broad_source_cidr; destination port in 22/3389/1433/5432, ranges containing them, `*`, or ranges ≥512 wide → sensitive_port_exposed; priority differing from baseline → priority_drift); safety-blocker candidates (missing_owner, unknown_downtime_risk, unknown_dependency_impact, production_runtime_change) emitted as candidates only — routing planner decides at P10; pipeline wiring alongside the storage agent
- Created:
  - backend/app/agents/nsg_drift_agent.py
  - backend/tests/test_nsg_drift_agent.py
- Changed: backend/app/api/findings.py (NSG agent in focused-agent step), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — POL-002 finding card shows broad_source_cidr, sensitive_port_exposed, priority_drift with decision fields null and action status Open. POL-002 blocker candidates are unknown_downtime_risk and production_runtime_change (owner exists); removing the owner adds missing_owner as a candidate without setting any route. Deny/outbound rules are ignored. ruff, mypy strict (39 files), pytest 61/61 pass.
- Drawbacks:
  - Blocker candidates are computed but not yet persisted on the violation (decision.blockers is owned by the scorer/routing at P08/P10)
  - Port-range parsing treats malformed ranges as not sensitive (deterministic, but a real connector should validate rule shapes upstream)
- Validation:
  - [x] POL-002 gets broad_source_cidr and sensitive_port_exposed (plus priority_drift; live verified)
  - [x] Missing owner produces blocker candidate but not final route (asserted)
  - [x] Agent does not auto-remediate (runtime properties untouched, no remediation task, status stays Open)
- Next trigger phrase: `START P08 SCORING`

## P08 — Risk and recurrence scoring

- Status: Implemented
- Implemented: pure deterministic scoring module (point model exactly per spec: severity +20, production +15, sensitive data +20, internet exposure +20, identity impact +15, recurrence +15, source drift +10, strong owner confidence +5; cap 100; bands Critical 80-100 / High 60-79 / Medium 40-59 / Low 0-39), deterministic safety blockers (missing owner/resource identity/failure reason/verification query, unknown downtime/dependency, missing permission check, production runtime change), separate actionability score (owner + source + remediation + permission + verification confidence − 10 per blocker, clamped 0-100), ScorerAgent as the single writer of decision score fields with rule version risk-1.0.0, scoring wired into ingest pipeline, POST /api/violations/{id}/score recompute endpoint, worklist sort=raw|ranked query parameter with score/band/blockers/actionability in summaries; canonical schema bumped to 1.1.0 (additive actionability fields on Decision)
- Created:
  - backend/app/domain/scoring.py
  - backend/app/agents/scorer_agent.py
  - backend/app/api/scoring.py
  - backend/tests/test_scoring.py
- Changed: backend/app/domain/evidence_schema.py (schema 1.1.0, actionability fields), backend/app/api/findings.py (scorer in pipeline, sort param, richer summaries), backend/app/main.py (scoring router), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — raw order leads with POL-002 (Critical raw severity); ranked order leads with POL-001 (score 100, Critical band, factors listed with points). POL-005 risk Low(20) but 4 blockers and actionability 0; POL-003 risk Medium(40) with zero blockers and actionability 80 (dry-run candidate); POL-001 Critical yet blocked by production_runtime_change — risk and actionability provably separate. ruff, mypy strict (43 files), pytest 72/72 pass. No LLM anywhere in scoring.
- Drawbacks:
  - POL-002 and POL-004 tie at 60; tie broken deterministically by raw severity then ID
  - Confidential data counts as sensitive (+20) alongside Restricted — documented rule choice
  - risk_scores DB table from spec section 15 not created; scores persist inside the evidence JSON with rule version (dedicated table can come with P14 audit work if needed)
- Validation:
  - [x] POL-001 scores Critical (100, capped from 105)
  - [x] POL-005 risky but blocked/actionability-limited (blockers surfaced, actionability 0)
  - [x] Scores are deterministic in tests (repeated runs identical)
  - [x] LLM is not used for scoring (pure functions only)
  - [x] Raw severity order differs from agent ranking (POL-002 vs POL-001 first; asserted and live verified)
- Next trigger phrase: `START P09 SOURCE DRIFT`

## P09 — Source-of-Truth Drift Agent

- Status: Implemented
- Implemented: SourceDriftAgent comparing failing runtime properties against repo-map current/expected source values, authoritative setter of history.sourceDriftLikely and history.sourceConfidence, runtime_patch_temporary flag (true whenever source still holds the bad value), analysis carrying repo/file/module/CODEOWNER/pipeline/drifted properties/verification query; deterministic PR/comment preview composer producing markdown with failing-property table, expected after-state, verification query, TEMPORARY runtime-patch warning, and explicit approval notice — preview only, no branch/commit/PR is ever created
- Created:
  - backend/app/agents/source_drift_agent.py
  - backend/app/agents/pr_comment_composer.py
  - backend/tests/test_source_drift_agent.py
  - backend/tests/test_pr_comment_composer.py
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: POL-001 analysis: sourceDriftLikely=true, sourceConfidence=High, two drifted properties (public_network_access_enabled true→false, network_rules.default_action Allow→Deny), runtime patch marked temporary; preview rendered with title "fix(payments-storage): POL-001 — …", full source-fix body, expected after-state, and approval notice. POL-003 mapped without drift (runtime patch not temporary); POL-005 unmapped returns None with Unknown source confidence. ruff, mypy strict (47 files), pytest 82/82 pass.
- Drawbacks:
  - Composer is template-based (deterministic); optional LLM polish for owner-friendly wording can be layered at P12 within AI-usage rules
  - compose_pr_comment raises ValueError when no drift exists — callers (P12 artifacts) must route non-drift cases elsewhere
  - Preview is not yet persisted or exposed via API; artifact generation endpoint arrives at P12
- Validation:
  - [x] POL-001 has high source confidence
  - [x] PR/comment includes expected after-state (source values and compliant runtime value)
  - [x] No real branch or PR is created without approval (preview flag, approval notice, action_state.pr_url stays null)
  - [x] Runtime-only patch is labelled temporary when source drift exists
- Next trigger phrase: `START P10 ROUTING`
