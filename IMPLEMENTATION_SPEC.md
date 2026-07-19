# Policy Compliance and Drift Detection Agent
 
## 1. Executive intent
 
Build an Azure-native enterprise agent that turns Azure Policy, Defender, and source-drift findings into a governed workflow:
 
1. ingest
2. normalize
3. enrich
4. detect domain-specific control drift
5. score risk and recurrence
6. route to the safest path
7. request approval where needed
8. create ticket, PR/comment, dry-run, exception, escalation, or blocked output
9. verify after-state
10. persist audit evidence
11. show a judge-readable dashboard and finding card
 
The primary outcome is a compliance worklist with risk-ranked violations, remediation path, evidence packet, approval state, and verification result.
 
## 2. Purpose
 
Prioritize and remediate Azure governance violations with owner routing, approval, and verified after-state.
 
The solution should answer:
 
- Which findings matter first?
- Who owns the finding?
- Is runtime remediation safe?
- Will the issue return from source configuration?
- What should be approved?
- What artifact was created?
- Did the resource actually become compliant?
 
## 3. Audience
 
Primary audiences:
 
- Hackathon judges
- Cloud governance team
- Security and compliance leads
- Cloud platform engineering
- Application owners
- IaC maintainers
- Change approvers
- Auditors
 
## 4. MVP target
 
The MVP must process at least five findings and demonstrate:
 
- Core Policy Compliance Agent
- Risk and Recurrence Scorer
- Remediation Routing Planner
- Source-of-Truth Drift Agent
- at least two focused control agents
- one source PR/comment
- one ticket or change request
- one remediation dry-run after approval
- one blocked unsafe action or exception route
- one before/after verification result
- one audit packet
- worklist and finding-card UI
 
## 5. Cloud scope
 
Initial hackathon scope:
 
- Subscription: ABI TECHOPS CLOUD ENGG
- Resource group: ghq-3-squad3-cloudgov-dev-rg
- Repository: to be added
 
Enterprise Azure-native services:
 
- Azure Policy / Policy Insights
- Microsoft Defender for Cloud
- Azure Resource Graph
- Azure Database for PostgreSQL
- Azure Storage Account
- Azure Key Vault
- Azure Logic Apps
- Azure AI Foundry / Azure OpenAI
- Azure DevOps or GitHub Actions
- Event Grid, Service Bus, scheduled triggers, or Logic App triggers
 
## 6. Use case portfolio and build priority
 
### P0 required backbone
 
| Capability | Purpose | MVP output |
|---|---|---|
| Core Policy Compliance Agent | Ingest and normalize Azure Policy or Defender findings | Normalized violation queue |
| Risk and Recurrence Scorer | Rank by real-world risk and actionability | Explainable score and band |
| Remediation Routing Planner | Select safest route | Ticket, PR/comment, dry-run, exception, escalation, or blocked path |
| Source-of-Truth Drift Agent | Prevent recurrence by checking IaC/source | PR/comment with expected after-state |
| Verification and Audit Engine | Prove outcome and store evidence | Before/after result and audit packet |
 
### P1 focused agents for demo
 
| Focused agent | Keep for MVP? | Why |
|---|---:|---|
| Storage Firewall Compliance Agent | Yes | Best hero scenario: public access, restricted data, source drift, ticket, PR/comment, verification |
| NSG Drift Management Agent | Yes | Best safety scenario: broad CIDR, management port, unsafe remediation, blocked path |
| Key Vault and Secrets Control Agent | Optional | Strong security example if time permits |
| Database Firewall Compliance Agent | Optional | Similar pattern to storage, good data-store example |
| IP Change Governance Agent | Defer | Useful but harder to demo without allowlist/DNS context |
| Exception and Trend Agent | Stretch | Good extra score after verification and routing are done |
 
## 7. Target personas and decisions
 
