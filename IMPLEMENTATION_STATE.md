# Implementation State — Policy Compliance and Drift Detection Agent

Current prompt: P19
Current status: Implemented — READY FOR DEMO
Last updated: 2026-07-20
Next trigger phrase: `READY FOR DEMO`

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

## P10 — Remediation Routing Planner

- Status: Implemented
- Implemented: pure deterministic route selection (domain/routing.py) over all eight routes with rule order: missing resource identity → invalid_finding; missing owner → blocked_manual_review; source drift with repo path → source_pr_plus_change_ticket (approval required, Cloud Governance Approver); valid exception request (owner+justification+compensating control+expiry) → time_bound_exception (approval required, Security/Compliance Lead) with invalid requests surfacing exception_without_expiry and falling to blocked; remediation supported + permission available + non-production + low downtime/restart → remediation_dry_run (approval required, Change Approver); otherwise owner_ticket_or_change_request; RouteDecision carries reason, blockers, side effects, rollback/next action, rule version route-1.0.0; RoutingPlanner agent is the single writer of decision route fields; routing wired into ingest pipeline; POST /api/violations/{id}/route with optional exceptionRequest body
- Created:
  - backend/app/domain/routing.py
  - backend/app/agents/routing_planner.py
  - backend/app/api/routes.py
  - backend/tests/test_routing_planner.py
- Changed: backend/app/api/findings.py (planner in pipeline), backend/app/main.py (routes router), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — POL-001 source_pr_plus_change_ticket (approval required, Cloud Governance Approver); POL-002 owner_ticket_or_change_request with unknown_downtime_risk and production blockers surfaced; POL-003 remediation_dry_run (approval required, Change Approver); POL-004 owner_ticket_or_change_request, switching to time_bound_exception via API when a valid exception request is supplied; POL-005 blocked_manual_review with missing_owner. Routing never executes anything: statuses stay Open, no artifact IDs are set, production changing routes carry approvalRequired=true. ruff, mypy strict (51 files), pytest 94/94 pass.
- Drawbacks:
  - Documented interpretation of spec section 12: unknown side effects block runtime remediation, not source fixes — otherwise POL-001 could never reach its required source PR route; missing owner always blocks
  - escalation and observe routes are defined but no fixture reaches them (escalation requires ownerless + valid-exception-less dead end already covered by blocked_manual_review)
  - Exception requests are evaluated per-call and not yet persisted as exception records (P12/P14)
- Validation:
  - [x] POL-001 routes to source PR/comment plus change ticket
  - [x] POL-002 routes to owner ticket (owner exists; unknown downtime and production evidence surfaced as blockers)
  - [x] POL-003 routes to remediation dry-run only with approval-ready evidence (approvalRequired=true)
  - [x] POL-005 routes to blocked/manual review
  - [x] Production item does not auto-apply (status Open, no artifacts, approval required on changing routes)
- Next trigger phrase: `START P11 APPROVAL GATE`

## P11 — Approval gate

- Status: Implemented
- Implemented: approval domain (change categories for runtime cloud / source code / network exposure / identity / production behavior changes; action kinds split into drafts allowed without approval, approval-required dry-run execution, and hackathon-forbidden runtime_apply/source_push refused even with approval; validate_action as the single deterministic enforcement point), ApprovalPayload with approver role, resource, route, risk score+factors, blockers, side effects, rollback/next action, verification query, change categories, rule version approval-1.0.0; ApprovalGate agent (request → AwaitingApproval; approve → approver+timestamp+Approved; reject/defer require reason, persist it; Rejected status recorded); approvals table with reversible migration 7ecc100ab2b6; API: POST approval-request, POST approve (approver role required), GET approvals; finding card (GET /violations/{id}) now includes approvals with payloads
- Created:
  - backend/app/domain/approval.py
  - backend/app/agents/approval_gate.py
  - backend/app/api/approvals.py
  - backend/app/repositories/approvals_repo.py
  - backend/migrations/versions/7ecc100ab2b6_approvals_table.py
  - backend/tests/test_approval_gate.py
