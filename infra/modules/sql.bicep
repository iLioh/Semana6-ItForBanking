param location string
param serverName string
param databaseName string
param administratorLogin string
param administratorObjectId string
param tenantId string
param skuName string
param tags object

resource server 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: serverName
  location: location
  tags: tags
  properties: {
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'User'
      login: administratorLogin
      sid: administratorObjectId
      tenantId: tenantId
      azureADOnlyAuthentication: true
    }
  }
}
resource firewall 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: server
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}
resource database 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: server
  name: databaseName
  location: location
  tags: tags
  sku: { name: skuName }
  properties: { zoneRedundant: false, readScale: 'Disabled' }
}
output serverFqdn string = server.properties.fullyQualifiedDomainName
output databaseName string = database.name