| Persona | Decision they need | Agent response |
|---|---|---|
| Security / Compliance Lead | Which violations create the most control risk? | Risk-ranked queue with exposure, data sensitivity, recurrence, and score factors |
| Cloud Platform Owner | Can this be remediated safely by platform automation? | Eligibility check, permission check, side-effect warning, approval requirement |
| Application Owner | What failed and what must I change? | Owner ticket with policy reason, business impact, remediation steps, verification query |
| IaC Maintainer | Will the issue return after deployment? | Source drift analysis and PR/comment against the likely Terraform or Bicep file |
| Change Approver | What is the blast radius and rollback or next action? | Approval card with affected resources, dependencies, side effects, expected after-state |
| Auditor / Judge | Is this governed and verifiable? | Audit trail with before/after state, approver, action ID, evidence packet |
 
## 8. End-to-end user journey
 
| Step | Persona | What happens | Evidence needed | UI surface |
|---:|---|---|---|---|
| 1 | Security Lead | Ingest Policy, Defender, or fixture findings | Policy ID, resource ID, reason, evaluated time | Upload/import screen |
| 2 | Security Lead / Auditor | Normalize records into one violation model | Canonical evidence object | Worklist |
| 3 | Platform Owner | Enrich context | Resource Graph, tags, owner map, repo map, Defender severity | Violation detail |
| 4 | Security Lead | Score risk and recurrence | Score factors, history, exposure, data class | Ranked worklist |
| 5 | Focused Agent | Detect domain-specific drift/control gap | Storage or NSG runtime/config facts | Finding card |
| 6 | IaC Maintainer | Check source-of-truth drift | Repo path, file, property, CODEOWNER | Source-fix panel |
| 7 | Platform Owner | Select route | Policy effect, remediation support, permission, side effects | Route panel |
| 8 | Change Approver | Approve or reject | Blast radius, rollback/next action, expected after-state | Approval card |
| 9 | Operator / Owner | Generate artifact or dry-run | Ticket payload, PR/comment, remediation plan, exception request | Route view |
| 10 | Auditor | Verify after-state | Before/after state, verification query, policy compliance state | Audit view |
| 11 | Security Lead | Review final digest | Metrics and residual blockers | Summary dashboard |
 
## 9. Inputs and data sources
 
| Input | Required fields | MVP fallback |
|---|---|---|
| Azure Policy compliance details | policyId, policyName, assignmentId, initiative, effect, complianceState, failureReason, evaluatedAt | JSON or CSV fixture with 5 findings |
| Defender for Cloud | recommendation, severity, regulatoryControl, affected resource | sample severity map |
| Azure Resource Graph | tags, resource type, environment, exposure, identity, region, relationships | resource inventory fixture |
| Activity Log and deployment history | caller, deployment, template, pipeline, timestamp, changed properties | deployment history fixture |
| Repo/IaC map | resourceId, repoUrl, repoPath, module, CODEOWNER, pipeline | two-resource repo map |
| Owner map | ownerTeam, ownerEmail, businessApp, supportGroup, escalation path | manual owner CSV |
| Ticketing/change | assignmentGroup, changeType, approvalState, ticketUrl, dueDate | mock ServiceNow/Jira payload |
| Verification source | beforeState, afterState, verificationQuery, expected value | before/after fixture state |
 
## 10. Canonical evidence schema
 
Use this as the first stable backend schema. Store as JSON schema and Pydantic models.
 