- Changed: backend/app/db/models.py (ApprovalRow), backend/app/domain/routing.py (side_effects_for made public), backend/app/api/findings.py (approvals on finding card), backend/app/main.py (approvals router), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — POL-003 approval request carries Change Approver role and change categories [runtime_cloud_change, identity_change]; approve records approver and flips card actionStatus to Approved with the payload visible on the finding card. Dry-run execution raises ApprovalRequiredError until approved; runtime_apply and source_push are refused in hackathon mode even after approval; rejection persists with reason (Rejected + "Change freeze"); reject/defer without reason is refused (403 via API). ruff, mypy strict (56 files), pytest 105/105 pass.
- Drawbacks:
  - Approver identity is a free-text field authenticated only by the local/test role stub until P16 Entra ID wiring
  - "Action buttons disabled without approval" is a frontend concern (P15); the backend enforces via validate_action and exposes approval state for the UI
  - repositories/approvals_repo.py added beyond the runbook's four listed files (separation of concerns)
- Validation:
  - [x] Cloud/source-changing action cannot execute without approval (dry-run raises until Approved; forbidden actions always refused)
  - [x] Production route cannot auto-apply (runtime_apply/source_push refused even with approval)
  - [x] Approval payload is visible in finding card (approvals list on GET /violations/{id})
  - [x] Rejection reason persists (DB row Rejected with reason and decided_at)
- Next trigger phrase: `START P12 ARTIFACTS`

## P12 — Action artifacts

- Status: Implemented
- Implemented: five markdown templates mirroring the Finding Card Template (ticket, pr_comment, remediation_dry_run, exception_request, blocked_card), deterministic ArtifactComposer filling templates from evidence (resource context, raw evidence, risk explanation with factors, recommended route, approval state, side effects, source fix from SourceDriftAgent, verification query, before state), route→artifact mapping (source PR route yields PR preview + ticket; dry-run route yields plan; blocked route yields card with per-blocker rule citation and safe alternative), exception artifact requiring owner+justification+compensating control+expiry, action_artifacts table with reversible migration 7a805285e858, POST /api/violations/{id}/artifact enforced through the approval gate (dry-run 403 until Approved; runtime_apply/source_push always 403), GET /api/violations/{id}/artifacts, action state updates (draft ticket_id/remediation_task_id; prUrl never set; blocked card sets status Blocked)
- Created:
  - backend/app/agents/artifact_composer.py
  - backend/app/api/artifacts.py
  - backend/app/templates/ticket.md
  - backend/app/templates/pr_comment.md
  - backend/app/templates/remediation_dry_run.md
  - backend/app/templates/exception_request.md
  - backend/app/templates/blocked_card.md
  - backend/migrations/versions/7a805285e858_action_artifacts_table.py
  - backend/tests/test_artifact_composer.py
- Changed: backend/app/db/models.py (ArtifactRow), backend/app/main.py (artifacts router), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — POL-001 → pr_comment_preview + ticket (source fix section filled, TEMPORARY warning); POL-002 → ticket; POL-003 → 403 until approval then remediation_dry_run with approvalState Approved and "NO live change" plan; POL-004 → exception_request only with valid expiry (403 without); POL-005 → blocked_card citing "RULES.md 2.7: missing owner blocks auto-action" with safe alternative, card status Blocked. All artifacts isDraft=true; prUrl stays null. ruff, mypy strict (59 files), pytest 117/117 pass.
- Drawbacks:
  - No real ServiceNow/Jira/GitHub/Azure calls by design; connectors for real writes arrive only with explicit approval and configuration (P16+)
  - Artifact bodies are deterministic template output; optional LLM wording polish (allowed by AI rules for drafts) not layered in
  - Escalation route reuses the blocked_card template (no dedicated escalation template in runbook list)
- Validation:
  - [x] Every artifact includes violation ID, evidence, risk explanation, recommended route, approval, side effects, source fix if applicable, verification query (section assertions per artifact)
  - [x] No real external write happens by default (all drafts; prUrl null; no external connectors invoked)
  - [x] Blocked path clearly states rule and safe alternative (rule citation + alternative per blocker)
- Next trigger phrase: `START P13 VERIFICATION`

## P13 — Verification engine

- Status: Implemented
- Implemented: pure verification rules (clause parser for "prop == value" expressions, case-insensitive comparison, NotRun when no after-state, Failed with mismatch details and mandatory next action, prose-only expectations require manual verification and never auto-pass), ensure_closable closure guard (Compliant result plus stored after-state required; ticket/PR creation alone never satisfies), VerificationEngine agent (fixture after-state by default, afterState override to simulate a live re-query, sets Verified status on success, downgrades a previously Closed item to VerificationPending if a re-check fails, writes verification.completed and violation.closed audit events with correlation IDs), audit_events table with reversible migration 3a10f3efc10d (P14 formalizes the store around it), POST /api/violations/{id}/verify and POST /api/violations/{id}/close (409 closure_blocked with nextAction)
- Created:
  - backend/app/domain/verification.py
  - backend/app/agents/verification_engine.py
  - backend/app/api/verification.py
  - backend/migrations/versions/3a10f3efc10d_audit_events_table.py
  - backend/tests/test_verification_engine.py
