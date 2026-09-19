param location string
param accountName string
param deploymentName string
param tags object

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: { customSubDomainName: accountName, publicNetworkAccess: 'Enabled', disableLocalAuth: true }
}
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: deploymentName
  sku: { name: 'GlobalStandard', capacity: 30 }
  properties: { model: { format: 'OpenAI', name: 'gpt-5-mini', version: '2025-08-07' }, versionUpgradeOption: 'OnceNewDefaultVersionAvailable' }
}
output accountId string = account.id
output endpoint string = account.properties.endpoint
