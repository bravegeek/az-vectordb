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
│   │   └── matching_service.py  # Customer matching service
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

## 🔧 Development Tools

### Code Formatting
```bash
# Format code with Black
black app/ tests/

# Sort imports with isort
isort app/ tests/

# Type checking with mypy
mypy app/
```

### Linting
```bash
# Run flake8
flake8 app/ tests/

# Run bandit for security
bandit -r app/
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

## 📚 API Documentation

Once the application is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 🔄 Migration from Old Structure

The old `main.py` file is still available for reference. To migrate:

1. **Update imports** in any custom scripts
2. **Use new endpoints** with `/api/v1/` prefix
3. **Update configuration** to use new settings structure

### Endpoint Changes
- Old: `/customers` → New: `/api/v1/customers/`
- Old: `/health` → New: `/api/v1/health/`
- Old: `/customers/match/{id}` → New: `/api/v1/matching/{id}`

## 🏗️ Architecture Benefits

### 1. **Scalability**
- Modular design allows easy addition of new features
- Service layer can be easily extended or replaced
- API versioning support for future changes

### 2. **Maintainability**
- Clear separation of concerns
- Consistent coding patterns
- Comprehensive testing coverage
- Automated code quality checks

### 3. **Developer Experience**
- Modern development tools
- Clear project structure
- Comprehensive documentation
- Easy testing and debugging

### 4. **Production Readiness**
- Proper error handling
- Logging configuration
- Health checks
- Performance monitoring support

## 🤝 Contributing

1. Follow the established project structure
2. Add tests for new features
3. Run code quality checks before committing
4. Update documentation as needed
5. Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information
4. Contact the development team

---

**Note**: This reorganization maintains full backward compatibility while providing a much more maintainable and scalable codebase structure. 