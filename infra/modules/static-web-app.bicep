param location string
param appName string
param skuName string
param tags object

resource app 'Microsoft.Web/staticSites@2023-12-01' = {
  name: appName
  location: location
  tags: tags
  sku: { name: skuName, tier: skuName }
  properties: { allowConfigFileUpdates: true }
}
output defaultHostname string = app.properties.defaultHostname
output resourceId string = app.id
