#!/bin/bash
# Azure Infrastructure Deployment Script for PostgreSQL with pgvector POC
# Run this script to deploy the complete infrastructure

set -e

# Configuration
RESOURCE_GROUP_NAME="rg-vectordb-poc"
DEPLOYMENT_NAME="vectordb-deployment-$(date +%Y%m%d-%H%M%S)"

# Read location from parameters file
PARAMS_FILE="bicep/postgresql-pgvector.parameters.json"
if [ -f "$PARAMS_FILE" ]; then
    # Try to use jq if available
    if command -v jq &> /dev/null; then
        LOCATION=$(jq -r '.parameters.location.value' "$PARAMS_FILE")
    else
        # Fallback to grep/awk if jq is not available
        LOCATION=$(grep -A 2 '"location"' "$PARAMS_FILE" | grep 'value' | awk -F'"' '{print $4}')
    fi
    
    if [ -z "$LOCATION" ]; then
        echo -e "${YELLOW}⚠️  Could not determine location from parameters file, using default 'eastus'${NC}"
        LOCATION="eastus"
    fi
else
    echo -e "${YELLOW}⚠️  Parameters file not found: $PARAMS_FILE, using default location 'eastus'${NC}"
    LOCATION="eastus"
fi

echo -e "${GREEN}🌍 Using location: $LOCATION${NC}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Azure Infrastructure Deployment${NC}"
echo "Resource Group: $RESOURCE_GROUP_NAME"
echo "Location: $LOCATION"
echo "Deployment: $DEPLOYMENT_NAME"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please login first.${NC}"
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}✅ Using subscription: $SUBSCRIPTION_ID${NC}"

# Get client IP address
echo "Getting your public IP address..."
CLIENT_IP=$(curl -s https://api.ipify.org)
echo -e "${GREEN}✅ Detected IP address: $CLIENT_IP${NC}"

# Confirm deployment
echo ""
echo -e "${YELLOW}🔍 Deployment Summary:${NC}"
echo "  Resource Group: $RESOURCE_GROUP_NAME"
echo "  Client IP: $CLIENT_IP"
echo ""

read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  Deployment cancelled.${NC}"
    exit 0
fi

# Create resource group
echo ""
echo -e "${GREEN}📦 Creating resource group...${NC}"
az group create \
    --name $RESOURCE_GROUP_NAME \
    --location $LOCATION \
    --output table

# Deploy infrastructure
echo ""
echo -e "${GREEN}🏗️  Deploying infrastructure...${NC}"
echo "This may take 10-15 minutes..."

# Deploy infrastructure and capture output
echo -e "${YELLOW}🚀 Starting Bicep deployment...${NC}"

# First, validate the deployment
if ! az deployment group validate \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME-validate" \
    --template-file bicep/postgresql-pgvector.bicep \
    --parameters "@$PARAMS_FILE" \
    --output none; then
    echo -e "${RED}❌ Template validation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Template validation passed${NC}"

# If validation passes, proceed with the actual deployment
if ! az deployment group create \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --template-file bicep/postgresql-pgvector.bicep \
    --parameters "@$PARAMS_FILE" \
    --output none; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Get deployment details for output
DEPLOYMENT_OUTPUT=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs" \
    --output json 2>/dev/null || echo "{}")

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Infrastructure deployment completed successfully!${NC}"
    
    # Extract outputs
    POSTGRESQL_FQDN=$(echo $DEPLOYMENT_OUTPUT | jq -r '.properties.outputs.postgresqlFQDN.value')
    KEY_VAULT_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.properties.outputs.keyVaultName.value')
    OPENAI_ENDPOINT=$(echo $DEPLOYMENT_OUTPUT | jq -r '.properties.outputs.openAiEndpoint.value')
    
    echo ""
    echo -e "${GREEN}📋 Deployment Details:${NC}"
    echo "  PostgreSQL Server: $POSTGRESQL_FQDN"
    echo "  Key Vault: $KEY_VAULT_NAME"
    echo "  OpenAI Endpoint: $OPENAI_ENDPOINT"
    
    # Create .env file for the application
    echo ""
    echo -e "${GREEN}📝 Creating application configuration...${NC}"
    
    cat > app/.env << EOF
# PostgreSQL Configuration
POSTGRES_HOST=$POSTGRESQL_FQDN
POSTGRES_PORT=5432
POSTGRES_DB=customer_matching
POSTGRES_USER=pgadmin
POSTGRES_PASSWORD=$ADMIN_PASSWORD

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=your_openai_api_key_from_azure_portal
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2023-12-01-preview

# Azure Key Vault
AZURE_KEY_VAULT_URL=https://$KEY_VAULT_NAME.vault.azure.net/
USE_KEY_VAULT=false

# Application Configuration
APP_NAME=Customer Matching POC
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# Similarity Thresholds
DEFAULT_SIMILARITY_THRESHOLD=0.8
HIGH_CONFIDENCE_THRESHOLD=0.9
POTENTIAL_MATCH_THRESHOLD=0.75

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
EOF

    echo -e "${GREEN}✅ Created app/.env file${NC}"
    
    # Restore original parameters file
    mv "${PARAMS_FILE}.backup" "$PARAMS_FILE"
    
    echo ""
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "1. Get the OpenAI API key from Azure Portal and update app/.env"
    echo "2. Run the database setup script:"
    echo "   psql -h $POSTGRESQL_FQDN -U pgadmin -d customer_matching -f sql/01-setup-pgvector.sql"
    echo "3. Install Python dependencies:"
    echo "   cd app && pip install -r requirements.txt"
    echo "4. Start the application:"
    echo "   cd app && python main.py"
    echo ""
    echo -e "${GREEN}🔗 Useful Links:${NC}"
    echo "  Azure Portal: https://portal.azure.com"
    echo "  Resource Group: https://portal.azure.com/#@/resource/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"
    
else
    echo -e "${RED}❌ Infrastructure deployment failed!${NC}"
    mv "${PARAMS_FILE}.backup" "$PARAMS_FILE"
    exit 1
fi
