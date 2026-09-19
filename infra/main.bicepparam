using './main.bicep'

param projectName = 'lab06banking'
param environment = 'dev'
param location = 'westus3'
param sqlEntraAdminLogin = 'REPLACE_WITH_ENTRA_ADMIN_NAME'
param sqlEntraAdminObjectId = '00000000-0000-0000-0000-000000000000'
param entraApiClientId = '00000000-0000-0000-0000-000000000000'
param enableUserAuth = false
param allowedClientIp = '0.0.0.0'
param deployAzureOpenAI = false
param azureOpenAIDeployment = 'gpt-5-mini'
param existingAzureOpenAIName = 'REPLACE_WITH_EXISTING_RESOURCE'
param appServiceSku = 'F1'
param sqlSku = 'Basic'
