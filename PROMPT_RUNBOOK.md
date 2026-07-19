# Prompt-wise Implementation Plan
 
## How to use this runbook
 
Use one prompt at a time. After every prompt, validate the output and update IMPLEMENTATION_STATE.md plus state.json.
 
Do not proceed to the next prompt until the current prompt passes the validation checklist or the drawback is explicitly recorded.
 
Each prompt has:
 
- trigger phrase
- implementation intent
- prompt to run
- expected outputs
- validation checklist
- state update requirement
- next trigger phrase
 
## Global prompt rules
 
Every implementation prompt must include this guardrail block:
 
```text
Follow RULES.md. Do not make runtime cloud changes, source-code changes, network exposure changes, identity changes, or production behavior changes without approval. Use deterministic code for normalization, scoring, routing, approval gating, and verification. Use the LLM only for summaries and draft artifacts. Update IMPLEMENTATION_STATE.md and state.json with what was implemented, created, changed, result, drawback, validation, and next trigger phrase.
```
 
## P01 - Requirements lock
 
### Trigger phrase
 
`START P01 REQUIREMENTS LOCK`
 
### Intent
 
Lock the use case, MVP scope, acceptance criteria, personas, focused agents, and constraints before writing code.
 
### Prompt
 
```text
START P01 REQUIREMENTS LOCK
 
Read RULES.md and IMPLEMENTATION_SPEC.md.
Create a requirements lock document for the Policy Compliance and Drift Detection Agent.
 
Include:
1. purpose
2. audience
3. MVP target
4. cloud scope
5. primary outcome
6. use case portfolio
7. build priority
8. required agent suite
9. target personas and decisions
10. acceptance criteria
11. selected focused agents for MVP
12. explicit out-of-scope items
13. assumptions and open questions
14. misimplementation warnings
 
Do not change code yet.
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- `docs/REQUIREMENTS_LOCK.md`
- updated `IMPLEMENTATION_STATE.md`
- updated `state.json`
 
### Validation checklist
 
- MVP keeps Storage Firewall and NSG as focused agents.
- Required backbone is not deferred.
- Acceptance criteria map one-to-one to implementation proof.
- Out-of-scope section defers extra agents until backbone is working.
- State file records result and drawback.
 
### Next trigger phrase
 
`START P02 SCHEMA AND FIXTURES`
 
## P02 - Canonical schema and fixtures
 
### Trigger phrase
 
`START P02 SCHEMA AND FIXTURES`
 
### Intent
 
Create canonical evidence schema and sample data for five findings.
 
### Prompt
 
```text
START P02 SCHEMA AND FIXTURES
 
Follow RULES.md.
Implement the canonical evidence schema and MVP fixtures.
 
Create:
1. backend/app/domain/enums.py
2. backend/app/domain/evidence_schema.py using Pydantic v2
3. data/fixtures/policy_findings.json with at least five non-compliance findings
4. data/fixtures/resource_inventory.json
5. data/fixtures/owner_map.csv
6. data/fixtures/repo_map.json
7. data/fixtures/before_after_state.json
8. tests/test_evidence_schema.py
 
The five findings must include:
- POL-001 storage public network access with restricted production data and source drift
- POL-002 NSG broad SSH or RDP exposure
- POL-003 remediation dry-run candidate
- POL-004 exception or change-review candidate
- POL-005 missing owner blocked candidate
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- Pydantic schema
- fixtures
- schema validation tests
- state update
 
### Validation checklist
 
- All five findings have policyId, resourceId, complianceState, failureReason, evaluatedAt.
- At least one finding has missing owner.
- At least two findings have repo mappings.
- POL-001 has before and after state.
- Test validates required fields and enum values.
 
### Next trigger phrase
 
`START P03 BACKEND SCAFFOLD`
 
## P03 - Backend scaffold
 
### Trigger phrase
 
`START P03 BACKEND SCAFFOLD`
 
### Intent
 
Create the Python FastAPI backend skeleton with quality tooling.
 
### Prompt
 
