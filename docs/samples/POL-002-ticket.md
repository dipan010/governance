# TICKET-b61719eb — Management ports should be closed on network security groups

Violation ID: POL-002
Artifact: owner ticket / change request (DRAFT — not sent to any external system)
Generated: 2026-07-20T10:12:46.597059+00:00

## Resource Context
Resource ID: /subscriptions/1a2b3c4d-0000-4000-8000-000000000001/resourceGroups/ghq-3-squad3-cloudgov-dev-rg/providers/Microsoft.Network/networkSecurityGroups/nsg-app-prod-01
Type: Microsoft.Network/networkSecurityGroups
Environment: Production
Owner: Web Frontline (web-frontline@example.com, confidence: High)
Support Group: CloudOps-Network
Business App: WebFront
Exposure: internet exposed
Data Classification: Internal

## Raw Evidence
Compliance State: NonCompliant
Failure Reason: Inbound rule allow-ssh-inbound permits 0.0.0.0/0 to destination port 22
Evaluated At: 2026-07-18T10:05:00+00:00

## Risk Explanation
Risk Score: 60 (High)
Drivers: high or critical severity (+20); production or shared platform resource (+15); internet exposure (+20); strong owner confidence (+5)
Blockers: unknown_downtime_risk; missing_permission_check; production_runtime_change
Actionability: 5

## Recommended Route
owner_ticket_or_change_request
Rollback / Next Action: Assign the ticket to the owner team and schedule a change review

## Approval and Side Effects
Approval Required: no
Approval State: NotRequested
Approver Role: unknown
Side Effects: restart risk: Unknown; downtime risk: Unknown; cost impact: Unknown; production resource: runtime change affects live traffic

## Source Fix
Not applicable (no source drift detected for this resource)

## Verification
Query: resources | where id =~ '<resourceId>' | mv-expand rule=properties.securityRules | where rule.properties.access == 'Allow' and rule.properties.sourceAddressPrefix in ('*','0.0.0.0/0','Internet') and rule.properties.destinationPortRange in ('22','3389')
Expected Compliant Value: no inbound allow from 0.0.0.0/0 to ports 22 or 3389
Before State: allow-ssh-inbound.sourceAddressPrefix=0.0.0.0/0, allow-ssh-inbound.destinationPortRange=22

## Audit
Artifact ID: b61719eb268845a4855635bca9f40075
