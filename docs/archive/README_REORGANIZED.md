# Customer Matching POC - Reorganized

A FastAPI-based customer matching application using PostgreSQL with pgvector for vector similarity search. This project has been reorganized following Python best practices for better maintainability, scalability, and development experience.

## 🏗️ Project Structure

```
az-vectordb/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── v1/                  # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── api.py           # Main API router
│   │   │   └── endpoints/       # API endpoints
│   │   │       ├── __init__.py
│   │   │       ├── customers.py # Customer endpoints
│   │   │       ├── health.py    # Health check endpoints
│   │   │       └── matching.py  # Matching endpoints
│   ├── core/                    # Core application components
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   └── database.py          # Database connection and session management
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy database models
│   │   └── schemas.py           # Pydantic API schemas
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── embedding_service.py # Azure OpenAI embedding service
│   │   └── matching/           # Modular customer matching services
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       └── helpers.py           # Common helper functions
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_api.py              # API tests
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── scripts/                     # Utility scripts
│   ├── generate_customer_data.py
│   └── import_customers.py
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Modern Python packaging configuration
└── README_REORGANIZED.md       # This file
```

## 🚀 Key Improvements

### 1. **Separation of Concerns**
- **API Layer**: Clean separation of endpoints by functionality
- **Business Logic**: Services handle complex business operations
- **Data Models**: Separate database models from API schemas
- **Configuration**: Centralized configuration management

### 2. **Modern Python Practices**
- **Type Hints**: Comprehensive type annotations throughout
- **Async Support**: Proper async/await patterns
- **Error Handling**: Consistent error handling and logging
- **Validation**: Pydantic models for request/response validation

### 3. **Testing Infrastructure**
- **Pytest**: Modern testing framework with fixtures
- **Test Coverage**: Comprehensive test coverage configuration
- **Mocking**: Proper mocking for external dependencies
- **Integration Tests**: Separate integration test suite

### 4. **Development Tools**
- **Code Quality**: Black, flake8, mypy, isort, bandit
- **Pre-commit**: Automated code quality checks
- **Documentation**: MkDocs for documentation generation
- **Profiling**: Performance profiling tools

### 5. **Package Management**
- **pyproject.toml**: Modern Python packaging
- **Dependency Management**: Separate production and development dependencies
- **Version Management**: Proper version constraints

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL with pgvector extension
- Azure OpenAI service

### 1. Clone and Setup
```bash
git clone <repository-url>
cd az-vectordb
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
# For production
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
# or
pip install -e ".[dev]"
```

### 3. Environment Configuration
Create a `.env` file:
```env
# Database
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=vectordb

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=text-embedding-ada-002
```

### 4. Database Setup
```bash
# Run SQL setup scripts
psql -h your-host -U your-user -d vectordb -f sql/01-setup-pgvector.sql
psql -h your-host -U your-user -d vectordb -f sql/02-functions.sql
```

## 🏃‍♂️ Running the Application

### Development Mode
```bash
# Using the new organized structure
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# API tests only
pytest tests/test_api.py
```