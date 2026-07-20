# Permissions — least privilege

Least privilege is mandatory (RULES.md 2.9, 9.3). No identity in this
project holds subscription Owner, and no role is granted at subscription
scope for routine workflows.

## Backend runtime (App Service system-assigned managed identity)

| Role | Scope | Why |
|---|---|---|
| Key Vault Secrets User | the project Key Vault only | read `database-url` and connector API keys; cannot manage the vault |
| Storage Blob Data Contributor | the evidence storage account only | write/read evidence packets in `evidence-packets` |
| Reader | resource group `ghq-3-squad3-cloudgov-dev-rg` | Resource Graph enrichment queries over the demo scope |
| Policy Insights Data Writer (preview) — **not granted in MVP** | — | only needed if live policy re-evaluation triggers are enabled, and only after approval |

Explicitly **not** granted to the runtime identity:

- No `Microsoft.Storage/storageAccounts/write` or any resource `write`
  beyond blob data: the agent proposes changes, it does not apply them.
  Runtime remediation (post-hackathon) would use a separate, per-action
  identity granted just-in-time after approval.
- No Key Vault management roles (no create/delete/purge).
- No role assignments write (cannot escalate itself).

## CI/CD principal (GitHub OIDC federated credential)

| Role | Scope | Why |
|---|---|---|
| Contributor | resource group `ghq-3-squad3-cloudgov-dev-rg` only | deploy Bicep + app code to dev |
| Key Vault Secrets Officer | the project Key Vault only | seed `database-url` during provisioning |

- Federated credential subject is pinned to this repository and branch —
  no long-lived client secret exists.
- The deploy job must sit behind a GitHub environment with a required
  reviewer (the human approval gate for deployments).

## Human roles (application-level, RULES.md 9.8)

| App role | May do |
|---|---|
| viewer | read worklist, cards, audit |
| analyst | ingest fixtures, rescore, re-route |
| approver | decide approval requests |
| operator | generate artifacts, run verification, close (with proof) |
| auditor | read audit trails and evidence packets |
| admin | all of the above (local/test only until Entra ID wiring) |

## Data-plane restrictions

- PostgreSQL: Entra-only authentication; password auth disabled at the
  server; no connection strings with embedded passwords anywhere.
- Storage: public blob access disabled, network default deny,
  TLS 1.2 minimum.
- Key Vault: RBAC authorization, soft delete and purge protection enabled.
- Audit events are append-only at the application layer; production
  hardening would add immutable blob storage for evidence packets.