```json
{
  "schemaVersion": "1.0.0",
  "violationId": "POL-001",
  "policyEvidence": {
    "policyId": "storage-public-network-disabled",
    "policyName": "Storage accounts should restrict public network access",
    "assignmentId": "cloud-governance-baseline",
    "initiative": "Azure Security Benchmark",
    "complianceState": "NonCompliant",
    "failureReason": "publicNetworkAccess is Enabled",
    "evaluatedAt": "2026-07-09T10:00:00Z"
  },
  "resourceFacts": {
    "resourceId": "/subscriptions/.../resourceGroups/.../providers/Microsoft.Storage/storageAccounts/stpayprod01",
    "resourceType": "Microsoft.Storage/storageAccounts",
    "subscriptionId": "ABI TECHOPS CLOUD ENGG",
    "resourceGroup": "ghq-3-squad3-cloudgov-dev-rg",
    "location": "eastus",
    "tags": { "app": "payments", "environment": "prod" },
    "environment": "Production",
    "productionCriticality": "High"
  },
  "riskSignals": {
    "severity": "High",
    "dataClassification": "Restricted",
    "internetExposure": true,
    "identityImpact": false,
    "dependencyCount": 6,
    "regulatoryControl": "Network Security",
    "focusedSignals": ["storage_public_network_access", "private_endpoint_gap"]
  },
  "ownership": {
    "ownerTeam": "Payments Platform",
    "ownerEmail": "payments-platform@example.com",
    "supportGroup": "CloudOps-Payments",
    "businessApp": "Payments",
    "repoUrl": "https://github.com/org/cloudgov-iac",
    "repoPath": "terraform/storage/payments/storage_account.tf",
    "codeOwner": "@payments-platform",
    "ownerConfidence": "High"
  },
  "remediationEligibility": {
    "policyEffect": "Audit",
    "remediationSupported": false,
    "requiredPermission": "Microsoft.Storage/storageAccounts/write",
    "permissionAvailable": false,
    "restartRisk": "None",
    "downtimeRisk": "Low",
    "costImpact": "None"
  },
  "history": {
    "firstSeen": "2026-07-01T09:00:00Z",
    "lastSeen": "2026-07-09T10:00:00Z",
    "previousFix": "Runtime patch on 2026-07-03",
    "recurrenceCount": 2,
    "sourceDriftLikely": true,
    "sourceConfidence": "High"
  },
  "decision": {
    "riskScore": 94,
    "riskBand": "Critical",
    "scoreFactors": ["high severity", "production", "restricted data", "internet exposed", "recurring", "source drift likely"],
    "blockers": [],
    "recommendedPath": "source_pr_plus_change_ticket",
    "approvalRequired": true,
    "approverRole": "Cloud Governance Approver",
    "rollbackOrNextAction": "Revert PR or restore previous network rule if approved exception exists"
  },
  "actionState": {
    "approver": null,
    "approvedAt": null,
    "ticketId": null,
    "prUrl": null,
    "remediationTaskId": null,
    "actionStatus": "AwaitingApproval"
  },
  "verification": {
    "beforeState": { "publicNetworkAccess": "Enabled" },
    "afterState": null,
    "verificationQuery": "resources | where id =~ '<resourceId>' | project publicNetworkAccess=properties.publicNetworkAccess",
    "expectedCompliantValue": "Disabled",
    "verificationResult": "NotRun",
    "nextAction": "Approve source PR/change and re-query after deployment"
  }
}
```
 
## 11. Decision logic and scoring
 
### 11.1 Score dimensions
 
Use deterministic scoring with a score cap of 100.
 
| Score area | Signal | Points |
|---|---|---:|
| Security impact | Critical or high Defender/policy severity | 20 |
| Blast radius | Production resource or shared platform resource | 15 |
| Data sensitivity | Restricted, regulated, customer, financial, secrets | 20 |
| Internet exposure | Public endpoint, broad CIDR, exposed management plane | 20 |
| Identity impact | Privileged identity, Key Vault, broad role assignment | 15 |
| Recurrence | Previous fix failed or violation reintroduced | 15 |
| Source drift | IaC contains bad value or likely redeploy recurrence | 10 |
| Owner confidence | Strong owner mapping exists | 5 |
 
### 11.2 Score bands
 
| Score | Band |
|---:|---|
| 80-100 | Critical |
| 60-79 | High |
| 40-59 | Medium |
| 0-39 | Low |
 
### 11.3 Safety blockers
 
Safety blockers do not necessarily lower risk. They restrict actionability.
 
| Blocker | Effect |
|---|---|
| missing_owner | block auto-action; route to owner discovery or manual review |
| missing_resource_identity | invalid finding; cannot route |
| missing_failure_reason | route to enrichment |
| missing_verification_query | cannot close; ticket only |
| unknown_downtime_risk | block auto-remediation |
| unknown_dependency_impact | block auto-remediation |
| production_runtime_change | ticket, PR/comment, or dry-run only |
| missing_permission_check | block runtime action |
| source_code_change_without_approval | block source action |
| exception_without_expiry | invalid exception |
 
### 11.4 Actionability score
 
Use a separate actionability view:
 
```text
actionability = ownerConfidence
              + sourceMapConfidence
              + remediationSupport
              + permissionConfidence
              + verificationConfidence
              - blockerWeight
```
 
The dashboard should show high risk but blocked items separately from high risk and actionable items.
 
