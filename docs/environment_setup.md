# Environment Setup Guide

This guide explains how to configure environment variables for the Customer Matching POC application.

## Environment Variables

The application uses environment variables for configuration. You can set these up in several ways:

### 1. Create a `.env` file

Create a `.env` file in the `app/` directory with the following variables:

```bash
# Environment Configuration for Customer Matching POC
# Copy this file to .env and fill in your actual values

# PostgreSQL Configuration
POSTGRES_HOST=your-postgresql-server.postgres.database.azure.com
POSTGRES_PORT=5432
POSTGRES_DB=customer_matching
POSTGRES_USER=pgadmin
POSTGRES_PASSWORD='your_secure_password'

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-account.openai.azure.com/
AZURE_OPENAI_API_KEY='your_openai_api_key'
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2023-12-01-preview

# Azure Key Vault (Optional - for production)
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
USE_KEY_VAULT=false

# Application Configuration
APP_NAME='Customer Matching POC'
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
```

### 2. Set Environment Variables Directly

You can also set environment variables directly in your shell:

```bash
# Windows PowerShell
$env:POSTGRES_HOST="your-postgresql-server.postgres.database.azure.com"
$env:POSTGRES_DB="customer_matching"
$env:POSTGRES_USER="pgadmin"
$env:POSTGRES_PASSWORD="your_secure_password"
$env:AZURE_OPENAI_ENDPOINT="https://your-openai-account.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY="your_openai_api_key"

# Windows Command Prompt
set POSTGRES_HOST=your-postgresql-server.postgres.database.azure.com
set POSTGRES_DB=customer_matching
set POSTGRES_USER=pgadmin
set POSTGRES_PASSWORD=your_secure_password
set AZURE_OPENAI_ENDPOINT=https://your-openai-account.openai.azure.com/
set AZURE_OPENAI_API_KEY=your_openai_api_key

# Linux/macOS
export POSTGRES_HOST=your-postgresql-server.postgres.database.azure.com
export POSTGRES_DB=customer_matching
export POSTGRES_USER=pgadmin
export POSTGRES_PASSWORD=your_secure_password
export AZURE_OPENAI_ENDPOINT=https://your-openai-account.openai.azure.com/
export AZURE_OPENAI_API_KEY=your_openai_api_key
```

### 3. Azure Key Vault Integration

If you're using Azure Key Vault for production environments, set the following variables:

```bash
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
USE_KEY_VAULT=true
```

The application will automatically fetch sensitive values like database passwords from Key Vault when `USE_KEY_VAULT=true`.

## Configuration Details

### PostgreSQL Configuration
- `POSTGRES_HOST`: Your PostgreSQL server hostname or IP address
- `POSTGRES_PORT`: Database port (default: 5432)
- `POSTGRES_DB`: Database name for customer matching data
- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password (use quotes for special characters)

### Azure OpenAI Configuration
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI service endpoint URL
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: The deployment name for text embeddings (default: text-embedding-ada-002)
- `AZURE_OPENAI_API_VERSION`: API version to use

### Similarity Thresholds
- `DEFAULT_SIMILARITY_THRESHOLD`: Default confidence threshold for matches (0.8)
- `HIGH_CONFIDENCE_THRESHOLD`: High confidence threshold for strong matches (0.9)
- `POTENTIAL_MATCH_THRESHOLD`: Lower threshold for potential matches (0.75)

### Application Configuration
- `APP_NAME`: Application name for logging and identification
- `APP_VERSION`: Application version
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `API_HOST`: API server host (0.0.0.0 for all interfaces)
- `API_PORT`: API server port

## Security Notes

- Never commit `.env` files to version control
- Use strong passwords for database connections
- Consider using Azure Key Vault for production environments
- The `.env` file is already in `.gitignore` to prevent accidental commits
- Use quotes around values containing special characters or spaces

## Validation

The application validates required environment variables on startup. If required variables are missing, you'll see clear error messages indicating what needs to be configured.

## Quick Setup

1. Copy `.env.example` to `.env` in the `app/` directory
2. Update the placeholder values with your actual configuration
3. Ensure all required variables are set before running the application 