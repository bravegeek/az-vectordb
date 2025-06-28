"""API tests for Customer Matching POC"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "database_connected" in data
    assert "openai_connected" in data


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns HTML"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Customer Matching POC" in response.text


def test_create_customer(client: TestClient, sample_customer_data):
    """Test creating a customer"""
    response = client.post("/api/v1/customers/", json=sample_customer_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["company_name"] == sample_customer_data["company_name"]
    assert data["contact_name"] == sample_customer_data["contact_name"]
    assert data["email"] == sample_customer_data["email"]
    assert "customer_id" in data


def test_list_customers(client: TestClient, sample_customer_data):
    """Test listing customers"""
    # First create a customer
    client.post("/api/v1/customers/", json=sample_customer_data)
    
    # Then list customers
    response = client.get("/api/v1/customers/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_incoming_customer(client: TestClient, sample_incoming_customer_data):
    """Test creating an incoming customer"""
    response = client.post("/api/v1/customers/incoming", json=sample_incoming_customer_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["company_name"] == sample_incoming_customer_data["company_name"]
    assert data["contact_name"] == sample_incoming_customer_data["contact_name"]
    assert data["email"] == sample_incoming_customer_data["email"]
    assert "request_id" in data
    assert data["processing_status"] == "pending"


def test_search_customers(client: TestClient, sample_customer_data):
    """Test searching customers"""
    # First create a customer
    client.post("/api/v1/customers/", json=sample_customer_data)
    
    # Then search
    search_data = {
        "query_text": "technology company",
        "similarity_threshold": 0.5,
        "max_results": 10
    }
    
    response = client.post("/api/v1/customers/search", json=search_data)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_invalid_customer_data(client: TestClient):
    """Test creating customer with invalid data"""
    invalid_data = {
        "company_name": "",  # Empty company name
        "email": "invalid-email",  # Invalid email
        "annual_revenue": -1000  # Negative revenue
    }
    
    response = client.post("/api/v1/customers/", json=invalid_data)
    # Should return 422 for validation error or 500 for server error
    assert response.status_code in [422, 500] 