- Changed: backend/app/db/models.py (AuditEventRow), backend/app/main.py (verification router), IMPLEMENTATION_STATE.md, state.json
- Result: Live verified — close before verify returns 409 ("closure requires after-state proof"); verify shows before publicNetworkAccess Enabled → after Disabled, result Compliant, status Verified with an audit event; close then succeeds (Closed with violation.closed audit event). Simulated failed after-state keeps the item open with a concrete next action; POL-002 (no after-state) is NotRun and unclosable; artifact creation leaves status ArtifactCreated and closure still blocked. ruff, mypy strict (63 files), pytest 128/128 pass.
- Drawbacks:
  - POL-002/004/005 expected values are prose, so their machine verification path is manual-verification-required by design (fixture limitation, safe default)
  - audit_events table introduced here ahead of P14's formal audit store (domain, repo, API, masking arrive at P14)
  - POST /close endpoint added beyond the runbook's API list to make closure enforcement provable
- Validation:
  - [x] POL-001 shows before publicNetworkAccess Enabled and after Disabled
  - [x] POL-001 closes only after successful verification (409 before, 200 after)
  - [x] Failed verification keeps item open and returns next action
  - [x] Ticket/PR creation alone does not close item (ArtifactCreated ≠ Closed; close still 409)
- Next trigger phrase: `START P14 AUDIT STORE`

## P14 — Audit store

- Status: Implemented
- Implemented: audit domain with the full spec event catalog (finding.ingested/normalized/enriched, focused_agent.signals_detected, risk.scored, route.planned, approval.requested/approved/rejected/deferred, artifact.generated, verification.completed, violation.closed, violation.blocked, exception.created), prompt-run ID read from state.json and stamped on every event, AuditRepository with correlation ID + action ID + evidence packet location + mask_sensitive on every payload, application-level append-only enforcement (SQLAlchemy before_flush guard raising AppendOnlyViolationError on any update or delete of audit rows; repository exposes no mutation methods), evidence packet store connector behind a Protocol (LocalEvidencePacketStore writing masked JSON packets, swappable for Azure Blob + managed identity), audit emission wired across the whole pipeline (ingest emits six event types per record sharing one correlation ID; approvals, artifacts, blocked cards, exceptions, verification, and closure all emit), verification engine refactored to write evidence packets and audit events through the store, GET /api/audit/{violationId} audit-trail endpoint, audit_events columns prompt_run_id + evidence_packet with reversible migration 380983188d8c
- Created:
  - backend/app/domain/audit.py
  - backend/app/repositories/audit_repo.py
  - backend/app/api/audit.py
  - backend/app/connectors/storage.py
  - backend/migrations/versions/380983188d8c_audit_prompt_run_id_and_evidence_packet.py
  - backend/tests/test_audit_store.py
- Changed: backend/app/db/models.py (audit columns + append-only guard), backend/app/core/config.py (evidence_packets_dir), backend/app/agents/verification_engine.py (audit repo + packet store), backend/app/api/verification.py, backend/app/api/findings.py (pipeline audit emission), backend/app/api/approvals.py, backend/app/api/artifacts.py, .gitignore (evidence packets dir), IMPLEMENTATION_STATE.md, state.json
- Result: POL-001 ingest produces finding.ingested/normalized/enriched, focused_agent.signals_detected, risk.scored, route.planned sharing one correlation ID; approval, artifact, blocked, exception, verification, and closure events all recorded; verification events carry a local:// evidence packet whose masked JSON holds before/after proof; secret-like keys (clientSecret, connectionString, sasToken, accessKey) masked in both audit payloads and packets; updates and deletes on audit rows raise AppendOnlyViolationError. ruff, mypy strict (68 files), pytest 138/138 pass.
- Drawbacks:
  - prompt_run_id reflects state.json currentPromptId at process start (lru_cache); long-running processes spanning prompt updates would need a cache clear
  - Evidence packets are stored locally under data/evidence_packets (gitignored); Azure Blob implementation arrives with P16 deployment work
  - Append-only is enforced at the application/session level; database-level immutability (permissions/immutable blobs) is a deployment concern for P16
