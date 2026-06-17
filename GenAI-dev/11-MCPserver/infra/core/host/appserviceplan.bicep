@description('Nombre del App Service Plan')
param name string

@description('Ubicación del recurso')
param location string = resourceGroup().location

@description('Tags del recurso')
param tags object = {}

@description('SKU del plan')
param sku object = {
  name: 'Y1'
  tier: 'Dynamic'
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: name
  location: location
  tags: tags
  sku: sku
  properties: {
    reserved: true // Linux
  }
}

output id string = appServicePlan.id
output name string = appServicePlan.name
