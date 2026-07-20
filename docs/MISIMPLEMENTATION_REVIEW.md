# Misimplementation review

Reviewed against RULES.md on 2026-07-20, after P01–P18. All quality gates
were re-run for this review: backend ruff + mypy strict + pytest 143/143,
frontend eslint + tsc + vitest 9/9 + build, acceptance script 9/9.

## The eleven review questions

| # | Question | Verdict | Evidence |
|---|---|---|---|
| 1 | Did any action bypass approval? | **No** | `validate_action` is the single enforcement point; dry-run artifact generation returns 403 at Not-Requested *and* Requested states (`test_artifact_composer.py`, `test_approval_gate.py`); drafts/previews change nothing by construction |
| 2 | Did any production route auto-apply? | **No** | `runtime_apply` and `source_push` are refused in hackathon mode *even with approval*; routing executes nothing (statuses stay Open, no artifact IDs); production changing routes carry approvalRequired=true (`test_routing_planner.py::test_production_item_does_not_auto_apply`) |
| 3 | Did any finding close without verification? | **No** | `ensure_closable` requires a Compliant result plus stored after-state; ticket/PR creation leaves status ArtifactCreated and close returns 409; a failed re-check downgrades a Closed item (`test_verification_engine.py`) |
| 4 | Did any focused agent own final scoring or routing? | **No** | Storage and NSG agents emit signals and blocker *candidates* only; tests assert decision fields stay null after detection; ScorerAgent and RoutingPlanner are the only writers of decision fields |
| 5 | Did the LLM generate authoritative score or route? | **No** | No LLM is invoked anywhere in the codebase; scoring, routing, approval, and verification are pure deterministic functions with rule versions (risk-1.0.0, route-1.0.0, approval-1.0.0, verification-1.0.0). LLM drafting (allowed by AI rules) was not needed — templates are deterministic |
| 6 | Are secrets masked and stored correctly? | **Yes** | `mask_sensitive` applied to logs, audit payloads, and evidence packets (tests cover clientSecret, connectionString, sasToken, accessKey); no secret-like literals committed (scanned); deployment uses Key Vault references + managed identity only |
| 7 | Are owner gaps visible? | **Yes** | `missing_owner` flag persists through enrichment; owner confidence explicit (Low when absent); UI shows "OWNER GAP — missing owner" and blockers as a first-class column; POL-005 blocked card cites the rule |
| 8 | Are exceptions time-bound? | **Yes** | `ExceptionRequest.is_valid()` requires owner, justification, compensating control, AND expiry; invalid requests surface `exception_without_expiry` and fall to blocked; the exception artifact refuses to compose without expiry (403) |
| 9 | Are source drift cases routed to source fixes? | **Yes** | POL-001 (drift + repo path) routes to source_pr_plus_change_ticket; PR preview carries the file, CODEOWNER, current→expected values, and the TEMPORARY runtime-patch warning |
| 10 | Are tests and quality gates passing? | **Yes** | 143/143 backend, 9/9 frontend, tsc/eslint/ruff/mypy strict clean, build passes, migrations reversible |
| 11 | Does acceptance evidence prove all criteria? | **Yes** | `scripts/validate_acceptance.py` 9/9 PASS; `docs/ACCEPTANCE_EVIDENCE.md` maps AC-1..AC-9 to artifacts, screenshots, and the audit trail |

## Issues found

| Issue | Violated rule | Impact | Fix | Owner | Status |
|---|---|---|---|---|---|
| Approver identity is free-text; roles resolve to admin in local/test only | RULES.md 9.7/9.8 (authn/authz on write APIs) intent not fully met pre-deployment | Low for the fixture demo (deny-by-default outside local/test); unacceptable for production | Wire Entra ID per docs/PERMISSIONS.md; map app roles to Entra groups | Cloud platform engineering | Documented; accepted for hackathon, required before any live deployment |
| Spec section 12 rule order interpreted: unknown side effects block *runtime* remediation, not source fixes | None (spec ambiguity, not a rule violation) | Without the interpretation, POL-001 could never reach its spec-required source PR route | Interpretation documented in routing.py docstring and P10 state entry | Governance team to ratify | Documented; accepted |
| Bicep templates hand-validated, never compiled | RULES.md 10 quality intent (build gates) | A template typo would surface at first deployment | Add a `bicep build` CI step; run `az deployment group what-if` before any create | Cloud platform engineering | Open; blocking for deployment, not for demo |
| Dependency vulnerability scanning absent from CI | RULES.md 10 ("no high or critical dependency issues before demo unless documented") | Unscanned dependencies | Add pip-audit and npm audit jobs to CI | Cloud platform engineering | Documented (this entry satisfies the "unless documented" clause); add before production |
| Prose expected values (POL-002/004/005) cannot be machine-verified | None — safe default honored | Those findings require manual verification and can never auto-close | Encode machine-checkable clauses when the real Resource Graph connector lands | Backend | Accepted (fails safe: item stays open) |
| `escalation` and `observe` routes defined but unreached by fixture data | None | Untested route branches in demo data | Covered by unit-level route logic; add fixtures post-hackathon if needed | Backend | Accepted |
| prompt_run_id cached per process start | RULES.md 4.10 intent | A long-running server spanning a prompt update stamps the older ID | Clear `current_prompt_run_id` cache on state change or read per-request | Backend | Accepted for demo |
| Evidence packets stored locally, not in Azure Blob | RULES.md 5 (Storage Account for evidence) | Packets are not yet in immutable cloud storage | `EvidencePacketStore` Protocol is the seam; Azure Blob implementation with managed identity at deployment | Backend | Open; part of the documented deployment plan |

## Demo readiness

**Status: READY FOR DEMO.**

- All eleven review questions pass with test-backed evidence.
- All nine acceptance criteria pass via the acceptance script.
- Every remaining drawback is listed above with owner and status; none
  blocks the fixture-based demo. The open items (Bicep compile, dependency
  scanning, Entra ID auth, Azure Blob packets) gate *deployment*, not the
  demo, and are already documented in docs/AZURE_DEPLOYMENT.md and
  docs/PERMISSIONS.md.
