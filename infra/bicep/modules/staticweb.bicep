param suffix string
param location string

resource staticSite 'Microsoft.Web/staticSites@2023-12-01' = {
  name: 'stapp-${suffix}-ui'
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    allowConfigFileUpdates: true
  }
}

output staticSiteName string = staticSite.name