```text
START P03 BACKEND SCAFFOLD
 
Follow RULES.md.
Create the backend scaffold using Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pytest, ruff, and mypy or pyright.
 
Create:
1. backend/pyproject.toml
2. backend/app/main.py
3. backend/app/core/config.py
4. backend/app/core/logging.py
5. backend/app/core/security.py
6. backend/app/db/session.py
7. backend/app/db/models.py
8. backend/app/api/health.py
9. backend/tests/test_health.py
 
Expose:
- GET /health
- GET /api/version
 
Add Makefile or task commands:
- lint
- format
- typecheck
- test
- run
 
Do not implement business logic yet.
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- running FastAPI app
- health endpoint
- quality tooling
- tests
 
### Validation checklist
 
- Backend starts locally.
- `/health` returns ok.
- pytest passes.
- ruff passes.
- typecheck passes or known drawback is recorded.
 
### Next trigger phrase
 
`START P04 INGEST NORMALIZER`
 
## P04 - Ingestion and normalization
 
### Trigger phrase
 
`START P04 INGEST NORMALIZER`
 
### Intent
 
Load policy/Defender fixtures and normalize into canonical violation objects.
 
### Prompt
 
```text
START P04 INGEST NORMALIZER
 
Follow RULES.md.
Implement ingestion and normalization.
 
Create:
1. backend/app/agents/core_policy_agent.py
2. backend/app/api/findings.py
3. backend/app/repositories/violations_repo.py
4. backend/app/domain/validation.py
5. tests/test_core_policy_agent.py
6. tests/test_findings_api.py
 
Implement:
- POST /api/ingest/policy
- POST /api/ingest/defender
- GET /api/violations
- GET /api/violations/{violationId}
 
Requirements:
- preserve raw evidence
- normalize to canonical schema
- generate stable violation IDs
- flag missing owner, repo map, severity, and verification query
- do not discard incomplete findings; route them to enrichment/manual review later
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- ingestion endpoints
- normalized queue
- missing evidence warnings
- tests
 
### Validation checklist
 
- Five fixtures ingest successfully.
- Invalid record returns structured error or warning.
- Raw evidence is preserved.
- Normalized object matches canonical schema.
- State file records files changed and result.
 
### Next trigger phrase
 
`START P05 ENRICHMENT`
 
## P05 - Context enrichment
 
### Trigger phrase
 
`START P05 ENRICHMENT`
 
### Intent
 
Attach resource facts, owner, repo map, Defender severity, history, and verification query.
 
### Prompt
 
```text
START P05 ENRICHMENT
 
Follow RULES.md.
Implement context enrichment using fixture-backed connectors with interfaces that can later be swapped for Azure Resource Graph, Defender, Activity Log, repo, and owner sources.
 
Create:
1. backend/app/connectors/resource_inventory.py
2. backend/app/connectors/owner_map.py
3. backend/app/connectors/repo_map.py
4. backend/app/connectors/defender.py
5. backend/app/connectors/verification_source.py
6. backend/app/agents/enrichment_agent.py
7. tests/test_enrichment_agent.py
 
Implement:
- owner confidence
- source confidence
- resource environment
- data classification
- internet exposure
- deployment/history fields
- verification query attachment
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- enriched violations
- owner gaps
- repo/source mappings
- verification queries
 
### Validation checklist
 
- POL-001 enriches as production, restricted, internet exposed, owner mapped, repo mapped.
- POL-005 remains missing owner and becomes safety-blocker candidate.
- Enrichment confidence is explicit.
- No connector leaks secrets.
 
### Next trigger phrase
 
`START P06 STORAGE AGENT`
 
## P06 - Storage Firewall Compliance Agent
 
### Trigger phrase
 
`START P06 STORAGE AGENT`
 
### Intent
 
Detect storage public access and firewall drift signals.
 
### Prompt
 
```text
START P06 STORAGE AGENT
 
Follow RULES.md.
Implement Storage Firewall Compliance Agent.
 
Create:
1. backend/app/agents/storage_firewall_agent.py
2. backend/app/domain/focused_signals.py
3. tests/test_storage_firewall_agent.py
 
Detection rules:
- publicNetworkAccess Enabled => storage_public_network_access
- networkAcls.defaultAction Allow => storage_firewall_default_allow
- restricted data without private endpoint => private_endpoint_gap
- source contains public access enabled => source_drift_likely
 
The agent must emit signals only. It must not choose final route or final score.
 
Update finding card data with storage signals.
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- storage focused signals
- tests
 
### Validation checklist
 
