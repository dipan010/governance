param suffix string
param location string
param adminObjectId string
param adminPrincipalName string

// Entra ID authentication only — no password auth, no connection strings
// in source. The backend authenticates with its managed identity.
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: 'psql-${suffix}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    storage: { storageSizeGB: 32 }
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled'
      tenantId: subscription().tenantId
    }
    network: {
      publicNetworkAccess: 'Enabled' // dev-only; VNet integration for prod
    }
  }
}

resource admin 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2023-12-01-preview' = {
  parent: postgres
  name: adminObjectId
  properties: {
    principalType: 'Group'
    principalName: adminPrincipalName
    tenantId: subscription().tenantId
  }
}

output serverName string = postgres.name
output serverFqdn string = postgres.properties.fullyQualifiedDomainName
