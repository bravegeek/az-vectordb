#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Display usage information
usage() {
    echo "Usage: $0 <sql-file-path>"
    echo "Example: $0 ./01-setup-pgvector.sql"
    exit 1
}
# ./exec-sql-file.sh ./01-setup-pgvector.sql

# Check if a file path was provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No SQL file specified${NC}"
    usage
fi

SQL_FILE="$1"

# Check if the file exists
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}❌ Error: SQL file not found: $SQL_FILE${NC}"
    exit 1
fi

# Source the .env file to get environment variables
if [ -f ../app/.env ]; then
    set -a  # automatically export all variables
    source ../app/.env
    set +a
    echo -e "${GREEN}✅ Loaded environment variables from .env file${NC}"
else
    echo -e "${YELLOW}⚠️ .env file not found. Please create one with the required variables.${NC}"
    exit 1
fi

# Execute the SQL file
echo -e "${YELLOW}🔧 Executing SQL file: $SQL_FILE${NC}"

az postgres flexible-server execute \
    --name vectordb-dev-postgresql-orafk6 \
    --admin-user pgadmin \
    --admin-password "$POSTGRES_PASSWORD" \
    --database-name customer_matching \
    --file-path "$SQL_FILE"

# Check the exit status of the last command
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Successfully executed SQL file${NC}"
else
    echo -e "${RED}❌ Error executing SQL file${NC}"
    exit 1
fi