# Remediation dry-run plan — ${policy_name}

Violation ID: ${violation_id}
Artifact: remediation DRY-RUN plan (no live change is made; approved execution produces a what-if result only)
Generated: ${created_at}

## Resource Context
Resource ID: ${resource_id}
Environment: ${environment}
Owner: ${owner_team} (confidence: ${owner_confidence})

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

## Dry-run plan
1. Resolve target resource: ${resource_id}
2. Evaluate change in what-if mode only: ${expected_compliant_value}
3. Required permission: ${required_permission}
4. Record what-if output to the evidence packet; make NO live change.
5. Applying the change for real requires a separate approved change.

## Verification
Query: ${verification_query}
Expected Compliant Value: ${expected_compliant_value}
Before State: ${before_state}

## Audit
Artifact ID: ${artifact_id}