- POL-001 gets storage_public_network_access.
- POL-001 gets source_drift_likely if repo property is bad.
- Agent does not calculate final risk score.
- Agent does not choose final route.
 
### Next trigger phrase
 
`START P07 NSG AGENT`
 
## P07 - NSG Drift Management Agent
 
### Trigger phrase
 
`START P07 NSG AGENT`
 
### Intent
 
Detect broad CIDR, management port exposure, priority drift, and unsafe action blockers.
 
### Prompt
 
```text
START P07 NSG AGENT
 
Follow RULES.md.
Implement NSG Drift Management Agent.
 
Create:
1. backend/app/agents/nsg_drift_agent.py
2. tests/test_nsg_drift_agent.py
 
Detection rules:
- sourceAddressPrefix in ["*", "0.0.0.0/0", "Internet"] => broad_source_cidr
- destinationPortRange in [22, 3389, 1433, 5432] or broad ranges => sensitive_port_exposed
- priority differs from baseline => priority_drift
- owner missing or dependency unknown => safety blocker candidate
 
The agent must emit signals only. It must not choose final route or final score.
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- NSG focused signals
- blocker candidates
- tests
 
### Validation checklist
 
- POL-002 gets broad_source_cidr and sensitive_port_exposed.
- Missing owner produces blocker candidate but not final route.
- Agent does not auto-remediate.
 
### Next trigger phrase
 
`START P08 SCORING`
 
## P08 - Risk and recurrence scoring
 
### Trigger phrase
 
`START P08 SCORING`
 
### Intent
 
Implement deterministic scoring and separate risk from actionability.
 
### Prompt
 
```text
START P08 SCORING
 
Follow RULES.md.
Implement Risk and Recurrence Scorer.
 
Create:
1. backend/app/domain/scoring.py
2. backend/app/agents/scorer_agent.py
3. backend/app/api/scoring.py
4. tests/test_scoring.py
 
Requirements:
- deterministic score, cap at 100
- score factors with points
- score band: Critical, High, Medium, Low
- separate actionability from risk
- safety blockers must not be hidden
- raw severity sort and agent-ranked sort must differ for fixture data
 
Point model:
- high or critical severity: +20
- production/shared platform: +15
- restricted/regulated/customer/secrets data: +20
- internet exposure: +20
- identity/secrets/privileged impact: +15
- recurrence: +15
- source drift likely: +10
- strong owner confidence: +5
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- scores and bands
- score explanation
- sorting logic
- tests
 
### Validation checklist
 
- POL-001 scores Critical.
- POL-005 can be risky but blocked/actionability-limited.
- Scores are deterministic in tests.
- LLM is not used for scoring.
- Raw severity order differs from agent ranking.
 
### Next trigger phrase
 
`START P09 SOURCE DRIFT`
 
## P09 - Source-of-Truth Drift Agent
 
### Trigger phrase
 
`START P09 SOURCE DRIFT`
 
### Intent
 
Map runtime failure properties to Terraform/Bicep/source configuration and generate PR/comment preview.
 
### Prompt
 
```text
START P09 SOURCE DRIFT
 
Follow RULES.md.
Implement Source-of-Truth Drift Agent.
 
Create:
1. backend/app/agents/source_drift_agent.py
2. backend/app/agents/pr_comment_composer.py
3. tests/test_source_drift_agent.py
4. tests/test_pr_comment_composer.py
 
Requirements:
- compare failing runtime property with repo_map expected/current source values
- set sourceDriftLikely and sourceConfidence
- produce PR/comment preview, not an actual PR by default
- include repo, file, module, CODEOWNER, failing property, current value, expected value, verification query
- mark runtime-only patch as temporary when source drift likely
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- source drift analysis
- PR/comment preview for POL-001
- tests
 
### Validation checklist
 
- POL-001 has high source confidence.
- PR/comment includes expected after-state.
- No real branch or PR is created without approval.
- Runtime-only patch is labelled temporary when source drift exists.
 
### Next trigger phrase
 
`START P10 ROUTING`
 
## P10 - Remediation Routing Planner
 
### Trigger phrase
 
`START P10 ROUTING`
 
### Intent
 
Select the safest route for every finding.
 
### Prompt
 
```text
START P10 ROUTING
 
Follow RULES.md.
Implement Remediation Routing Planner.
 
