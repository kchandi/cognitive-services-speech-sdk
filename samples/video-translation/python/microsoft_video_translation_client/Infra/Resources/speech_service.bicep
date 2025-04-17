@description('The Azure region for the Speech Service.')
param location string = resourceGroup().location

@description('The name of the Speech Service.')
param name string = 'speech-${uniqueString(resourceGroup().id)}'

@description('Custom subdomain name for the Speech Service endpoint.')
param customSubDomainName string = ''

var skuName = 'S0'

// Speech Service resource
resource speechService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  sku: {
    name: skuName
  }
  kind: 'SpeechServices'
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: !empty(customSubDomainName) ? customSubDomainName : toLower(name)
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Output the Speech Service name, endpoint and key for use in other templates
output name string = speechService.name
output id string = speechService.id
output endpoint string = speechService.properties.endpoint
output region string = location