## 12. Routing logic
 
```text
If resourceId is missing:
    route = invalid_finding
 
Else if owner is missing or side effect is unknown:
    route = blocked_manual_review
 
Else if sourceDriftLikely is true and repoPath exists:
    route = source_pr_plus_change_ticket
 
Else if remediationSupported is true
    and permissionAvailable is true
    and production is false
    and downtimeRisk is low
    and approval is ready:
        route = remediation_dry_run
 
Else if ownerTeam exists:
    route = owner_ticket_or_change_request
 
Else if exception request has owner, justification, compensating control, and expiry:
    route = time_bound_exception
 
Else:
    route = escalation
```
 
## 13. Required agent behavior
 
### 13.1 Core Policy Compliance Agent
 
Purpose:
 
- Ingest Azure Policy, Defender, or fixture findings.
- Normalize into canonical evidence schema.
- Mark missing fields.
- Preserve raw evidence.
 
Inputs:
 
- policy export
- Defender recommendation
- Policy Insights fixture
 
Output:
 
- normalized violation queue
- missing evidence warnings
 
### 13.2 Storage Firewall Compliance Agent
 
Purpose:
 
- Detect storage account public exposure and network-rule drift.
 
Signals:
 
- publicNetworkAccess enabled
- defaultAction allow
- restricted data with missing private endpoint
- source property still enables public access
 
Preferred route:
 
- source PR/comment plus change ticket for production and source drift
- dry-run only for approved non-production runtime remediation
 
Verification:
 
```text
publicNetworkAccess == Disabled
networkAcls.defaultAction == Deny
policy compliance state == Compliant
```
 
### 13.3 NSG Drift Management Agent
 
Purpose:
 
- Detect broad source CIDR, sensitive port exposure, priority drift, and source/runtime mismatch.
 
Signals:
 
- sourceAddressPrefix equals *, Internet, or 0.0.0.0/0
- destinationPortRange includes 22, 3389, 1433, 5432, or broad range
- rule priority changed from baseline
- missing owner or unknown subnet dependency
 
Preferred route:
 
- owner ticket or blocked path for production or missing owner
- remediation dry-run only after approval for non-production low-risk cases
 
Verification:
 
```text
No inbound allow from 0.0.0.0/0 to sensitive management ports
Rule priority matches baseline or approved exception
```
 
### 13.4 Risk and Recurrence Scorer
 
Purpose:
 
- Calculate deterministic risk score and band.
- Explain score factors.
- Keep score separate from actionability.
 
Output:
 
- score
- band
- factor list
- blockers
- confidence
 
### 13.5 Source-of-Truth Drift Agent
 
Purpose:
 
- Compare runtime failure property with Terraform, Bicep, or pipeline configuration.
- Identify whether runtime-only patch would be temporary.
 
Output:
 
- repo URL
- file path
- module
- CODEOWNER
- failing property
- current source value
- expected source value
- PR/comment draft
 
### 13.6 Remediation Routing Planner
 
Purpose:
 
- Select the safest route using evidence, risk, source drift, permission, production gate, and verification readiness.
 
Output:
 
- recommended path
- route reason
- side effects
- required approval
- next action
 
### 13.7 Approval Gate
 
Purpose:
 
- Prevent any cloud, source, network, identity, or production-affecting change without approval.
 
Output:
 
- approval payload
- approver role
- timestamp
- status
- denial reason if rejected
 
### 13.8 Verification and Audit Engine
 
Purpose:
 
- Re-query policy/resource state.
- Compare before and after.
- Enforce no closure without proof.
- Persist evidence packet.
 
Output:
 
- verification result
- after-state
- action ID
- evidence packet
- next action
 
## 14. Backend service design
 
### 14.1 Suggested modules
 