Create:
1. backend/app/domain/routing.py
2. backend/app/agents/routing_planner.py
3. backend/app/api/routes.py
4. tests/test_routing_planner.py
 
Routes:
- source_pr_plus_change_ticket
- remediation_dry_run
- owner_ticket_or_change_request
- time_bound_exception
- blocked_manual_review
- escalation
- observe
- invalid_finding
 
Rules:
- missing resourceId => invalid finding
- missing owner or unknown side effect => blocked/manual review
- source drift and repo path => source PR/comment plus change ticket
- remediation supported and low risk non-production and permission available => remediation dry-run
- owner exists but automation not safe => owner ticket/change request
- exception requires owner, justification, compensating control, expiry
- otherwise escalation
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- every finding has route
- route reason and blockers
- tests
 
### Validation checklist
 
- POL-001 routes to source PR/comment plus change ticket.
- POL-002 routes to owner ticket or blocked depending owner/dependency evidence.
- POL-003 routes to remediation dry-run only after approval-ready evidence.
- POL-005 routes to blocked/manual review.
- Production item does not auto-apply.
 
### Next trigger phrase
 
`START P11 APPROVAL GATE`
 
## P11 - Approval gate
 
### Trigger phrase
 
`START P11 APPROVAL GATE`
 
### Intent
 
Enforce human approval before any changing action.
 
### Prompt
 
```text
START P11 APPROVAL GATE
 
Follow RULES.md.
Implement Approval Gate.
 
Create:
1. backend/app/domain/approval.py
2. backend/app/agents/approval_gate.py
3. backend/app/api/approvals.py
4. tests/test_approval_gate.py
 
Requirements:
- approval required for runtime cloud change, source-code change, network exposure change, identity change, production behavior change
- production gate stops at ticket/PR/comment/dry-run in hackathon mode
- approval payload includes approver role, resource, route, risk, side effects, rollback/next action, verification query
- rejected/deferred approvals persist with reason
- action buttons disabled without approval where required
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- approval payload
- approval enforcement
- tests
 
### Validation checklist
 
- Cloud/source-changing action cannot execute without approval.
- Production route cannot auto-apply.
- Approval payload is visible in finding card.
- Rejection reason persists.
 
### Next trigger phrase
 
`START P12 ARTIFACTS`
 
## P12 - Action artifacts
 
### Trigger phrase
 
`START P12 ARTIFACTS`
 
### Intent
 
Generate ticket, PR/comment, remediation dry-run, blocked card, and exception request artifacts.
 
### Prompt
 
```text
START P12 ARTIFACTS
 
Follow RULES.md.
Implement action artifact generation.
 
Create:
1. backend/app/agents/artifact_composer.py
2. backend/app/api/artifacts.py
3. backend/app/templates/ticket.md
4. backend/app/templates/pr_comment.md
5. backend/app/templates/remediation_dry_run.md
6. backend/app/templates/exception_request.md
7. backend/app/templates/blocked_card.md
8. tests/test_artifact_composer.py
 
Artifacts must tie back to the Finding Card Template.
 
Generate for fixtures:
- POL-001 PR/comment plus change ticket
- POL-002 ticket or blocked card
- POL-003 remediation dry-run after approval
- POL-004 exception or change review request
- POL-005 blocked manual review card
 
Do not call real ServiceNow/Jira/GitHub/Azure remediation APIs yet unless explicitly approved and configured.
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- draft artifacts for all routes
- templates
- tests
 
### Validation checklist
 
- Every artifact includes violation ID, evidence, risk explanation, recommended route, approval, side effects, source fix if applicable, verification query.
- No real external write happens by default.
- Blocked path clearly states rule and safe alternative.
 
### Next trigger phrase
 
`START P13 VERIFICATION`
 
## P13 - Verification engine
 
### Trigger phrase
 
`START P13 VERIFICATION`
 
### Intent
 
Compare before/after fixture state or query output and enforce closure only with proof.
 
### Prompt
 
