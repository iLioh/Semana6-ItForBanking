param location string
param appName string
param planName string
param skuName string
param databaseServer string
param databaseName string
param storageUrl string
param openAIEndpoint string
param openAIDeployment string
param vaultUri string
param applicationInsightsConnectionString string
param entraTenantId string
param entraClientId string
param entraAudience string
param enableUserAuth bool
param allowedClientIp string
param corsOrigin string
param tags object

var sqlConnection = 'mssql+pyodbc://@${databaseServer}.database.windows.net/${databaseName}?driver=ODBC+Driver+18+for+SQL+Server&Authentication=ActiveDirectoryMsi&Encrypt=yes&TrustServerCertificate=no'

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  tags: tags
  kind: 'linux'
  sku: { name: skuName, tier: skuName == 'F1' ? 'Free' : 'Basic', capacity: 1 }
  properties: { reserved: true }
}

resource app 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: skuName != 'F1'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appCommandLine: 'uvicorn src.app.main:app --host 0.0.0.0 --port 8000'
      ipSecurityRestrictionsDefaultAction: empty(allowedClientIp) ? 'Allow' : 'Deny'
      ipSecurityRestrictions: empty(allowedClientIp) ? [] : [
        {
          ipAddress: '${allowedClientIp}/32'
          action: 'Allow'
          priority: 100
          name: 'LabPresenterIp'
        }
      ]
      scmIpSecurityRestrictionsUseMain: false
      cors: { allowedOrigins: [corsOrigin], supportCredentials: true }
      appSettings: [
        { name: 'APP_ENV', value: enableUserAuth ? 'production' : 'azure-demo' }
        { name: 'AI_PROVIDER', value: 'azure' }
        { name: 'AUTH_REQUIRED', value: string(enableUserAuth) }
        { name: 'DATABASE_URL', value: sqlConnection }
        { name: 'AZURE_STORAGE_ACCOUNT_URL', value: storageUrl }
        { name: 'AZURE_OPENAI_ENDPOINT', value: openAIEndpoint }
        { name: 'AZURE_OPENAI_DEPLOYMENT', value: openAIDeployment }
        { name: 'AZURE_OPENAI_API_VERSION', value: '2024-10-21' }
        { name: 'KEY_VAULT_URI', value: vaultUri }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: applicationInsightsConnectionString }
        { name: 'ENTRA_TENANT_ID', value: entraTenantId }
        { name: 'ENTRA_CLIENT_ID', value: entraClientId }
        { name: 'ENTRA_AUDIENCE', value: entraAudience }
        { name: 'ENTRA_ISSUER', value: '${environment().authentication.loginEndpoint}${entraTenantId}/v2.0' }
        { name: 'ENTRA_REQUIRED_SCOPE', value: 'Lab.Access' }
        { name: 'CORS_ORIGINS', value: corsOrigin }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
      ]
    }
  }
}

output principalId string = app.identity.principalId
output defaultHostname string = app.properties.defaultHostName
output appId string = app.id
