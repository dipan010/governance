# Policy Compliance & Drift Detection Console

An Azure-native governance console that turns Azure Policy, Defender, and
source-drift findings into a risk-ranked, routed, approved, and verified
remediation worklist.

```bash
npm install
npm run dev          # http://localhost:5174
```

## The story this UI tells

1. Findings are ingested and normalized into one violation model.
2. A deterministic scorer **re-ranks them differently from raw severity** —
   toggle the worklist ordering to see the top of the list change.
3. Each finding gets the safest available route.
4. Changing actions require approval, with side effects and rollback shown.
5. Nothing closes without before/after verification proof and an audit packet.

## Screens

| Route | Screen | What it shows |
|---|---|---|
| `/` | Dashboard | Nine compliance metrics plus a **risk vs actionability** split — high risk *and actionable* separately from high risk *but blocked* |
| `/worklist` | Worklist | Filterable table with the raw-severity vs agent-ranked toggle |
| `/violations/:id` | Finding card | Raw evidence, enriched context, score drivers as chips, blockers, focused-agent signals, source map, route, approval state, verification query |
| `/violations/:id/route` | Route view | One route artifact at a time plus the approval card and verification panel |
| `/violations/:id/audit` | Audit view | Append-only trail with before/after state, approver, action ID, evidence packet, and the prompt run |

## API-ready seam

All data access goes through **`src/data/dataClient.ts`**. No screen or
component imports `mockClient` or `apiClient` directly, and every function
returns a Promise whose signature matches the backend contract.

```bash
# .env
VITE_USE_MOCK=true    # in-memory mock (default)
VITE_USE_MOCK=false   # real FastAPI backend, proxied to :8000 by Vite
```

Switching to production is that one flag — no component changes.

| DataClient method | Backend endpoint |
|---|---|
| `ingestPolicy` / `ingestDefender` | `POST /api/ingest/policy` · `/defender` |
| `listViolations` / `getViolation` | `GET /api/violations` · `/{id}` |
| `score` / `route` | `POST /api/violations/{id}/score` · `/route` |
| `requestApproval` / `approve` | `POST /api/violations/{id}/approval-request` · `/approve` |
| `generateArtifact` / `verify` | `POST /api/violations/{id}/artifact` · `/verify` |
| `dashboardSummary` | `GET /api/dashboard/summary` |
| `auditTrail` | `GET /api/audit/{violationId}` |

### The client is deliberately "dumb"

Scoring, routing, approval, and closure are **server responsibilities**. This
UI only *displays* those values — it never computes a final score, chooses a
route, or closes a finding. Worklist ordering is presentation only; the
scores it sorts by come from the server. That is what keeps the backend swap
to a single file.

## Seed data

Five findings, with the agent ranking deliberately differing from raw
severity:

| ID | Finding | Route | Note |
|---|---|---|---|
| POL-001 | Prod storage allows public network access | `source_pr_plus_change_ticket` | Recurring + source drift → **top of the agent ranking**; verification already Compliant |
| POL-002 | NSG allows 0.0.0.0/0 to port 22 | `blocked_manual_review` | Highest *raw* severity but blocked on a missing owner |
| POL-003 | Key Vault purge protection disabled | `remediation_dry_run` | Starts unapproved so the full request → approve → generate journey is demonstrable |
| POL-004 | PostgreSQL firewall allows broad CIDR | `time_bound_exception` | Exception carries owner, justification, compensating control, expiry |
| POL-005 | Public IP drift, missing owner | `blocked_manual_review` | Verification `NotRun` |

Raw severity order: POL-002, POL-005, POL-001, POL-004, POL-003
Agent-ranked order: **POL-001**, POL-002, POL-004, POL-003, POL-005

## Architecture

- **Screens** fetch; **components** are presentational. All fetching goes
  through `store/` hooks that call `data/dataClient.ts`.
- `store/useViolations.ts` holds a session cache so an approval granted on
  the route view is still visible on the finding card and audit trail.
- Every async call has loading skeletons, an error state with retry, and an
  empty state — the mock simulates latency so those states are real.
- Light and dark themes share one component layer via CSS variable tokens in
  `src/styles/globals.css`.
- Accessible: keyboard-navigable table rows, labelled filters, visible focus
  rings, semantic landmarks, and a skip link.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Dev server on :5174 |
| `npm run build` | Typecheck + production build |
| `npm run typecheck` | `tsc` strict, no emit |
| `npm run lint` | ESLint |