```text
START P13 VERIFICATION
 
Follow RULES.md.
Implement Verification Engine.
 
Create:
1. backend/app/domain/verification.py
2. backend/app/agents/verification_engine.py
3. backend/app/api/verification.py
4. tests/test_verification_engine.py
 
Requirements:
- compare before/after state to expected compliant value
- store verification query
- status cannot close if verification is missing, failed, or not run
- failed verification must produce next action
- verified fix must create audit event
 
Use before_after_state.json for MVP.
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- verification API
- before/after comparison
- closure enforcement
- tests
 
### Validation checklist
 
- POL-001 can show before publicNetworkAccess Enabled and after Disabled.
- POL-001 can close only after successful verification.
- Failed verification keeps item open and returns next action.
- Ticket/PR creation alone does not close item.
 
### Next trigger phrase
 
`START P14 AUDIT STORE`
 
## P14 - Audit store
 
### Trigger phrase
 
`START P14 AUDIT STORE`
 
### Intent
 
Persist traceable audit events and evidence packets.
 
### Prompt
 
```text
START P14 AUDIT STORE
 
Follow RULES.md.
Implement Audit Store.
 
Create:
1. backend/app/domain/audit.py
2. backend/app/repositories/audit_repo.py
3. backend/app/api/audit.py
4. backend/app/connectors/storage.py
5. tests/test_audit_store.py
 
Requirements:
- append-only audit events
- event types for ingest, normalize, enrich, score, route, approval, artifact, verification, exception, blocked
- correlation ID and action ID
- evidence packet location
- prompt run ID
- no secrets in audit logs
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- audit trail
- evidence packet references
- tests
 
### Validation checklist
 
- Every major decision has audit event.
- Audit includes prompt run ID.
- Secret masking test passes.
- Audit is append-only at application level.
 
### Next trigger phrase
 
`START P15 FRONTEND`
 
## P15 - React dashboard and finding cards
 
### Trigger phrase
 
`START P15 FRONTEND`
 
### Intent
 
Build the judge-readable UI around the finding card.
 
### Prompt
 
```text
START P15 FRONTEND
 
Follow RULES.md.
Implement the React TypeScript frontend.
 
Create:
1. frontend package setup using React and TypeScript
2. API client types
3. ComplianceSummary component
4. Worklist component with raw severity vs agent-ranked toggle
5. FindingCard component
6. ScoreBreakdown component
7. RouteView component
8. ApprovalPanel component
9. SourceFixPanel component
10. VerificationPanel component
11. AuditTimeline component
12. tests for rendering critical cards and blocked cards
 
UX requirements:
- finding card is the hero
- blockers are visible
- action buttons disabled when approval or evidence is missing
- all routes show next action and verification query
- filters include policy, severity, exposure, data classification, owner, app, source drift, route, confidence, status, blocker
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- React dashboard
- finding card
- tests
 
### Validation checklist
 
- Summary metrics render.
- Worklist can toggle raw severity and agent ranking.
- POL-001 card shows PR/comment and ticket route.
- POL-005 card shows blocked route.
- Action button is disabled without approval.
 
### Next trigger phrase
 
`START P16 CI CD AND AZURE`
 
## P16 - CI/CD and Azure environment
 
### Trigger phrase
 
`START P16 CI CD AND AZURE`
 
### Intent
 
Add pipelines and Azure-native deployment scaffolding without over-permissioning.
 
### Prompt
 
```text
START P16 CI CD AND AZURE
 
Follow RULES.md.
Create CI/CD and Azure deployment scaffolding.
 
Create:
1. .github/workflows/backend-ci.yml or azure-pipelines.yml
2. .github/workflows/frontend-ci.yml or azure-pipelines.yml
3. infra/bicep or infra/terraform modules for app hosting, PostgreSQL, Storage, Key Vault, managed identity, and basic monitoring
4. docs/AZURE_DEPLOYMENT.md
5. docs/PERMISSIONS.md
 
Requirements:
- use Key Vault for secrets
- prefer managed identity or OIDC/federated credentials
- do not require broad subscription Owner for app runtime
- document least privilege permissions
- no real production deployment without approval
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- CI pipeline
- deployment docs
- least privilege permissions doc
 
### Validation checklist
 
- Lint/test jobs exist.
- Secrets are referenced from Key Vault or pipeline secret store, not committed.
- Permissions doc lists scopes and roles.
- Deployment is dry-run or dev-only unless approved.
 
### Next trigger phrase
 
`START P17 TEST AND QUALITY`
 
## P17 - Test and quality gates
 
### Trigger phrase
 
`START P17 TEST AND QUALITY`
 
### Intent
 
