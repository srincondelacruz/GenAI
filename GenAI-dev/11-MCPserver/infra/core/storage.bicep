@description('Nombre de la Storage Account')
param name string

@description('Ubicación del recurso')
param location string = resourceGroup().location

@description('Tags del recurso')
param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

output name string = storageAccount.name
output id string = storageAccount.id
