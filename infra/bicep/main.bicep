// Policy Compliance and Drift Detection Agent — Azure environment.
// Dev-only by default; production deployment requires explicit approval
// (RULES.md 2.3). No secrets appear in these templates: everything
// sensitive lives in Key Vault and is read via managed identity.

targetScope = 'resourceGroup'

@description('Prefix for all resource names')
param namePrefix string = 'cloudgov'

@description('Deployment environment; production requires approval')
@allowed(['dev'])
param environment string = 'dev'

param location string = resourceGroup().location

@description('Entra ID admin object ID for PostgreSQL')
param postgresAdminObjectId string

@description('Entra ID admin principal name for PostgreSQL')
param postgresAdminPrincipalName string

var suffix = '${namePrefix}-${environment}'

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    suffix: suffix
    location: location
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyVault'
  params: {
    suffix: suffix
    location: location
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    namePrefix: namePrefix
    environment: environment
    location: location
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    suffix: suffix
    location: location
    adminObjectId: postgresAdminObjectId
    adminPrincipalName: postgresAdminPrincipalName
  }
}

module appService 'modules/appservice.bicep' = {
  name: 'appService'
  params: {
    suffix: suffix
    location: location
    keyVaultName: keyVault.outputs.keyVaultName
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
  }
}

module staticWeb 'modules/staticweb.bicep' = {
  name: 'staticWeb'
  params: {
    suffix: suffix
    location: location
  }
}

// Least-privilege role assignments for the backend's managed identity:
// scoped to the individual resources, never the subscription.
module roles 'modules/roles.bicep' = {
  name: 'roles'
  params: {
    backendPrincipalId: appService.outputs.backendPrincipalId
    keyVaultName: keyVault.outputs.keyVaultName
    storageAccountName: storage.outputs.storageAccountName
  }
}

output backendUrl string = appService.outputs.backendUrl
output keyVaultName string = keyVault.outputs.keyVaultName
output storageAccountName string = storage.outputs.storageAccountName