```text
backend/
  app/
    main.py
    api/
      findings.py
      violations.py
      routes.py
      approvals.py
      artifacts.py
      verification.py
      dashboard.py
    core/
      config.py
      security.py
      logging.py
      idempotency.py
    domain/
      models.py
      enums.py
      evidence_schema.py
      scoring.py
      routing.py
      blockers.py
      verification_rules.py
    agents/
      core_policy_agent.py
      storage_firewall_agent.py
      nsg_drift_agent.py
      source_drift_agent.py
      scorer_agent.py
      routing_planner.py
      approval_gate.py
      artifact_composer.py
      verification_engine.py
    connectors/
      azure_policy.py
      defender.py
      resource_graph.py
      key_vault.py
      github.py
      azure_devops.py
      logic_app.py
      ticketing.py
      storage.py
    repositories/
      violations_repo.py
      audit_repo.py
      prompt_state_repo.py
    db/
      session.py
      models.py
      migrations/
    tests/
```
 
### 14.2 API endpoints
 
| Method | Path | Purpose |
|---|---|---|
| POST | /api/ingest/policy | Ingest policy fixture/export |
| POST | /api/ingest/defender | Ingest Defender fixture/export |
| GET | /api/violations | Worklist with filters and sorting |
| GET | /api/violations/{id} | Full finding card details |
| POST | /api/violations/{id}/score | Recalculate score using current rule version |
| POST | /api/violations/{id}/route | Generate route recommendation |
| POST | /api/violations/{id}/approval-request | Create approval payload |
| POST | /api/violations/{id}/approve | Record approval |
| POST | /api/violations/{id}/artifact | Generate ticket, PR/comment, dry-run, exception, blocked card |
| POST | /api/violations/{id}/verify | Run or simulate verification |
| GET | /api/dashboard/summary | Metrics summary |
| GET | /api/audit/{violationId} | Audit trail |
| GET | /api/state/prompts | Prompt implementation state |
 
## 15. PostgreSQL persistence model
 
Minimum tables:
 
| Table | Purpose |
|---|---|
| raw_findings | immutable raw policy/Defender records |
| violations | normalized canonical violation records |
| resource_facts | enriched resource inventory and relationships |
| owner_map | owner and escalation metadata |
| repo_map | resource to repo/file/CODEOWNER mapping |
| risk_scores | score, band, rule version, factors |
| route_recommendations | route, reason, blockers, actionability |
| approvals | approver, timestamp, decision, payload |
| action_artifacts | ticket payloads, PR comments, dry-run plans, exception requests |
| verification_results | before state, after state, query, result |
| exceptions | owner, reason, compensating control, expiry, status |
| audit_events | append-only decision and action log |
| prompt_runs | implementation prompt, status, result, drawback, validation |
 
## 16. Event and workflow design
 
Recommended events:
 
```text
finding.ingested
finding.normalized
finding.enriched
focused_agent.signals_detected
risk.scored
route.planned
approval.requested
approval.approved
artifact.generated
verification.requested
verification.completed
violation.closed
violation.blocked
exception.created
```
 
Use Logic Apps for approval and ticketing integrations. Use scheduled or event-triggered verification after a ticket, PR, or dry-run result is available.
 
## 17. Dashboard and experience requirements
 
### 17.1 Compliance summary
 
Show:
 
- total findings
- critical findings
- repeat violations
- auto-remediable count
- tickets
- PRs/comments
- exceptions
- blocked unsafe actions
- verified fixes
 
### 17.2 Worklist filters
 
Filters:
 
- policy
- severity
- risk band
- exposure
- data classification
- owner
- app
- source drift
- route
- confidence
- status
- blocker
 
### 17.3 Worklist sorting
 
Must show:
 
- raw severity order
- agent-ranked order
 
This proves the scorer improves prioritization.
 
### 17.4 Violation detail
 
Show:
 
- raw evidence
- enriched resource context
- score factors
- focused-agent signals
- source map
- side effects
- recommended path
- approval state
- verification query
 
### 17.5 Route view
 
Show one route artifact at a time:
 
- ticket payload
- PR/comment preview
- remediation dry-run
- exception request
- escalation note
- blocked reason
 
### 17.6 Audit view
 
Show:
 
- before state
- after state
- approver
- action ID
- evidence packet
- next action
- prompt run that generated or changed the behavior
 
## 18. Recommendation or finding card template
 