- Validation:
  - [x] Every major decision has audit event (pipeline, approval, artifact, verification, closure, blocked, exception)
  - [x] Audit includes prompt run ID (stamped from state.json on every event)
  - [x] Secret masking test passes (payloads and evidence packets)
  - [x] Audit is append-only at application level (update and delete both raise)
- Next trigger phrase: `START P15 FRONTEND`

## P15 — React dashboard and finding cards

- Status: Implemented
- Implemented: Vite + React 18 + TypeScript strict frontend with typed API client (all backend contracts mirrored in src/api/types.ts); ComplianceSummary rendering the nine spec metrics from the new GET /api/dashboard/summary; Worklist with raw-severity vs agent-ranked toggle, all eleven required filters (policy, severity, exposure, data classification, owner, app, source drift, route, confidence, status, blocker), and blockers shown as first-class column; FindingCard hero composing ScoreBreakdown (score + factors + actionability + blockers + rule versions), RouteView (route, approval requirement, next action, verification query, artifact generation button disabled without approval, artifact previews), ApprovalPanel (request/approve/reject/defer with reason required to reject, payload visible), SourceFixPanel (repo/file/CODEOWNER, temporary-runtime-patch warning), VerificationPanel (before/after states, run verification, close disabled until Compliant), AuditTimeline (event type, prompt run, action ID, evidence packet); backend worklist summaries extended with route/owner/exposure/classification/drift/confidence fields to power filters; vitest + testing-library suite covering summary metrics, sort toggle, blocker filtering, all filters present, POL-001 route + disabled/enabled artifact button, closure disabled without proof, POL-005 blocked card with owner gap
- Created:
  - frontend/package.json, tsconfig.json, vite.config.ts, eslint.config.js, index.html
  - frontend/src/main.tsx, App.tsx, styles.css
  - frontend/src/api/types.ts, client.ts
  - frontend/src/components/{ComplianceSummary,Worklist,FindingCard,ScoreBreakdown,RouteView,ApprovalPanel,SourceFixPanel,VerificationPanel,AuditTimeline}.tsx
  - frontend/src/test/{setup.ts,fixtures.ts,components.test.tsx}
  - backend/app/api/dashboard.py (GET /api/dashboard/summary)
- Changed: backend/app/api/findings.py (worklist summary fields for filters), backend/app/main.py (dashboard router), IMPLEMENTATION_STATE.md, state.json
- Result: Frontend typecheck (tsc strict), eslint, vitest 9/9, and production build all pass; backend remains green (ruff, mypy strict 69 files, pytest 138/138). Live: dashboard summary returns the nine metrics (blockedUnsafeActions=1, verifiedFixes=1 after exercising POL-005 and POL-001) and worklist rows carry route/owner/drift/exposure for filtering. Dev server proxies /api to the backend on :8000.
- Drawbacks:
  - No dedicated dashboard API tests yet (endpoint covered indirectly; P17 hardens)
  - Approver identity is a free-text input in the UI, matching the P11 auth stub until P16
  - Plain fetch-based data loading instead of TanStack Query (acceptable for the demo scale; rules list it as preferred, not mandatory)
  - Route artifacts for the exception path require the API's exceptionRequest body; the UI generates default route artifacts only (exception form is a stretch item)
- Validation:
  - [x] Summary metrics render (ComplianceSummary test + live endpoint)
  - [x] Worklist can toggle raw severity and agent ranking (toggle test; server-side sort param)
  - [x] POL-001 card shows PR/comment and ticket route ("Source PR/comment plus change ticket")
  - [x] POL-005 card shows blocked route (blocked_manual_review with owner gap and blockers)
  - [x] Action button is disabled without approval (disabled test, enabled-after-approval test, closure disabled without proof)
- Next trigger phrase: `START P16 CI CD AND AZURE`

## P16 — CI/CD and Azure environment

