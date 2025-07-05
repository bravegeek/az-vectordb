#!/usr/bin/env python3
"""Script to run database migrations for test results table"""
import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the test results table migration"""
    try:
        # Create database engine
        engine = create_engine(settings.database_url)
        
        # Read migration SQL file
        migration_file = Path(__file__).parent.parent / "sql" / "03-create-test-results-table.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        with engine.connect() as conn:
            logger.info("Executing test results table migration...")
            
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    logger.info(f"Executing: {statement[:50]}...")
                    conn.execute(text(statement))
            
            conn.commit()
            logger.info("✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 