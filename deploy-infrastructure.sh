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

# Get admin password from parameters file or prompt for it
if [ -f "$PARAMS_FILE" ]; then
    # Try to extract password from parameters file using grep/awk
    # Look for adminPassword in the parameters file
    PASSWORD_LINE=$(grep -A 2 '"adminPassword"' "$PARAMS_FILE" | grep 'value')
    
    if [ -n "$PASSWORD_LINE" ]; then
        # Extract password value using sed
        # This handles passwords with special characters better than awk
        ADMIN_PASSWORD=$(echo "$PASSWORD_LINE" | sed -E 's/.*"value"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')
        
        if [ -n "$ADMIN_PASSWORD" ]; then
            echo -e "${GREEN}✅ Using admin password from parameters file${NC}"
        else
            echo -e "${YELLOW}⚠️ Could not parse admin password from parameters file${NC}"
            read -s -p "Enter PostgreSQL admin password: " ADMIN_PASSWORD
            echo ""
            
            if [ -z "$ADMIN_PASSWORD" ]; then
                echo -e "${RED}❌ Password cannot be empty${NC}"
                exit 1
            fi
        fi
    else
        # Prompt for password if not found in parameters file
        echo -e "${YELLOW}⚠️ Admin password not found in parameters file${NC}"
        read -s -p "Enter PostgreSQL admin password: " ADMIN_PASSWORD
        echo ""
        
        if [ -z "$ADMIN_PASSWORD" ]; then
            echo -e "${RED}❌ Password cannot be empty${NC}"
            exit 1
        fi
    fi
else
    # Prompt for password if parameters file doesn't exist
    echo -e "${YELLOW}⚠️ Parameters file not found, please enter admin password manually${NC}"
    read -s -p "Enter PostgreSQL admin password: " ADMIN_PASSWORD
    echo ""
    
    if [ -z "$ADMIN_PASSWORD" ]; then
        echo -e "${RED}❌ Password cannot be empty${NC}"
        exit 1
    fi
fi

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
VALIDATION_LOG="${DEPLOYMENT_NAME}-validation.log"
echo -e "${YELLOW}🔍 Validating template (output in $VALIDATION_LOG)...${NC}"

# Run validation and capture output
if ! az deployment group validate \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME-validate" \
    --template-file bicep/postgresql-pgvector.bicep \
    --parameters "@$PARAMS_FILE" \
    --output json > "$VALIDATION_LOG" 2>&1; then
    
    echo -e "${RED}❌ Template validation failed${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    
    # Try to extract and display error details
    if [ -f "$VALIDATION_LOG" ]; then
        if command -v jq &> /dev/null; then
            jq -r '.error.details[].message' "$VALIDATION_LOG" 2>/dev/null || cat "$VALIDATION_LOG"
        else
            cat "$VALIDATION_LOG"
        fi
    fi
    
    echo -e "\n${YELLOW}Full validation log: $VALIDATION_LOG${NC}"
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

# Get deployment details for output - using direct Azure CLI queries instead of jq
echo -e "${YELLOW}🔍 Getting deployment outputs...${NC}"

# Extract outputs directly using Azure CLI queries
POSTGRESQL_SERVER_NAME=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs.postgresqlServerName.value" \
    --output tsv 2>/dev/null || echo "")

POSTGRESQL_FQDN=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs.postgresqlFQDN.value" \
    --output tsv 2>/dev/null || echo "")

KEY_VAULT_NAME=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs.keyVaultName.value" \
    --output tsv 2>/dev/null || echo "")

OPENAI_ENDPOINT=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$DEPLOYMENT_NAME" \
    --query "properties.outputs.openAiEndpoint.value" \
    --output tsv 2>/dev/null || echo "")

if [ -n "$POSTGRESQL_SERVER_NAME" ] && [ -n "$POSTGRESQL_FQDN" ]; then
    echo -e "${GREEN}✅ Infrastructure deployment completed successfully!${NC}"
    
    # Enable pgvector extension
    if [ -n "$POSTGRESQL_SERVER_NAME" ]; then
        echo -e "${YELLOW}🔧 Allowing vector extension in server parameters...${NC}"
        # First, allow the vector extension by updating server parameters
        if az postgres flexible-server parameter set \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --server-name "$POSTGRESQL_SERVER_NAME" \
            --name "azure.extensions" \
            --value "vector"; then
            echo -e "${GREEN}✅ Successfully allowed vector extension in server parameters${NC}"
            
            # Wait a bit for the parameter change to take effect
            echo -e "${YELLOW}⏳ Waiting for parameter changes to propagate (30 seconds)...${NC}"
            sleep 30
            
            echo -e "${YELLOW}🔧 Enabling pgvector extension...${NC}"
            if az postgres flexible-server execute \
                --name "$POSTGRESQL_SERVER_NAME" \
                --admin-password "$ADMIN_PASSWORD" \
                --admin-user "pgadmin" \
                --database-name "customer_matching" \
                --file-path "./enable-pgvector.sql"; then
                echo -e "${GREEN}✅ Successfully enabled pgvector extension${NC}"
            else
                echo -e "${YELLOW}⚠️ Failed to enable pgvector extension. You may need to enable it manually.${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ Failed to allow vector extension in server parameters. You may need to do this manually.${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Could not determine PostgreSQL server name. You may need to enable pgvector extension manually.${NC}"
    fi
    
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