Harden quality gates and acceptance tests.
 
### Prompt
 
```text
START P17 TEST AND QUALITY
 
Follow RULES.md.
Implement test and quality gates.
 
Create or update:
1. backend tests for schema, normalizer, enrichment, storage agent, NSG agent, scorer, routing, approval, artifacts, verification, audit, masking
2. frontend tests for summary, worklist, finding card, blocked card, approval disabled state
3. acceptance test script that proves all MVP acceptance criteria
4. docs/TESTING.md
 
Commands must include:
- backend lint
- backend typecheck
- backend test
- frontend lint
- frontend typecheck
- frontend test
- build
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- acceptance test script
- quality docs
- test coverage for core logic
 
### Validation checklist
 
- Acceptance script proves five findings, two focused agents, ticket, PR/comment, dry-run, blocked path, verification.
- All pure decision logic has tests.
- Security masking test passes.
- Any failing gate is recorded as drawback.
 
### Next trigger phrase
 
`START P18 DEMO VALIDATION`
 
## P18 - Demo validation and story
 
### Trigger phrase
 
`START P18 DEMO VALIDATION`
 
### Intent
 
Prepare the demo flow and validate acceptance criteria against actual app output.
 
### Prompt
 
```text
START P18 DEMO VALIDATION
 
Follow RULES.md.
Create demo validation and final story.
 
Create:
1. docs/DEMO_SCRIPT.md
2. docs/ACCEPTANCE_EVIDENCE.md
3. data/demo/demo_seed.json
4. screenshots or sample cards if available
 
Demo flow:
1. open worklist scoped to ABI TECHOPS CLOUD ENGG and ghq-3-squad3-cloudgov-dev-rg
2. show raw severity order
3. switch to agent-ranked order
4. open POL-001 storage finding
5. show score, source drift, PR/comment, change ticket, verification query
6. open POL-003 dry-run after approval
7. open POL-005 blocked unsafe action
8. show verified after-state and audit packet
9. close with metrics
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- demo script
- acceptance evidence matrix
- final story
 
### Validation checklist
 
- Demo covers all acceptance criteria.
- Each persona sees a decision moment.
- No production auto-apply is shown.
- Blocked path is explicit.
- Verification proof is visible.
 
### Next trigger phrase
 
`START P19 MISIMPLEMENTATION CHECK`
 
## P19 - Misimplementation check
 
### Trigger phrase
 
`START P19 MISIMPLEMENTATION CHECK`
 
### Intent
 
Review the full implementation against RULES.md and identify unsafe or low-quality choices.
 
### Prompt
 
```text
START P19 MISIMPLEMENTATION CHECK
 
Follow RULES.md.
Review the implementation for misimplementation, rule violations, gaps, and demo risks.
 
Check:
1. Did any action bypass approval?
2. Did any production route auto-apply?
3. Did any finding close without verification?
4. Did any focused agent own final scoring or routing?
5. Did the LLM generate authoritative score or route?
6. Are secrets masked and stored correctly?
7. Are owner gaps visible?
8. Are exceptions time-bound?
9. Are source drift cases routed to source fixes?
10. Are tests and quality gates passing?
11. Does acceptance evidence prove all criteria?
 
Create docs/MISIMPLEMENTATION_REVIEW.md with:
- issue
- violated rule
- impact
- fix
- owner
- status
 
Update IMPLEMENTATION_STATE.md and state.json.
```
 
### Expected outputs
 
- misimplementation review
- final demo readiness status
- state update
 
### Validation checklist
 
- Every rule violation is documented or fixed.
- Demo readiness is stated honestly.
- Remaining drawbacks are visible.
- Final status is either Ready for Demo or Blocked with reason.
 
### Next trigger phrase
 
`READY FOR DEMO`
 
## Validation command pack
 
Use these commands as the default local validation pack after relevant prompts.
 
```bash
cd backend
ruff format --check .
ruff check .
mypy app tests
pytest
```
 
```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```
 
```bash
python scripts/validate_acceptance.py
```
 
## Prompt completion template
 
Every assistant response after an implementation prompt should end with this compact state summary:
 
```text
State update:
- Prompt ID:
- Status:
- Implemented:
- Created:
- Changed:
- Result:
- Drawback:
- Validation:
- Next trigger phrase:
```
 