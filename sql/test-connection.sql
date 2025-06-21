-- Simple test query to verify database connection
SELECT 
    'Connection successful' AS status,
    current_database() AS database_name,
    current_user AS database_user,
    version() AS postgres_version;
