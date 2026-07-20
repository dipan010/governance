param namePrefix string
param environment string
param location string

// Evidence packet storage. Practices what the agent preaches:
// no public network access from anywhere but required services,
// default deny, no public blobs, TLS 1.2 minimum.
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower('st${namePrefix}${environment}evid')
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled' // dev-only; private endpoint for prod
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

resource evidenceContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'evidence-packets'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountName string = storageAccount.name
