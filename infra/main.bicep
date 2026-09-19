targetScope = 'resourceGroup'

@description('Prefijo corto y unico para los recursos.')
param projectName string = 'lab06banking'
@allowed(['dev', 'test', 'prod'])
param environment string = 'dev'
param location string = resourceGroup().location
param tags object = { project: 'IBLaboratorio06', environment: environment, academic: 'true' }
param sqlEntraAdminLogin string
param sqlEntraAdminObjectId string
param entraTenantId string = tenant().tenantId
param entraApiClientId string = ''
param entraApiAudience string = empty(entraApiClientId) ? '' : 'api://${entraApiClientId}'
@description('Activa autenticacion de usuarios con Entra. En tenants educativos restringidos puede desactivarse para una demo con IP permitida.')
param enableUserAuth bool = false
@description('IPv4 publica del presentador. Si se define, el API rechaza cualquier otra IP.')
param allowedClientIp string = '0.0.0.0'
param azureOpenAIDeployment string = 'gpt-5-mini'
param deployAzureOpenAI bool = false
param existingAzureOpenAIName string = ''
@allowed(['F1', 'B1'])
param appServiceSku string = 'F1'
@allowed(['Basic', 'S0'])
param sqlSku string = 'Basic'

var suffix = uniqueString(subscription().subscriptionId, resourceGroup().id, projectName, environment)
var names = {
  app: take('${projectName}-${environment}-api-${suffix}', 60)
  plan: take('${projectName}-${environment}-plan', 40)
  sql: take('${projectName}-${environment}-sql-${suffix}', 63)
  database: '${projectName}-${environment}'
  storage: take(replace('${projectName}${environment}${suffix}', '-', ''), 24)
  vault: take('${projectName}-${environment}-kv-${suffix}', 24)
  workspace: take('${projectName}-${environment}-logs', 63)
  insights: take('${projectName}-${environment}-appi', 255)
  openai: take('${projectName}-${environment}-aoai-${suffix}', 63)
}

module observability 'modules/observability.bicep' = {
  name: 'observability'
  params: { location: location, workspaceName: names.workspace, insightsName: names.insights, tags: tags }
}
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: { location: location, accountName: names.storage, tags: tags }
}
module sql 'modules/sql.bicep' = {
  name: 'sql'
  params: { location: location, serverName: names.sql, databaseName: names.database, administratorLogin: sqlEntraAdminLogin, administratorObjectId: sqlEntraAdminObjectId, tenantId: entraTenantId, skuName: sqlSku, tags: tags }
}
module vault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: { location: location, vaultName: names.vault, tenantId: entraTenantId, tags: tags }
}
module openai 'modules/openai.bicep' = if (deployAzureOpenAI) {
  name: 'openai'
  params: { location: location, accountName: names.openai, deploymentName: azureOpenAIDeployment, tags: tags }
}

var openAIId = deployAzureOpenAI ? openai!.outputs.accountId : resourceId('Microsoft.CognitiveServices/accounts', existingAzureOpenAIName)
var openAIEndpoint = deployAzureOpenAI ? openai!.outputs.endpoint : 'https://${existingAzureOpenAIName}.openai.azure.com/'

module backend 'modules/appservice.bicep' = {
  name: 'backend'
  params: { location: location, appName: names.app, planName: names.plan, skuName: appServiceSku, databaseServer: names.sql, databaseName: names.database, storageUrl: storage.outputs.accountUrl, openAIEndpoint: openAIEndpoint, openAIDeployment: azureOpenAIDeployment, vaultUri: vault.outputs.vaultUri, applicationInsightsConnectionString: observability.outputs.connectionString, entraTenantId: entraTenantId, entraClientId: entraApiClientId, entraAudience: entraApiAudience, enableUserAuth: enableUserAuth, allowedClientIp: allowedClientIp, corsOrigin: 'https://${names.app}.azurewebsites.net', tags: tags }
}
module permissions 'modules/rbac.bicep' = {
  name: 'rbac'
  params: { principalId: backend.outputs.principalId, storageId: storage.outputs.accountId, keyVaultId: vault.outputs.vaultId, openAIId: openAIId }
}

output frontendHostname string = backend.outputs.defaultHostname
output backendHostname string = backend.outputs.defaultHostname
output backendPrincipalId string = backend.outputs.principalId
output sqlServerName string = names.sql
output storageAccountName string = names.storage
output openAIResourceId string = openAIId
output nextSteps array = [
  enableUserAuth ? 'Assign Entra app roles Analyst and Reviewer and expose Lab.Access.' : 'Demo access is restricted to the configured presenter IP; Entra remains pending tenant-admin permission.'
  'Create the contained Azure SQL user for the App Service managed identity.'
  'Build React before packaging; FastAPI serves frontend/dist from the same App Service.'
]
