param principalId string
param storageId string
param keyVaultId string
param openAIId string

var blobContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var keyVaultSecretsUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var openAIUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: last(split(storageId, '/'))
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: last(split(keyVaultId, '/'))
}
resource openai 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: last(split(openAIId, '/'))
}

resource storageRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, principalId, blobContributor)
  scope: storage
  properties: { roleDefinitionId: blobContributor, principalId: principalId, principalType: 'ServicePrincipal' }
}
resource vaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, principalId, keyVaultSecretsUser)
  scope: vault
  properties: { roleDefinitionId: keyVaultSecretsUser, principalId: principalId, principalType: 'ServicePrincipal' }
}
resource openAIRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai.id, principalId, openAIUser)
  scope: openai
  properties: { roleDefinitionId: openAIUser, principalId: principalId, principalType: 'ServicePrincipal' }
}
