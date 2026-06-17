targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Nombre del entorno (se usa como prefijo para los recursos)')
param environmentName string

@minLength(1)
@description('Región de Azure para desplegar los recursos')
param location string

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// ── Resource Group ────────────────────────────────────────────────────────
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// ── Storage Account (requerido por Azure Functions) ───────────────────────
module storage './core/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
  }
}

// ── App Service Plan (Consumption) ───────────────────────────────────────
module appServicePlan './core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: rg
  params: {
    name: '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'Y1'
      tier: 'Dynamic'
    }
  }
}

// ── Function App ─────────────────────────────────────────────────────────
module functionApp './core/host/functions.bicep' = {
  name: 'functionapp'
  scope: rg
  params: {
    name: '${abbrs.webSitesFunctions}${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'mcp' })
    appServicePlanId: appServicePlan.outputs.id
    storageAccountName: storage.outputs.name
    runtimeName: 'node'
    runtimeVersion: '20'
  }
}

// ── Outputs ──────────────────────────────────────────────────────────────
output AZURE_FUNCTION_URL string = functionApp.outputs.uri
output AZURE_RESOURCE_GROUP string = rg.name