- Status: Implemented
- Implemented: GitHub Actions backend CI (ruff format+lint, mypy strict, pytest, migration up/down/up reversibility check on Python 3.12) and frontend CI (npm ci, eslint, tsc, vitest, build on Node 22), both with contents:read only; Bicep environment under infra/bicep with modules for monitoring (Log Analytics + App Insights), Key Vault (RBAC authorization, soft delete + purge protection — practices the POL-003 policy), Storage (evidence-packets container, no public blobs, default deny, TLS 1.2 — practices the POL-001 policy), PostgreSQL Flexible Server (Entra-only auth, password auth disabled), App Service backend with system-assigned managed identity reading database-url via a Key Vault reference, Static Web App frontend, and resource-scoped role assignments (Key Vault Secrets User + Storage Blob Data Contributor only); environment parameter allowlist rejects anything but dev; docs/AZURE_DEPLOYMENT.md (what-if-first workflow, OIDC federated credentials, approval gates) and docs/PERMISSIONS.md (runtime/CI/human role tables, explicit not-granted list, data-plane restrictions)
- Created:
  - .github/workflows/backend-ci.yml
  - .github/workflows/frontend-ci.yml
  - infra/bicep/main.bicep
  - infra/bicep/modules/{monitoring,keyvault,storage,postgres,appservice,staticweb,roles}.bicep
  - docs/AZURE_DEPLOYMENT.md
  - docs/PERMISSIONS.md
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: Both workflow files parse and contain the full lint/typecheck/test/build job sets (verified with YAML load); a repo-wide scan finds no committed secret-like literals — the only secret (database-url) is a Key Vault reference resolved via managed identity; runtime identity gets no resource write permissions beyond blob data (the agent proposes, never applies); deployment is dev-only with the template rejecting other environments and what-if documented as the default mode.
- Drawbacks:
  - az/bicep CLI unavailable in this environment, so Bicep files are hand-validated but not compiled; first `az deployment group what-if` run should confirm them
  - No deploy job in CI yet by design — adding one requires the documented GitHub environment protection and OIDC setup (an approval-gated change)
  - Live-connector settings (Key Vault URI, DefaultAzureCredential wiring) are documented but the app still runs on fixtures until live connectors are approved
- Validation:
  - [x] Lint/test jobs exist (backend: format/lint/mypy/pytest/migrations; frontend: lint/typecheck/test/build)
  - [x] Secrets are referenced from Key Vault, not committed (KV reference + secret-literal scan clean)
  - [x] Permissions doc lists scopes and roles (runtime, CI, human roles, and an explicit not-granted list)
  - [x] Deployment is dry-run or dev-only unless approved (environment allowlist = dev; what-if-first documented)
- Next trigger phrase: `START P17 TEST AND QUALITY`

## P17 — Test and quality gates

- Status: Implemented
- Implemented: gap-filling tests (dashboard summary API with full-flow counts and empty-state; state tracker consistency test asserting state.json validity, currentPromptId == latest run, all required per-run fields, and IMPLEMENTATION_STATE.md sections for every prompt), acceptance script scripts/validate_acceptance.py booting the real app against a throwaway database and proving AC-1..AC-9 end to end with a printed PASS/FAIL matrix and non-zero exit on failure, docs/TESTING.md (command table, backend/frontend test inventories, security-focused test list, known gaps), root Makefile aggregating backend-lint/backend-typecheck/backend-test/frontend-lint/frontend-typecheck/frontend-test/build/acceptance/all
- Created:
  - backend/tests/test_dashboard.py
  - backend/tests/test_state_tracker.py
  - scripts/validate_acceptance.py
  - docs/TESTING.md
  - Makefile (repo root)
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: Acceptance script proves all nine criteria (9/9 PASS): five findings ingested; storage+NSG signals; score/owner-or-gap/route/verification-query on every record; raw [POL-002 first] vs ranked [POL-001 first] orders differ; ticket for POL-002; PR/comment preview with source fix for POL-001; POL-003 dry-run 403 before approval and generated after; POL-005 blocked card citing the missing-owner rule; POL-001 before Enabled / after Disabled with proof-gated closure and a stored evidence packet. Full gate pack green: backend ruff + mypy strict (71 files) + pytest 143/143; frontend eslint + tsc + vitest 9/9 + build.
- Drawbacks:
  - Dependency vulnerability scanning (pip-audit/npm audit) not wired into CI (documented in TESTING.md)
  - Bicep compilation not in CI (needs bicep CLI step)
  - Acceptance script asserts against fixture-specific IDs (POL-001..005) by design — it validates the demo dataset, not arbitrary data
- Validation:
  - [x] Acceptance script proves five findings, two focused agents, ticket, PR/comment, dry-run, blocked path, verification (9/9 PASS)
  - [x] All pure decision logic has tests (schema, normalizer, enrichment, both focused agents, scorer, routing, approval, artifacts, verification, audit, masking, state tracker)
  - [x] Security masking test passes (audit payloads, evidence packets, connector leak check)
  - [x] Failing gates: none; remaining gaps recorded as drawbacks
- Next trigger phrase: `START P18 DEMO VALIDATION`

## P18 — Demo validation and story

