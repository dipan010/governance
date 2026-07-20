param backendPrincipalId string
param keyVaultName string
param storageAccountName string

// Built-in role definition IDs (least privilege, narrow scope):
// Key Vault Secrets User — read secret values only, no management.
var keyVaultSecretsUser = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '4633458b-17de-408a-b874-0445c86b69e6'
)
// Storage Blob Data Contributor — evidence packet read/write only.
var storageBlobDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource kvSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, backendPrincipalId, keyVaultSecretsUser)
  scope: keyVault
  properties: {
    principalId: backendPrincipalId
    roleDefinitionId: keyVaultSecretsUser
    principalType: 'ServicePrincipal'
  }
}

resource blobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, backendPrincipalId, storageBlobDataContributor)
  scope: storageAccount
  properties: {
    principalId: backendPrincipalId
    roleDefinitionId: storageBlobDataContributor
    principalType: 'ServicePrincipal'
  }
}
