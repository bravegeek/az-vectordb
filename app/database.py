"""Database connection and session management"""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from models import Base

logger = logging.getLogger(__name__)

# Synchronous database engine
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# Asynchronous database engine
async_engine = create_async_engine(
    settings.async_database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> Generator[AsyncSession, None, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        yield session


def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def check_pgvector_extension() -> bool:
    """Check if pgvector extension is installed"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking pgvector extension: {e}")
        return False


def initialize_database():
    """Initialize database with required extensions and schema"""
    try:
        with engine.connect() as conn:
            # Check if schema exists
            schema_check = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'customer_data'
            """))
            
            if not schema_check.fetchone():
                logger.info("Creating customer_data schema...")
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS customer_data"))
                conn.commit()
            
            # Check pgvector extension
            if not check_pgvector_extension():
                logger.warning("pgvector extension not found. Please install it manually.")
                return False
            
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
