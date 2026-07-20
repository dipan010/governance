# Azure Deployment

Deployment scope for the hackathon: **dev-only**, in subscription
**ABI TECHOPS CLOUD ENGG**, resource group **ghq-3-squad3-cloudgov-dev-rg**.
No production deployment happens without explicit human approval
(RULES.md 2.3); the Bicep `environment` parameter only allows `dev`.

## Architecture

| Component | Azure service | Module |
|---|---|---|
| Backend API (FastAPI) | App Service (Linux, Python 3.12), system-assigned managed identity | `infra/bicep/modules/appservice.bicep` |
| Frontend (React) | Static Web Apps (Free tier) | `infra/bicep/modules/staticweb.bicep` |
| Relational state | Azure Database for PostgreSQL Flexible Server, Entra-only auth (password auth disabled) | `infra/bicep/modules/postgres.bicep` |
| Evidence packets | Storage Account (`evidence-packets` container, no public access, default deny) | `infra/bicep/modules/storage.bicep` |
| Secrets | Key Vault (RBAC authorization, soft delete + purge protection) | `infra/bicep/modules/keyvault.bicep` |
| Monitoring | Log Analytics + Application Insights | `infra/bicep/modules/monitoring.bicep` |
| Role assignments | Resource-scoped, least privilege | `infra/bicep/modules/roles.bicep` |

## Secrets

- **Nothing sensitive is committed.** The only secret the app needs
  (`database-url`) lives in Key Vault; App Service resolves it through a
  `@Microsoft.KeyVault(...)` reference using the app's managed identity.
- The backend reads `PCDA_KEY_VAULT_URI` and uses `DefaultAzureCredential`
  when the live connectors replace the fixtures.
- CI never holds long-lived credentials: use **OIDC federated credentials**
  (`azure/login` with `permissions: id-token: write`), never client secrets
  stored in GitHub.

## Deploying (dev only)

```bash
az deployment group what-if \
  --resource-group ghq-3-squad3-cloudgov-dev-rg \
  --template-file infra/bicep/main.bicep \
  --parameters postgresAdminObjectId=<entra-group-object-id> \
               postgresAdminPrincipalName=<entra-group-name>
```

Run `what-if` first, review the diff, and only then replace `what-if` with
`create`. Treat `what-if` as the default mode: it is the deployment analogue
of the agent's remediation dry-run.

After infrastructure exists:

1. Put the PostgreSQL connection URL in Key Vault as `database-url`
   (constructed with Entra token auth, no password).
2. Run `alembic upgrade head` against the server from a trusted network.
3. Deploy backend code (`az webapp deploy`) and frontend
   (`swa deploy frontend/dist`).
4. Verify `GET /health` on the App Service URL.

## Approval gates

- Production values for `environment` are intentionally rejected by the
  template. Extending the allowlist is itself a change that requires the
  Cloud Governance Approver.
- The CI workflows run lint/typecheck/test/build only. A deployment job, if
  added, must target dev, use OIDC, and sit behind a GitHub environment
  protection rule with a required reviewer.

## Event and workflow integrations (future)

Logic Apps handle approval and ticketing integrations; Event Grid or
scheduled triggers re-run verification after a ticket/PR/dry-run completes.
These are integration points behind the existing connector interfaces and
are not provisioned by the MVP template.
