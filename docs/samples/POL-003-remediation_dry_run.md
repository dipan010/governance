# Remediation dry-run plan — Key vaults should have purge protection enabled

Violation ID: POL-003
Artifact: remediation DRY-RUN plan (no live change is made; approved execution produces a what-if result only)
Generated: 2026-07-20T10:12:46.641012+00:00

## Resource Context
Resource ID: /subscriptions/1a2b3c4d-0000-4000-8000-000000000001/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.KeyVault/vaults/kv-govdev-01
Environment: Development
Owner: Cloud Governance (confidence: High)

## Raw Evidence
Compliance State: NonCompliant
Failure Reason: enablePurgeProtection is not set
Evaluated At: 2026-07-18T10:10:00+00:00

## Risk Explanation
Risk Score: 40 (Medium)
Drivers: sensitive data classification (Confidential) (+20); identity, secrets, or privileged impact (+15); strong owner confidence (+5)
Blockers: none

## Recommended Route
remediation_dry_run
Rollback / Next Action: Review the dry-run plan output; apply only with a separate approved change

## Approval and Side Effects
Approval Required: yes
Approval State: Approved
Approver Role: Change Approver
Side Effects: restart risk: None; downtime risk: None; cost impact: None

## Dry-run plan
1. Resolve target resource: /subscriptions/1a2b3c4d-0000-4000-8000-000000000001/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.KeyVault/vaults/kv-govdev-01
2. Evaluate change in what-if mode only: enablePurgeProtection == true
3. Required permission: Microsoft.KeyVault/vaults/write
4. Record what-if output to the evidence packet; make NO live change.
5. Applying the change for real requires a separate approved change.

## Verification
Query: resources | where id =~ '<resourceId>' | project purgeProtection=properties.enablePurgeProtection
Expected Compliant Value: enablePurgeProtection == true
Before State: enablePurgeProtection=False

## Audit
Artifact ID: be9d59db95f5437f8c579ab728f9162a
