"""Pytest configuration and fixtures for Customer Matching POC - PostgreSQL only"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.models.database import Base
from app.core.config import settings

# Use main database URL from settings for testing
TEST_DATABASE_URL = settings.database_url

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    
    # Ensure tables exist (but don't drop them)
    Base.metadata.create_all(bind=engine)
    
    yield engine


@pytest.fixture
def db_session(db_engine):
    """Create test database session with transaction rollback"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback transaction to undo all changes
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