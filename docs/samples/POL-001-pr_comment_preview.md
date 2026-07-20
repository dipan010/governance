# Source fix required — Storage accounts should restrict public network access

Violation ID: POL-001
Artifact: PR/comment PREVIEW (no branch, commit, or pull request is created without explicit human approval)
Generated: 2026-07-20T10:12:46.571693+00:00

## Resource Context
Resource ID: /subscriptions/1a2b3c4d-0000-4000-8000-000000000001/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.Storage/storageAccounts/stpayprod01
Environment: Production
Owner: Payments Platform (confidence: High)
Exposure: internet exposed
Data Classification: Restricted

## Raw Evidence
Compliance State: NonCompliant
Failure Reason: publicNetworkAccess is Enabled
Evaluated At: 2026-07-18T10:00:00+00:00

## Risk Explanation
Risk Score: 100 (Critical)
Drivers: high or critical severity (+20); production or shared platform resource (+15); sensitive data classification (Restricted) (+20); internet exposure (+20); recurrence: previous fix failed or violation reintroduced (+15); source drift likely (+10); strong owner confidence (+5)
Blockers: unknown_downtime_risk; missing_permission_check; production_runtime_change

## Recommended Route
source_pr_plus_change_ticket
Rollback / Next Action: Revert the source PR if the deployment misbehaves; re-run verification after deployment

## Approval and Side Effects
Approval Required: yes
Approval State: NotRequested
Approver Role: Cloud Governance Approver
Side Effects: restart risk: Unknown; downtime risk: Unknown; cost impact: Unknown; production resource: runtime change affects live traffic

## Source Fix
Repo: https://github.com/dipan010/cloudgov-iac
File: terraform/storage/payments/storage_account.tf
Module: payments-storage
CODEOWNER: @payments-platform
Property public_network_access_enabled: current 'true' -> expected 'false' (runtime: publicNetworkAccess)
Property network_rules.default_action: current 'Allow' -> expected 'Deny' (runtime: networkAcls.defaultAction)

Runtime-only patching would be TEMPORARY while the source still contains the
non-compliant value: the next deployment reintroduces the violation.

## Verification
Query: resources | where id =~ '<resourceId>' | project publicNetworkAccess=properties.publicNetworkAccess, defaultAction=properties.networkAcls.defaultAction
Expected Compliant Value: publicNetworkAccess == Disabled and networkAcls.defaultAction == Deny
Before State: publicNetworkAccess=Enabled, networkAcls.defaultAction=Allow

## Audit
Artifact ID: 99958db135334050ab917bd1fc276e8c