- Status: Implemented
- Implemented: docs/DEMO_SCRIPT.md covering the full nine-step runbook flow (worklist scoped to ABI TECHOPS CLOUD ENGG / ghq-3-squad3-cloudgov-dev-rg, raw vs agent-ranked, POL-001 hero card with score/source drift/PR+ticket/verification query, POL-003 dry-run after approval, POL-005 blocked unsafe action, verified after-state with audit packet, closing metrics) with per-persona talking points and the hard rules the demo never breaks; docs/ACCEPTANCE_EVIDENCE.md mapping AC-1..AC-9 to concrete evidence plus a definition-of-done cross-check against spec section 22; data/demo/demo_seed.json (directly ingestible — verified 5/5 — with the ordered demoActions plan); real generated samples in docs/samples/ (PR/comment preview, two tickets, dry-run plan, exception request, blocked card, POL-001 audit trail JSON, dashboard summary JSON) and two live UI screenshots captured with Chromium+Playwright against the running app (worklist with metrics/filters/blockers, POL-001 full finding card)
- Created:
  - docs/DEMO_SCRIPT.md
  - docs/ACCEPTANCE_EVIDENCE.md
  - data/demo/demo_seed.json
  - docs/samples/ (10 files: 5 artifact cards, audit trail, dashboard summary, 2 screenshots)
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: Screenshot confirms the live dashboard: 5 findings, agent-ranked order led by POL-001 Critical 100 with POL-001 already Verified, POL-005 Blocked, all metrics populated (tickets 2, PR 1, exception 1, blocked 1, verified 1). Demo seed ingests cleanly (5/5). Full suite remains green (143/143). Every persona has a decision moment in the script; no production auto-apply appears anywhere in the flow; the blocked path and verification proof are explicit steps.
- Drawbacks:
  - Screenshots reflect this session's run; regenerate after UI changes (commands in DEMO_SCRIPT.md)
  - The demo uses the local stack; the Azure-hosted variant (P16 infra) is documented but not exercised
  - Playwright was installed ad hoc (--no-save) for screenshots and is not a project dependency
- Validation:
  - [x] Demo covers all acceptance criteria (mapped 1:1 in ACCEPTANCE_EVIDENCE.md)
  - [x] Each persona sees a decision moment (Security Lead, IaC maintainer via source fix, Change Approver, Platform Owner, Auditor)
  - [x] No production auto-apply is shown (drafts/previews/dry-run only; hard-rules section in script)
  - [x] Blocked path is explicit (step 7: POL-005 with rule citation)
  - [x] Verification proof is visible (step 8: before/after, proof-gated close, audit packet)
- Next trigger phrase: `START P19 MISIMPLEMENTATION CHECK`

## P19 — Misimplementation check

- Status: Implemented — final status READY FOR DEMO
- Implemented: docs/MISIMPLEMENTATION_REVIEW.md answering all eleven review questions with test-backed evidence (no approval bypass — single enforcement point with 403s proven; no production auto-apply — forbidden actions refused even with approval; no closure without verification — proof-gated with failed-recheck downgrade; focused agents emit signals only; no LLM anywhere in decision paths — all rules deterministic and versioned; secrets masked in logs/audit/packets and none committed; owner gaps first-class; exceptions require expiry; source drift routes to source fixes with temporary-patch warnings; all gates passing; acceptance evidence complete), plus an honest issues table (eight findings with violated rule, impact, fix, owner, status — none blocking the demo; open items gate deployment only)
- Created: docs/MISIMPLEMENTATION_REVIEW.md
- Changed: IMPLEMENTATION_STATE.md, state.json
- Result: Final gate re-run for the review: backend ruff + mypy strict (71 files) + pytest 143/143; frontend eslint + tsc + vitest 9/9 + build; acceptance script 9/9 PASS. All eleven review questions pass. Demo readiness stated honestly: READY FOR DEMO, with deployment-gating items (Bicep compile, dependency scanning, Entra ID auth, Azure Blob evidence packets) documented with owners.
- Drawbacks:
  - The eight review-table items remain as recorded (four accepted for hackathon, two documented, two open for deployment)
- Validation:
  - [x] Every rule violation is documented or fixed (issues table with owner and status)
  - [x] Demo readiness is stated honestly (gates re-run for this review)
  - [x] Remaining drawbacks are visible (review table plus per-prompt drawbacks throughout this file)
  - [x] Final status: READY FOR DEMO
- Next trigger phrase: `READY FOR DEMO`
