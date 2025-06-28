# Migration Guide: Old Structure to New Organized Structure

This guide helps you transition from the old flat project structure to the new organized structure while maintaining full functionality.

## 🔄 What Changed

### File Structure Changes

| Old Location | New Location | Purpose |
|--------------|--------------|---------|
| `app/main.py` | `app/main_new.py` | Main application entry point |
| `app/config.py` | `app/core/config.py` | Configuration management |
| `app/database.py` | `app/core/database.py` | Database connection management |
| `app/models.py` | `app/models/database.py` + `app/models/schemas.py` | Split into DB models and API schemas |
| `app/embedding_service.py` | `app/services/embedding_service.py` | Business logic service |
| `app/matching_service.py` | `app/services/matching_service.py` | Business logic service |
| `app/import/` | `scripts/` | Utility scripts moved |

### API Endpoint Changes

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| `/health` | `/api/v1/health/` | Added API versioning |
| `/customers` | `/api/v1/customers/` | Added API versioning |
| `/customers/incoming` | `/api/v1/customers/incoming` | Added API versioning |
| `/customers/match/{id}` | `/api/v1/matching/{id}` | Reorganized matching endpoints |
| `/customers/search` | `/api/v1/customers/search` | Added API versioning |
| `/matches/{id}` | `/api/v1/matching/results/{id}` | Reorganized matching endpoints |

## 🚀 Quick Migration Steps

### 1. Update Your Environment

The old `main.py` is still available, so you can run both versions during transition:

```bash
# Old way (still works)
python -m app.main

# New way (recommended)
python -m app.main_new
```

### 2. Update API Calls

If you have scripts or applications calling the API, update the endpoints:

```python
# Old way
response = requests.get("http://localhost:8000/health")

# New way
response = requests.get("http://localhost:8000/api/v1/health/")
```

### 3. Update Import Statements

If you have custom scripts importing from the old structure:

```python
# Old imports
from app.config import settings
from app.models import Customer
from app.embedding_service import embedding_service

# New imports
from app.core.config import settings
from app.models.database import Customer
from app.services.embedding_service import embedding_service
```

## 📋 Detailed Migration Checklist

### ✅ Environment Setup
- [ ] Install new development dependencies: `pip install -r requirements-dev.txt`
- [ ] Verify `.env` file configuration is still valid
- [ ] Test database connection with new structure

### ✅ Application Testing
- [ ] Test old `main.py` still works: `python -m app.main`
- [ ] Test new `main_new.py`: `python -m app.main_new`
- [ ] Verify all endpoints return expected responses
- [ ] Check API documentation at `/docs` and `/redoc`

### ✅ API Integration Updates
- [ ] Update any external API calls to use new endpoints
- [ ] Test customer creation endpoints
- [ ] Test matching functionality
- [ ] Test search functionality
- [ ] Verify health check endpoints

### ✅ Script Updates
- [ ] Update `scripts/generate_customer_data.py` imports
- [ ] Update `scripts/import_customers.py` imports
- [ ] Test data generation scripts
- [ ] Test data import scripts

### ✅ Development Workflow
- [ ] Install pre-commit hooks: `pre-commit install`
- [ ] Run code formatting: `black app/ tests/`
- [ ] Run linting: `flake8 app/ tests/`
- [ ] Run type checking: `mypy app/`
- [ ] Run tests: `pytest`

## 🔧 Configuration Changes

### Environment Variables
No changes required - all existing environment variables work with the new structure.

### Database Configuration
No changes required - database connection and schema remain the same.

### Azure OpenAI Configuration
No changes required - all Azure OpenAI settings work with the new structure.

## 🧪 Testing the Migration

### 1. Health Check
```bash
# Test old endpoint
curl http://localhost:8000/health

# Test new endpoint
curl http://localhost:8000/api/v1/health/
```

### 2. Customer Creation
```bash
# Test new customer endpoint
curl -X POST http://localhost:8000/api/v1/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "contact_name": "John Doe",
    "email": "john@testcompany.com"
  }'
```

### 3. Customer Search
```bash
# Test search endpoint
curl -X POST http://localhost:8000/api/v1/customers/search \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "technology company",
    "similarity_threshold": 0.8,
    "max_results": 10
  }'
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` when importing from new structure
**Solution**: Update import statements to use new package structure

#### 2. API 404 Errors
**Problem**: API endpoints returning 404
**Solution**: Update endpoint URLs to include `/api/v1/` prefix

#### 3. Database Connection Issues
**Problem**: Database connection failing with new structure
**Solution**: Verify `.env` file and database credentials

#### 4. Test Failures
**Problem**: Tests failing after migration
**Solution**: Update test imports and endpoint URLs

### Getting Help

1. Check the logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test with the old structure first to isolate issues
4. Review the new project structure documentation

## 📈 Benefits After Migration

### 1. **Better Code Organization**
- Clear separation of concerns
- Easier to find and modify code
- Better maintainability

### 2. **Improved Development Experience**
- Modern development tools
- Automated code quality checks
- Better testing infrastructure

### 3. **Enhanced Scalability**
- Modular architecture
- API versioning support
- Service layer abstraction

### 4. **Production Readiness**
- Comprehensive error handling
- Better logging
- Health checks and monitoring

## 🔄 Rollback Plan

If you need to rollback to the old structure:

1. **Keep the old `main.py`** - it's still functional
2. **Use old endpoints** - they still work
3. **Revert import changes** in your scripts
4. **Switch back to old entry point**: `python -m app.main`

## 📞 Support

If you encounter issues during migration:

1. Check this migration guide
2. Review the new README_REORGANIZED.md
3. Test with the old structure to isolate issues
4. Create an issue with detailed error information

---

**Note**: The migration is designed to be non-breaking. You can run both the old and new structures simultaneously during the transition period. 