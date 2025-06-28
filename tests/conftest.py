"""Pytest configuration and fixtures for Customer Matching POC"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, Column, Integer, String, Text, DECIMAL, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from app.main_new import app
from app.core.database import get_db

# Check if we should use SQLite for testing
USE_SQLITE = os.getenv("USE_SQLITE_FOR_TESTS", "false").lower() == "true"

if USE_SQLITE:
    # SQLite test configuration
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    
    # Create simplified models for SQLite testing
    TestBase = declarative_base()
    
    class TestCustomer(TestBase):
        """Simplified Customer model for SQLite testing"""
        __tablename__ = "customers"
        
        customer_id = Column(Integer, primary_key=True, index=True)
        company_name = Column(String(255), nullable=False, index=True)
        contact_name = Column(String(255))
        email = Column(String(255), index=True)
        phone = Column(String(50), index=True)
        address_line1 = Column(String(255))
        address_line2 = Column(String(255))
        city = Column(String(100))
        state_province = Column(String(100))
        postal_code = Column(String(20))
        country = Column(String(100))
        industry = Column(String(100))
        annual_revenue = Column(DECIMAL(15, 2))
        employee_count = Column(Integer)
        website = Column(String(255))
        description = Column(Text)
        created_date = Column(DateTime, default=func.now())
        updated_date = Column(DateTime, default=func.now(), onupdate=func.now())
        
        # Simplified embeddings as JSON strings for SQLite
        company_name_embedding = Column(String)  # Store as JSON string
        full_profile_embedding = Column(String)  # Store as JSON string
    
    class TestIncomingCustomer(TestBase):
        """Simplified IncomingCustomer model for SQLite testing"""
        __tablename__ = "incoming_customers"
        
        request_id = Column(Integer, primary_key=True, index=True)
        company_name = Column(String(255), nullable=False)
        contact_name = Column(String(255))
        email = Column(String(255))
        phone = Column(String(50))
        address_line1 = Column(String(255))
        address_line2 = Column(String(255))
        city = Column(String(100))
        state_province = Column(String(100))
        postal_code = Column(String(20))
        country = Column(String(100))
        industry = Column(String(100))
        annual_revenue = Column(DECIMAL(15, 2))
        employee_count = Column(Integer)
        website = Column(String(255))
        description = Column(Text)
        request_date = Column(DateTime, default=func.now())
        
        # Simplified embeddings as JSON strings for SQLite
        company_name_embedding = Column(String)  # Store as JSON string
        full_profile_embedding = Column(String)  # Store as JSON string
        
        # Processing status
        processing_status = Column(String(20), default="pending")
        processed_date = Column(DateTime)
    
    class TestMatchingResult(TestBase):
        """Simplified MatchingResult model for SQLite testing"""
        __tablename__ = "matching_results"
        
        match_id = Column(Integer, primary_key=True, index=True)
        incoming_customer_id = Column(Integer, ForeignKey("incoming_customers.request_id"))
        matched_customer_id = Column(Integer, ForeignKey("customers.customer_id"))
        similarity_score = Column(DECIMAL(5, 4))
        match_type = Column(String(50))
        match_criteria = Column(JSON)
        confidence_level = Column(DECIMAL(5, 4))
        created_date = Column(DateTime, default=func.now())
        reviewed = Column(Boolean, default=False)
        reviewer_notes = Column(Text)
    
    # Override the model imports for SQLite testing
    import app.models.database as db_module
    db_module.Customer = TestCustomer
    db_module.IncomingCustomer = TestIncomingCustomer
    db_module.MatchingResult = TestMatchingResult
    db_module.Base = TestBase
    
    # Create engine with SQLite configuration
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base = TestBase
    
else:
    # PostgreSQL test configuration
    TEST_DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/test_vectordb"
    )
    
    engine = create_engine(TEST_DATABASE_URL)
    
    # Import the original models for PostgreSQL
    from app.models.database import Base

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_schema():
    """Create the customer_data schema for testing (PostgreSQL only)"""
    if not USE_SQLITE:
        with engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS customer_data"))
            conn.commit()


def drop_test_schema():
    """Drop the test schema (PostgreSQL only)"""
    if not USE_SQLITE:
        with engine.connect() as conn:
            # Drop schema and all its objects
            conn.execute(text("DROP SCHEMA IF EXISTS customer_data CASCADE"))
            conn.commit()


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    # Override the application's database engine and session
    import app.core.database as db_module
    db_module.engine = engine
    db_module.SessionLocal = TestingSessionLocal
    
    # Override database initialization functions for SQLite
    if USE_SQLITE:
        def sqlite_check_pgvector_extension() -> bool:
            """SQLite-compatible pgvector check - always return True for testing"""
            return True
        
        def sqlite_initialize_database() -> bool:
            """SQLite-compatible database initialization"""
            try:
                # Create all tables
                Base.metadata.create_all(bind=engine)
                return True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error initializing SQLite database: {e}")
                return False
        
        # Override the functions
        db_module.check_pgvector_extension = sqlite_check_pgvector_extension
        db_module.initialize_database = sqlite_initialize_database
    
    if not USE_SQLITE:
        # Create schema first for PostgreSQL
        create_test_schema()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    if not USE_SQLITE:
        drop_test_schema()


@pytest.fixture
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with overridden database dependency"""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        "company_name": "Test Company Inc",
        "contact_name": "John Doe",
        "email": "john.doe@testcompany.com",
        "phone": "+1-555-123-4567",
        "address_line1": "123 Test Street",
        "city": "Test City",
        "state_province": "Test State",
        "postal_code": "12345",
        "country": "United States",
        "industry": "Technology",
        "annual_revenue": 1000000.0,
        "employee_count": 50,
        "website": "https://testcompany.com",
        "description": "A test company for unit testing"
    }


@pytest.fixture
def sample_incoming_customer_data():
    """Sample incoming customer data for testing"""
    return {
        "company_name": "Test Company LLC",
        "contact_name": "Jane Smith",
        "email": "jane.smith@testcompany.com",
        "phone": "+1-555-987-6543",
        "address_line1": "456 Test Avenue",
        "city": "Test City",
        "state_province": "Test State",
        "postal_code": "12345",
        "country": "United States",
        "industry": "Technology",
        "annual_revenue": 1500000.0,
        "employee_count": 75,
        "website": "https://testcompany.com",
        "description": "Another test company for unit testing"
    } 