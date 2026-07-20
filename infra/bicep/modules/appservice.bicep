param suffix string
param location string
param keyVaultName string
param appInsightsConnectionString string

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'plan-${suffix}'
  location: location
  kind: 'linux'
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true
  }
}

// System-assigned managed identity: no client secrets anywhere.
resource backend 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-${suffix}-api'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'PCDA_ENVIRONMENT'
          value: 'dev'
        }
        {
          name: 'PCDA_KEY_VAULT_URI'
          value: 'https://${keyVaultName}${az.environment().suffixes.keyvaultDns}/'
        }
        {
          // Secret reference resolved by App Service via managed identity;
          // the secret value itself never appears in source or settings.
          name: 'PCDA_DATABASE_URL'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultName};SecretName=database-url)'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsightsConnectionString
        }
      ]
    }
  }
}

output backendPrincipalId string = backend.identity.principalId
output backendUrl string = 'https://${backend.properties.defaultHostName}'
