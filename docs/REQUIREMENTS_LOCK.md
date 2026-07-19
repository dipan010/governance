# Requirements Lock — Policy Compliance and Drift Detection Agent

Status: LOCKED
Locked at: 2026-07-19
Source documents: RULES.md, IMPLEMENTATION_SPEC.md, PROMPT_RUNBOOK.md
Prompt: P01 REQUIREMENTS LOCK

This document freezes scope, acceptance criteria, personas, focused agents, and constraints before any code is written. Changes to this lock require an explicit new decision recorded in IMPLEMENTATION_STATE.md and state.json.

---

## 1. Purpose

Prioritize and remediate Azure governance violations with owner routing, approval gating, and verified after-state.

The system converts Azure Policy, Defender for Cloud, and source-drift findings into a governed workflow: ingest → normalize → enrich → detect domain-specific control drift → score risk and recurrence → route to the safest path → request approval where needed → create ticket / PR-comment / dry-run / exception / escalation / blocked output → verify after-state → persist audit evidence → present a judge-readable dashboard and finding card.

The solution must answer:

- Which findings matter first?
- Who owns the finding?
- Is runtime remediation safe?
- Will the issue return from source configuration?
- What should be approved?
- What artifact was created?
- Did the resource actually become compliant?

## 2. Audience

- Hackathon judges
- Cloud governance team
- Security and compliance leads
- Cloud platform engineering
- Application owners
- IaC maintainers
- Change approvers
- Auditors

## 3. MVP target

The MVP must process **at least five findings** and demonstrate:

- Core Policy Compliance Agent
- Risk and Recurrence Scorer
- Remediation Routing Planner
- Source-of-Truth Drift Agent
- At least two focused control agents (Storage Firewall + NSG Drift — see section 11)
- One source PR/comment
- One ticket or change request
- One remediation dry-run after approval
- One blocked unsafe action or exception route
- One before/after verification result
- One audit packet
- Worklist and finding-card UI

## 4. Cloud scope

Hackathon scope:

- Subscription: **ABI TECHOPS CLOUD ENGG**
- Resource group: **ghq-3-squad3-cloudgov-dev-rg**
- Repository: `dipan010/governance` (this repo)

Approved enterprise Azure-native services (per RULES.md section 5):

- Azure Policy / Policy Insights
- Microsoft Defender for Cloud
- Azure Resource Graph
- Azure Database for PostgreSQL
- Azure Storage Account (evidence packets, artifacts)
- Azure Key Vault (all secrets)
- Azure Logic Apps (approval, ticketing, workflow)
- Azure AI Foundry / Azure OpenAI (summaries and drafts only)
- Azure App Service / Container Apps / AKS (backend hosting)
- Azure Static Web Apps or equivalent (frontend hosting)
- Azure DevOps or GitHub Actions (CI/CD)
- Event Grid, Service Bus, scheduled triggers, or Logic App triggers

MVP fixtures stand in for live Azure APIs behind swappable connector interfaces.

## 5. Primary outcome

A compliance worklist with risk-ranked violations, remediation path, evidence packet, approval state, and verification result — governed end-to-end and auditable per finding.

## 6. Use case portfolio

| Capability | Purpose | MVP output |
|---|---|---|
| Core Policy Compliance Agent | Ingest and normalize Azure Policy or Defender findings | Normalized violation queue |
| Risk and Recurrence Scorer | Rank by real-world risk and actionability | Explainable score and band |
| Remediation Routing Planner | Select safest route | Ticket, PR/comment, dry-run, exception, escalation, or blocked path |
| Source-of-Truth Drift Agent | Prevent recurrence by checking IaC/source | PR/comment with expected after-state |
| Verification and Audit Engine | Prove outcome and store evidence | Before/after result and audit packet |
| Storage Firewall Compliance Agent | Detect storage public exposure and network-rule drift | Focused signals on finding card |
| NSG Drift Management Agent | Detect broad CIDR, management-port exposure, priority drift | Focused signals and blocker candidates |

## 7. Build priority

**P0 — required backbone (built first, never deferred):**

1. Core Policy Compliance Agent (ingest + normalize)
2. Risk and Recurrence Scorer
3. Remediation Routing Planner
4. Source-of-Truth Drift Agent
5. Verification and Audit Engine
6. Approval Gate

**P1 — focused agents for demo (built with the backbone, limited to two):**

- Storage Firewall Compliance Agent — hero scenario (public access, restricted data, source drift, ticket, PR/comment, verification)
- NSG Drift Management Agent — safety scenario (broad CIDR, management port, unsafe remediation, blocked path)

**Deferred (see section 12 — Out of scope).**

Build order follows PROMPT_RUNBOOK.md P02 → P19 exactly.

## 8. Required agent suite

| Agent | Owns | Must NOT do |
|---|---|---|
| Core Policy Compliance Agent | Ingest, normalize to canonical schema, flag missing fields, preserve raw evidence | Discard incomplete findings |
| Storage Firewall Compliance Agent | Emit storage exposure/drift signals | Choose final score or route |
| NSG Drift Management Agent | Emit NSG drift signals and blocker candidates | Choose final score or route; auto-remediate |
| Risk and Recurrence Scorer | Deterministic score, band, factors, blockers, confidence | Use LLM for scoring; hide blockers |
| Source-of-Truth Drift Agent | Runtime-vs-source comparison, PR/comment preview | Create real branch/PR without approval |
| Remediation Routing Planner | Route selection with reason, side effects, approval need | Auto-apply production changes |
| Approval Gate | Approval enforcement for every changing action | Allow bypass; hide rejection reasons |
| Verification and Audit Engine | Closure eligibility, before/after proof, evidence packets | Close without after-state proof |

