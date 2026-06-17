@description('Nombre de la Function App')
param name string

@description('Ubicación del recurso')
param location string = resourceGroup().location

@description('Tags del recurso')
param tags object = {}

@description('ID del App Service Plan')
param appServicePlanId string

@description('Nombre de la Storage Account')
param storageAccountName string

@description('Runtime de la Function App')
param runtimeName string = 'node'

@description('Versión del runtime')
param runtimeVersion string = '20'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: name
  location: location
  tags: tags
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: '${toUpper(runtimeName)}|${runtimeVersion}'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: runtimeName
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '~${runtimeVersion}'
        }
      ]
      cors: {
        allowedOrigins: ['*']
      }
      minTlsVersion: '1.2'
    }
  }
}

output id string = functionApp.id
output name string = functionApp.name
output uri string = 'https://${functionApp.properties.defaultHostName}'
