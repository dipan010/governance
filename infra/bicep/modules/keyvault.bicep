param suffix string
param location string

// RBAC authorization only — no legacy access policies. Secrets are read
// by the backend's managed identity (Key Vault Secrets User at vault scope).
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${suffix}'
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled' // dev-only; private endpoint for prod
    networkAcls: {
      defaultAction: 'Allow' // dev-only; Deny + allowlist for prod
      bypass: 'AzureServices'
    }
  }
}

output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
