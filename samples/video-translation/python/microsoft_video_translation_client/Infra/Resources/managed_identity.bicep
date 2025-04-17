@description('Name of Managed Identity resource.')
param name string = 'id-${uniqueString(resourceGroup().id)}'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of Storage Account resource.')
param storage_account_name string

@description('Name of OpenAI Service resource.')
param openai_service_name string

@description('Name of Speech Service resource.')
param speech_service_name string

resource managed_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
}

//-----------Storage Account Role Assignments-----------//
resource storage_account 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storage_account_name
}

resource storage_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage_account.id, managed_identity.id, storage_blob_data_contributor_role.id)
  scope: storage_account
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: storage_blob_data_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Storage Blob Data Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-contributor).')
resource storage_blob_data_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
    name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

//-----------OpenAI Service Role Assignments-----------//
resource openai_service 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openai_service_name
}

resource openai_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai_service.id, managed_identity.id, cognitive_services_openai_contributor_role.id)
  scope: openai_service
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: cognitive_services_openai_contributor_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Cognitive Services OpenAI Contributor role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#cognitive-services-openai-contributor).')
resource cognitive_services_openai_contributor_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
}

//-----------Speech Service Role Assignments-----------//
resource speech_service 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: speech_service_name
}

resource speech_role_assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(speech_service.id, managed_identity.id, cognitive_services_user_role.id)
  scope: speech_service
  properties: {
    principalId: managed_identity.properties.principalId
    roleDefinitionId: cognitive_services_user_role.id
    principalType: 'ServicePrincipal'
  }
}

@description('Built-in Cognitive Services User role (https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/ai-machine-learning#cognitive-services-user).')
resource cognitive_services_user_role 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: 'a97b65f3-24c7-4388-baec-2e87135dc908'
}

//-----------Outputs-----------//
output name string = managed_identity.name
