# Blocked: unsafe action — Public IP addresses must have an owner and approved network rules

Violation ID: POL-005
Artifact: blocked-action card (no action is taken; this card documents why)
Generated: 2026-07-20T10:12:46.671001+00:00

## Resource Context
Resource ID: /subscriptions/1a2b3c4d-0000-4000-8000-000000000001/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.Network/publicIPAddresses/pip-legacy-app-01
Environment: Unknown
Owner: unknown (confidence: Low)
Exposure: internet exposed

## Raw Evidence
Compliance State: NonCompliant
Failure Reason: Public IP has network rule drift and no owner tag is present
Evaluated At: 2026-07-18T10:20:00+00:00

## Risk Explanation
Risk Score: 20 (Low)
Drivers: internet exposure (+20)

## Why this is blocked
- missing_owner: RULES.md 2.7: missing owner blocks auto-action
- unknown_downtime_risk: RULES.md 2.7: unknown downtime risk blocks auto-remediation
- unknown_dependency_impact: RULES.md 2.7: unknown dependency impact blocks auto-remediation
- missing_permission_check: RULES.md 2.7: missing permission check blocks runtime action

## Safe alternative
- Run owner discovery (tags, CMDB, deployment caller), then re-route
- Owner assesses downtime impact in a change review
- Map dependencies via Resource Graph before any change
- Verify the managed identity's effective permission first

## Recommended Route
blocked_manual_review
Rollback / Next Action: Run owner discovery or manual review, then re-route

## Approval and Side Effects
Approval Required: no
Approval State: NotRequested
Side Effects: restart risk: Unknown; downtime risk: Unknown; cost impact: Unknown

## Verification
Query: resources | where id =~ '<resourceId>' | project tags, ipConfiguration=properties.ipConfiguration
Expected Compliant Value: owner tag present and network rules match approved baseline

## Audit
Artifact ID: 52d00fb86ee64fcb88492c8c8790f30c
