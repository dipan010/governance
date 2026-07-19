# Source fix required — ${policy_name}

Violation ID: ${violation_id}
Artifact: PR/comment PREVIEW (no branch, commit, or pull request is created without explicit human approval)
Generated: ${created_at}

## Resource Context
Resource ID: ${resource_id}
Environment: ${environment}
Owner: ${owner_team} (confidence: ${owner_confidence})
Exposure: ${exposure}
Data Classification: ${data_classification}

## Raw Evidence
Compliance State: ${compliance_state}
Failure Reason: ${failure_reason}
Evaluated At: ${evaluated_at}

## Risk Explanation
Risk Score: ${risk_score} (${risk_band})
Drivers: ${score_factors}
Blockers: ${blockers}

## Recommended Route
${route}
Rollback / Next Action: ${rollback_or_next_action}

## Approval and Side Effects
Approval Required: ${approval_required}
Approval State: ${approval_state}
Approver Role: ${approver_role}
Side Effects: ${side_effects}

## Source Fix
${source_fix}

Runtime-only patching would be TEMPORARY while the source still contains the
non-compliant value: the next deployment reintroduces the violation.

## Verification
Query: ${verification_query}
Expected Compliant Value: ${expected_compliant_value}
Before State: ${before_state}

## Audit
Artifact ID: ${artifact_id}
