// ========== main.bicep ========== //
targetScope = 'resourceGroup'

@description('GPT model deployment type.')
@allowed([
  'Standard'
  'GlobalStandard'
])
param gpt_deployment_type string = 'GlobalStandard'

@description('Name of GPT model to deploy.')
@allowed([
  'gpt-4o-mini'
  'gpt-4o'
  'gpt-4'
])
param gpt_model_name string = 'gpt-4o-mini'

@description('Capacity of GPT model deployment.')
param gpt_deployment_capacity int = 20

@description('Name of Embedding model to deploy.')
@allowed([
  'text-embedding-ada-002'
])
param embedding_model_name string = 'text-embedding-ada-002'

@description('Capacity of embedding model deployment.')
param embedding_deployment_capacity int = 20

// Deploy resources:
module storage_account 'resources/storage_account.bicep' = {
  name: 'deploy_storage_account'
}

module openai_service 'resources/openai_service.bicep' = {
  name: 'deploy_openai_service'
  params: {
    gpt_model_name: gpt_model_name
    gpt_deployment_capacity: gpt_deployment_capacity
    embedding_model_name: embedding_model_name
    embedding_deployment_capacity: embedding_deployment_capacity
    gpt_deployment_type: gpt_deployment_type
  }
}

module speech_service 'resources/speech_service.bicep' = {
  name: 'deploy_speech_service'
  params: {
    name: 'sk-video-speech-${uniqueString(resourceGroup().id)}'
    location: resourceGroup().location
  }
}

module managed_identity 'resources/managed_identity.bicep' = {
  name: 'deploy_managed_identity'
  params: {
    speech_service_name: speech_service.outputs.name
    openai_service_name: openai_service.outputs.name
    storage_account_name: storage_account.outputs.name
  }
}

// // Deploy container app:
// module container_group 'resources/container_group.bicep' = {
//   name: 'deploy_container_group'
//   params: {
//     aoai_deployment: openai_service.outputs.gpt_deployment_name
//     aoai_endpoint: openai_service.outputs.endpoint
//     speech_endpoint: speech_service.outputs.endpoint
//     managed_identity_name: managed_identity.outputs.name
//     blob_container_name: storage_account.outputs.blob_container_name
//     embedding_deployment_name: openai_service.outputs.embedding_deployment_name
//     embedding_model_dimensions: openai_service.outputs.embedding_model_dimensions
//     embedding_model_name: openai_service.outputs.embedding_model_name
//     storage_account_connection_string: storage_account.outputs.connection_string
//     storage_account_name: storage_account.outputs.name
//   }
// }

// output WEB_APP_URL string = container_group.outputs.fqdn
