// main.bicep - Azure PostgreSQL Flexible Server with pgvector and Azure OpenAI
// Target: Cost-optimized vector database solution with AI capabilities

@description('The name of the resource group to deploy resources to')
param resourceGroupName string = resourceGroup().name

@description('The Azure region where resources will be deployed')
param location string = resourceGroup().location

// PostgreSQL Parameters
@description('The name of the PostgreSQL server (must be globally unique)')
@minLength(3)
@maxLength(63)
param serverName string = toLower('psql-${uniqueString(resourceGroup().id)}')

@description('The admin username for the PostgreSQL server')
@minLength(1)
param adminUsername string

@description('The admin password for the PostgreSQL server')
@secure()
@minLength(8)
@maxLength(128)
param adminPassword string

// Azure OpenAI Parameters
@description('Name of the Azure OpenAI service')
param openAIServiceName string = 'oai-${uniqueString(resourceGroup().id)}'

@description('The SKU of the Azure OpenAI service')
@allowed([
  'S0'
  'S1'
  'S2'
  'S3'
])
param openAISku string = 'S0'

@description('The name of the deployment for the embedding model')
param embeddingDeploymentName string = 'text-embedding-ada-002'

@description('The model version to use for embeddings')
param embeddingModelVersion string = '2'

// Azure Cognitive Services for text analytics (optional)
param cognitiveServicesName string = 'cog-${uniqueString(resourceGroup().id)}'

// Resource Tags
param tags object = {
  environment: 'Production'
  workload: 'VectorDatabase'
  managedBy: 'Bicep'
}

// Azure OpenAI Service
resource openAIService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAIServiceName
  location: location
  sku: {
    name: openAISku
  }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: toLower(openAIServiceName)
    publicNetworkAccess: 'Enabled'
    apiProperties: {
      capabilities: [
        {
          name: 'text-embedding-ada-002'
          version: embeddingModelVersion
        }
      ]
    }
  }
  tags: union(tags, {
    component: 'OpenAIService'
  })
}

// Output the OpenAI endpoint and key for reference
output openAIEndpoint string = openAIService.properties.endpoint
output openAIKey string = listKeys(openAIService.name, openAIService.apiVersion).key1
output embeddingModelDeploymentName string = embeddingDeploymentName

@description('The PostgreSQL server version')
@allowed([
  '15'
])
param serverVersion string = '15'

@description('The SKU name for the PostgreSQL server (Burstable tier for cost optimization)')
@allowed([
  'Standard_B1ms'     // 1 vCore, 2GB RAM - Development/Test
  'Standard_B2s'      // 2 vCores, 4GB RAM - Production Light
  'Standard_D2s_v4'   // 2 vCores, 8GB RAM - Production
])
param skuName string = 'Standard_B1ms'

@description('Initial storage size in GB (min 32GB)')
@minValue(32)
@maxValue(16384)
param storageSizeGB int = 32

@description('Enable auto-grow for storage')
param storageAutoGrow bool = true

@description('Backup retention period in days')
@minValue(7)
@maxValue(35)
param backupRetentionDays int = 7

@description('The name of the initial database')
param databaseName string = 'vectordb'

@description('Enable public network access (for initial setup, disable in production)')
param publicNetworkAccess bool = true

@description('Allowed IP addresses for firewall rules')
@maxLength(50)
array allowedIPRanges = [
  '0.0.0.0/0'  // WARNING: Restrict this in production
]

// Main PostgreSQL Flexible Server resource
resource postgresqlServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: serverName
  location: location
  sku: {
    name: skuName
    tier: contains(skuName, 'Standard_B') ? 'Burstable' : 'GeneralPurpose'
  }
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: serverVersion
    storage: {
      storageSizeGB: storageSizeGB
      autoGrow: storageAutoGrow ? 'Enabled' : 'Disabled'
    }
    backup: {
      backupRetentionDays: backupRetentionDays
      geoRedundantBackup: 'Disabled'  // Enable for production
    }
    highAvailability: {
      mode: 'Disabled'  // Enable for production
    }
    network: {
      publicNetworkAccess: publicNetworkAccess ? 'Enabled' : 'Disabled'
      delegatedSubnetResourceId: null  // Set for VNet integration
    }
  }
  tags: {
    environment: 'Development'
    workload: 'VectorDatabase'
  }
}

// Configure firewall rules for public access
resource firewallRules 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = [for ip in allowedIPRanges: {
  name: 'allow_${replace(ip, '/', '_')}'
  parent: postgresqlServer
  properties: {
    startIpAddress: split(ip, '/')[0]
    endIpAddress: split(ip, '/')[0]
  }
}]

// Create the initial database
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgresqlServer
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Enable pgvector extension
resource vectorExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-03-01-preview' = {
  parent: postgresqlServer
  name: 'azure.extensions'
  properties: {
    source: 'user-override'
    value: 'VECTOR'
  }
}

// Optional: Enable query store for performance monitoring
resource queryStoreConfig 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-03-01-preview' = {
  parent: postgresqlServer
  name: 'pg_qs.query_capture_mode'
  properties: {
    source: 'user-override'
    value: 'TOP'
  }
}

// Output the connection details
output serverFqdn string = postgresqlServer.properties.fullyQualifiedDomainName
output databaseName string = databaseName
output adminUsername string = adminUsername
output connectionString string = 'postgresql://${adminUsername}%40${serverName}:${adminPassword}@${postgresqlServer.properties.fullyQualifiedDomainName}:5432/${databaseName}?sslmode=require'