Architecture constraints (RULES.md section 4): one decision pipeline, not unrelated agents; focused agents emit signals only; central scorer owns scoring; routing planner owns routes; approval gate owns approvals; verification engine owns closure; audit store records everything; state transitions idempotent; every action has a correlation ID; every prompt run updates state files.

## 9. Target personas and decisions

| Persona | Decision they need | Agent response |
|---|---|---|
| Security / Compliance Lead | Which violations create the most control risk? | Risk-ranked queue with exposure, data sensitivity, recurrence, score factors |
| Cloud Platform Owner | Can this be remediated safely by platform automation? | Eligibility check, permission check, side-effect warning, approval requirement |
| Application Owner | What failed and what must I change? | Owner ticket with policy reason, business impact, remediation steps, verification query |
| IaC Maintainer | Will the issue return after deployment? | Source drift analysis and PR/comment against the likely Terraform or Bicep file |
| Change Approver | What is the blast radius and rollback or next action? | Approval card with affected resources, dependencies, side effects, expected after-state |
| Auditor / Judge | Is this governed and verifiable? | Audit trail with before/after state, approver, action ID, evidence packet |

## 10. Acceptance criteria (one-to-one implementation proof)

| # | Acceptance criterion | Implementation proof |
|---|---|---|
| AC-1 | At least five non-compliance records processed | `data/fixtures/policy_findings.json` plus normalized violations table |
| AC-2 | Core agent plus at least two focused agents | Core Policy, Storage Firewall, NSG Drift agents with tests |
| AC-3 | Each record has score, owner or owner gap, route, verification query | Finding card and `GET /api/violations/{id}` response |
| AC-4 | Ranking differs from raw severity-only sorting | Worklist raw-severity vs agent-ranked toggle and score factors |
| AC-5 | One ticket/change route | Generated ticket payload (POL-002 or POL-004) |
| AC-6 | One source PR/comment route | Generated PR/comment preview (POL-001) |
| AC-7 | One remediation dry-run after approval | Approval payload plus dry-run artifact (POL-003) |
| AC-8 | One blocked/exception unsafe action | Blocker card with rule reason (POL-005) |
| AC-9 | Before/after verification for at least one case | Verification result and audit packet (POL-001) |

## 11. Selected focused agents for MVP

Exactly two focused agents are in scope:

1. **Storage Firewall Compliance Agent** — signals: `storage_public_network_access`, `storage_firewall_default_allow`, `private_endpoint_gap`, `source_drift_likely`. Preferred route: source PR/comment plus change ticket for production source drift; dry-run only for approved non-production runtime remediation. Verification: `publicNetworkAccess == Disabled`, `networkAcls.defaultAction == Deny`, policy compliance state `Compliant`.
2. **NSG Drift Management Agent** — signals: `broad_source_cidr`, `sensitive_port_exposed`, `priority_drift`, plus safety-blocker candidates for missing owner / unknown dependency. Preferred route: owner ticket or blocked path for production or missing owner; dry-run only after approval for non-production low-risk cases. Verification: no inbound allow from 0.0.0.0/0 to sensitive management ports; rule priority matches baseline or approved exception.

## 12. Explicit out-of-scope items

Deferred until the backbone (ingest, scoring, routing, approval, verification, audit) is working and demo-ready:

- Key Vault and Secrets Control Agent (optional; only if time permits after P19)
- Database Firewall Compliance Agent (optional; only if time permits after P19)
- IP Change Governance Agent (deferred — needs allowlist/DNS context)
- Exception and Trend Agent (stretch — only after verification and routing are done)
- Live Azure API integration (Policy Insights, Resource Graph, Defender) — fixtures behind connector interfaces for MVP
- Real ServiceNow/Jira ticket creation — mock payloads only
- Real GitHub PR/branch creation — previews only, never without explicit approval
- Any runtime cloud change to real resources — hackathon stops at ticket, PR/comment, or dry-run
- Multi-subscription / multi-resource-group scale-out
- Role-based auth beyond the minimal role model needed for approval gating in the demo

## 13. Assumptions and open questions

Assumptions:

- Fixture data is representative of real Policy Insights / Defender exports and can be swapped for live connectors later without schema change.
- The five demo findings are POL-001..POL-005 as defined in IMPLEMENTATION_SPEC.md section 20.
- PostgreSQL is the target persistence; SQLite may back local tests if wired through the same SQLAlchemy models (drawback recorded if used).
- LLM usage (summaries/drafts) is optional for the demo; all decision logic is deterministic and works without any LLM configured.
- Demo runs against subscription "ABI TECHOPS CLOUD ENGG", resource group "ghq-3-squad3-cloudgov-dev-rg" in read-only/fixture mode.

Open questions (carry-forward drawbacks from P00):

- Ticketing system (ServiceNow vs Jira) not finalized — mock payload shape covers both.
- Approver identities not finalized — approver role names used until identities are provided.
- Azure hosting choice (App Service vs Container Apps) decided at P16.
- Whether Azure OpenAI credentials will be available for draft generation during demo.

## 14. Misimplementation warnings (locked)

1. Implementing every focused agent before routing, approval, and verification is a misimplementation. Build the required backbone plus Storage and NSG first.
2. Letting each focused agent calculate its own final score is a misimplementation. Focused agents emit signals; the central scorer calculates score.
3. Combining risk and actionability is a misimplementation. High-risk items can still be blocked.
4. Treating runtime remediation as permanent when source drift exists is a misimplementation.
5. Letting the LLM decide final score, route, approval, or closure is a misimplementation.
6. Closing findings based on ticket or PR creation alone is a misimplementation. Closure requires after-state proof.
7. Auto-changing production resources during the demo is a misimplementation. Use ticket, PR/comment, or dry-run.
8. Creating exceptions without expiry and compensating control is a misimplementation.
