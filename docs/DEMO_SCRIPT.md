# Demo script — Policy Compliance and Drift Detection Agent

Scope shown on screen: subscription **ABI TECHOPS CLOUD ENGG**, resource
group **ghq-3-squad3-cloudgov-dev-rg**. Total time ≈ 7 minutes.

## Setup (before the demo)

```bash
# Terminal 1 — backend
cd backend && .venv/bin/python -m uvicorn app.main:app --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev          # http://localhost:5173

# Terminal 3 — seed the demo data
curl -s -X POST http://127.0.0.1:8000/api/ingest/policy \
  -H 'Content-Type: application/json' \
  -d @data/demo/demo_seed.json
```

## Flow

### 1. Open the worklist (Security Lead)
Open http://localhost:5173. Point at the scope line and the summary
metrics: five findings, one Critical.
> "Five real governance violations from our dev resource group, ingested
> from Azure Policy and Defender evidence and normalized into one canonical
> schema."

### 2. Raw severity order
Click **Raw severity**. POL-002 (Critical raw severity) is on top.
> "Sorted by raw severity, the NSG rule looks most urgent."

### 3. Agent-ranked order
Click **Agent-ranked**. POL-001 (score 100, Critical band) takes the top.
> "The scorer disagrees — deterministically. Production, restricted data,
> internet exposure, a recurrence, and source drift add up to 100. The
> ranking is explainable, not a black box: every point is a listed factor."

### 4. Open POL-001 (the hero finding)
Click **POL-001**. Walk the card top to bottom:
- Resource context: production storage account, restricted data, owner
  *Payments Platform* (High confidence).
- Focused signals from the Storage Firewall agent: public network access,
  default allow, private endpoint gap, source drift.
- Score factors with points; blockers visible (production runtime change).
- **Source fix panel**: `terraform/storage/payments/storage_account.tf`,
  CODEOWNER @payments-platform, with the temporary-runtime-patch warning.
> "Fixing this at runtime would be temporary — the Terraform still says
> `public_network_access_enabled = true`. So the agent routes to a source
> PR plus a change ticket."

### 5. Route + approval on POL-001
Show the route panel: **Generate artifact is disabled** until approval.
Request approval, approve as `cloudgov-approver`, then generate: the
PR/comment preview and the change ticket appear (drafts — nothing is
pushed to GitHub or a ticketing system).

### 6. POL-003 dry-run after approval (Change Approver)
Open **POL-003** (Key Vault purge protection, dev, actionability 80, zero
blockers). Click Generate artifact → refused (403, approval required).
Request approval → approve → generate: the **remediation dry-run plan**
appears, stating "make NO live change".
> "Even the safest automated path executes nothing without a human
> approval, and even then it is a what-if plan."

### 7. POL-005 blocked unsafe action (Auditor)
Open **POL-005**. Owner gap is front and center; route is
**Blocked: manual review**; the blocked card cites the exact rule
("RULES.md 2.7: missing owner blocks auto-action") and the safe
alternative (owner discovery).
> "High-noise finding, no owner, unknown side effects — the agent refuses
> to act and says why."

### 8. Verified after-state and audit packet (Auditor)
Back on **POL-001**: click **Close violation** → refused (no proof).
Click **Run verification** → before `publicNetworkAccess: Enabled`,
after `Disabled`, result **Compliant**. Now Close succeeds. Open the
audit timeline: every step from `finding.ingested` to `violation.closed`,
each with a correlation ID, the prompt run that produced the behavior,
and the evidence packet location.

### 9. Close with metrics (Security Lead)
Scroll to the summary: tickets 2, PR/comments 1, exception 1, blocked 1,
verified 1.
> "Every finding got a governed outcome: prioritized, owner-routed,
> approval-gated, and closed only with proof."

## Hard rules the demo never breaks

- No runtime cloud change, no real PR, no real ticket — drafts and
  previews only.
- Production stops at ticket / PR-comment / dry-run.
- Nothing closes without before/after proof.
- The LLM never decides scores, routes, approvals, or closure.
