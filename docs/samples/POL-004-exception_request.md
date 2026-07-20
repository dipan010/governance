# Time-bound exception request — PostgreSQL servers should not allow broad public IP ranges

Violation ID: POL-004
Artifact: exception request (DRAFT — becomes active only after approval)
Generated: 2026-07-20T10:12:46.656643+00:00

## Resource Context
Resource ID: /subscriptions/1a2b3c4d-0000-4000-8000-000000000001/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/psql-analytics-dev-01
Environment: Development
Owner: Analytics Engineering (confidence: High)
Data Classification: Confidential

## Raw Evidence
Compliance State: NonCompliant
Failure Reason: Firewall rule allow-all-temp permits 0.0.0.0-255.255.255.255
Evaluated At: 2026-07-18T10:15:00+00:00

## Risk Explanation
Risk Score: 60 (High)
Drivers: sensitive data classification (Confidential) (+20); internet exposure (+20); recurrence: previous fix failed or violation reintroduced (+15); strong owner confidence (+5)
Blockers: unknown_downtime_risk; missing_permission_check

## Exception Terms
Exception Owner: Analytics Engineering
Justification: One-off migration window
Compensating Control: Firewall logging plus weekly review
Expiry Date: 2026-08-15 00:00:00+00:00
Review Date: 2026-08-01 00:00:00+00:00

## Recommended Route
owner_ticket_or_change_request
Rollback / Next Action: Assign the ticket to the owner team and schedule a change review

## Approval and Side Effects
Approval Required: no
Approval State: NotRequested
Approver Role: unknown
Side Effects: restart risk: Unknown; downtime risk: Unknown; cost impact: Unknown

## Verification
Query: resources | where id =~ '<resourceId>' | mv-expand rule=properties.firewallRules | where rule.startIpAddress == '0.0.0.0' and rule.endIpAddress == '255.255.255.255'
Expected Compliant Value: no firewall rule spanning 0.0.0.0-255.255.255.255

## Audit
Artifact ID: 62189d53c46940c3ab29d425a93473ee
