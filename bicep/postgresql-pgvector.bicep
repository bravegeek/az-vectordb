// Azure PostgreSQL with pgvector POC Infrastructure
@description('Environment name (dev, test, prod)')
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Administrator username for PostgreSQL')
param adminUsername string = 'pgadmin'

@description('Administrator password for PostgreSQL')
@secure()
param adminPassword string

@description('Your IP address for firewall rules')
param clientIpAddress string

// Variables
var resourcePrefix = 'vectordb-${environment}'
var postgresqlServerName = '${resourcePrefix}-postgresql-${substring(uniqueString(resourceGroup().id), 0, 6)}'
// Key Vault name limited to 24 chars: vdb-{env}-{hash}
var keyVaultName = 'vdb-${environment}-${substring(uniqueString(resourceGroup().id), 0, 5)}'
var openAiAccountName = '${resourcePrefix}-openai-${substring(uniqueString(resourceGroup().id), 0, 5)}'

// Key Vault for secrets management
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// PostgreSQL Flexible Server
resource postgresqlServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: postgresqlServerName
  location: 'westus' // only westus is supported in US for now
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: '17'
    storage: {
      storageSizeGB: 32
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    maintenanceWindow: {
      customWindow: 'Enabled'
      dayOfWeek: 0
      startHour: 2
      startMinute: 0
    }
  }
}

// Database for the POC
resource customerDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgresqlServer
  name: 'customer_matching'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// PostgreSQL Configuration for pgvector
// NOTE: The pgvector extension should be enabled after deployment using Azure CLI:
// az postgres flexible-server execute --name <server-name> --admin-password <password> --admin-user <admin-username> \
//   --database-name customer_matching --file-path ./enable-pgvector.sql
// Where enable-pgvector.sql contains: CREATE EXTENSION IF NOT EXISTS vector;

// Firewall rule for client access
resource postgresqlFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgresqlServer
  name: 'AllowClientIP'
  properties: {
    startIpAddress: clientIpAddress
    endIpAddress: clientIpAddress
  }
}

// Firewall rule for Azure services
resource postgresqlFirewallRuleAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgresqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}



// Azure OpenAI Service
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: openAiAccountName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiAccountName
    publicNetworkAccess: 'Enabled'
  }
}

// OpenAI Deployment for text-embedding-ada-002
resource openAiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAiAccount
  name: 'text-embedding-ada-002'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: 120
  }
}

// Store secrets in Key Vault
resource postgresqlConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgresql-connection-string'
  properties: {
    value: 'Host=${postgresqlServer.properties.fullyQualifiedDomainName};Database=customer_matching;Username=${adminUsername};Password=${adminPassword};SSL Mode=Require;'
  }
}

resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openAiAccount.listKeys().key1
  }
}

resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-endpoint'
  properties: {
    value: openAiAccount.properties.endpoint
  }
}

// Outputs
output postgresqlServerName string = postgresqlServer.name
output postgresqlFQDN string = postgresqlServer.properties.fullyQualifiedDomainName
output keyVaultName string = keyVault.name
output openAiEndpoint string = openAiAccount.properties.endpoint