```text
Violation ID:
<stable ID tied to policy, resource, and evaluation time>
 
Policy and Control:
Policy: <policyName>
Assignment: <assignmentId>
Initiative: <initiative>
Category / Regulatory mapping: <value if available>
 
Resource Context:
Resource ID: <resourceId>
Type: <resourceType>
Environment: <environment>
Owner: <ownerTeam or owner gap>
Business App: <businessApp>
Exposure: <internet exposure / private only>
Data Classification: <classification>
 
Raw Evidence:
Compliance State: <state>
Failure Reason: <reason>
Evaluated At: <timestamp>
 
Risk Explanation:
Risk Score: <score>
Risk Band: <band>
Drivers: <score factor list>
Blockers: <blocker list or none>
Confidence: <evidence confidence>
 
Recommended Route:
<policy task / source PR-comment / owner ticket / change request / exception / escalation / blocked / observe>
 
Approval and Side Effects:
Approval Required: <yes/no>
Approver Role: <role>
Restart Risk: <none/low/unknown>
Downtime Risk: <none/low/unknown>
Security Impact: <impact>
Change Window: <required or not>
Rollback / Next Action: <rollback or next action>
 
Source Fix:
Repo: <repoUrl>
File: <repoPath>
Property: <failingProperty>
Current Source Value: <current>
Expected Source Value: <expected>
 
Artifact:
Ticket ID: <id or draft>
PR/Comment: <url or draft>
Remediation Task: <id or dry-run>
Exception: <request id or not applicable>
 
Verification:
Query: <exact query or property check>
Before: <before state>
After: <after state>
Result: <not run / compliant / failed>
Next Action: <next action>
 
Audit:
Action ID: <id>
Evidence Packet: <blob path or audit id>
Prompt Run: <prompt id>
```
 
## 19. Acceptance criteria mapping
 
| Acceptance criterion | Implementation proof |
|---|---|
| At least five non-compliance records processed | policy_findings.json plus normalized violations table |
| Core agent plus at least two focused agents | Core, Storage Firewall, NSG Drift |
| Each record has score, owner or owner gap, route, verification query | finding card and API response |
| Ranking differs from raw severity-only sorting | worklist toggle and score factors |
| One ticket/change route | generated ticket payload |
| One source PR/comment route | generated PR/comment preview |
| One remediation dry-run after approval | approval payload plus dry-run artifact |
| One blocked/exception unsafe action | blocker card with rule reason |
| Before/after verification for at least one case | verification result and audit packet |
 
## 20. Recommended five demo findings
 
| ID | Focused agent | Finding | Route |
|---|---|---|---|
| POL-001 | Storage Firewall | Production storage account allows public network access | Source PR/comment plus change ticket |
| POL-002 | NSG Drift | NSG allows 0.0.0.0/0 to port 22 or 3389 | Owner ticket or blocked path |
| POL-003 | Core / Key Vault optional | Purge protection disabled | Remediation dry-run after approval |
| POL-004 | Database Firewall optional | SQL/Cosmos/PostgreSQL firewall allows broad CIDR | Exception or change review |
| POL-005 | Core / IP optional | Public IP or network rule drift with missing owner | Blocked manual review |
 
## 21. Callouts for likely misimplementation
 
1. Trying to implement every focused agent before routing, approval, and verification is a misimplementation. Build the required backbone plus Storage and NSG first.
2. Letting each focused agent calculate its own final score is a misimplementation. Focused agents should emit signals; the central scorer calculates score.
3. Combining risk and actionability is a misimplementation. High-risk items can still be blocked.
4. Treating runtime remediation as permanent when source drift exists is a misimplementation.
5. Letting the LLM decide final score, route, approval, or closure is a misimplementation.
6. Closing findings based on ticket or PR creation alone is a misimplementation. Closure requires after-state proof.
7. Auto-changing production resources during the demo is a misimplementation. Use ticket, PR/comment, or dry-run.
8. Creating exceptions without expiry and compensating control is a misimplementation.
 
## 22. Definition of done
 
The implementation is demo-ready when:
 
- five findings are ingested and normalized
- Storage and NSG focused agents emit signals
- scores and ranking are explainable
- raw severity and agent-ranked views differ
- every finding has a route
- one ticket is generated
- one PR/comment is generated
- one remediation dry-run is generated after approval
- one unsafe action is blocked or routed to exception
- at least one before/after verification succeeds
- every changing action has approval, side-effect notes, and rollback or next action
- audit packet exists for each route
- prompt state file is updated for every prompt execution