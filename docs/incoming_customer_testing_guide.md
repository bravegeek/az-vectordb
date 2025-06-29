# Incoming Customer Testing Guide

## Overview

This guide provides comprehensive instructions for generating test incoming customer data with controlled variations to thoroughly test the customer matching algorithms. The system allows you to create realistic test scenarios by modifying existing customer records in predictable ways.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Data Generation Script](#test-data-generation-script)
3. [Variation Types and Examples](#variation-types-and-examples)
4. [Testing Strategies](#testing-strategies)
5. [API Testing Methods](#api-testing-methods)
6. [Database Integration](#database-integration)
7. [Monitoring and Validation](#monitoring-and-validation)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Existing customer data in the database
- Python environment with required dependencies
- Database connection configured

### Basic Usage

```bash
# Generate 5 incoming customers with medium variations
python scripts/generate_incoming_customers.py --count 5 --intensity medium

# Generate 10 customers with high variations and save to JSON for review
python scripts/generate_incoming_customers.py --count 10 --intensity high --output-json test_data.json

# Generate 3 customers with low variations (closer to original)
python scripts/generate_incoming_customers.py --count 3 --intensity low
```

### Command Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--count` | int | 10 | Number of incoming customers to generate |
| `--intensity` | str | medium | Variation intensity level (low/medium/high) |
| `--output-json` | str | None | Optional JSON output file for review |
| `--db-url` | str | settings | Database URL (defaults to settings) |

## Test Data Generation Script

### Script Location
`scripts/generate_incoming_customers.py`

### Key Features

- **Controlled Variation Types**: Company name suffixes, prefixes, typos, abbreviations
- **Realistic Data Modifications**: Address formatting, email domain changes, phone number variations
- **Configurable Intensity Levels**: Low, medium, high variation probabilities
- **Database Integration**: Direct saving with embeddings generation
- **Comprehensive Logging**: Full audit trail of generated data

### Class Structure

```python
class IncomingCustomerGenerator:
    """Expert class for generating incoming customer test data with controlled variations"""
    
    def __init__(self, db_url: str)
    def get_existing_customers(self, limit: int = 50) -> List[Customer]
    def create_company_name_variation(self, original_name: str, variation_type: str) -> str
    def create_address_variation(self, original_address: str, variation_type: str) -> str
    def create_email_variation(self, original_email: str, variation_type: str) -> str
    def create_phone_variation(self, original_phone: str, variation_type: str) -> str
    def generate_incoming_customer(self, base_customer: Customer, variation_intensity: str) -> Dict[str, Any]
    def create_incoming_customers(self, count: int, variation_intensity: str) -> List[Dict[str, Any]]
    def save_to_database(self, incoming_customers: List[Dict[str, Any]]) -> List[IncomingCustomer]
    def save_to_json(self, incoming_customers: List[Dict[str, Any]], output_path: str) -> bool
```

## Variation Types and Examples

### Company Name Variations

#### 1. Suffix Changes
```python
# Original → Modified
"Acme Corporation" → "Acme Corp Inc"
"Tech Solutions" → "Tech Solutions LLC"
"Global Industries" → "Global Industries & Associates"
```

#### 2. Prefix Addition
```python
# Original → Modified
"Acme Corp" → "Advanced Acme Corp"
"Tech Solutions" → "Global Tech Solutions"
"Data Systems" → "Innovative Data Systems"
```

#### 3. Typos
```python
# Original → Modified
"Acme Corporation" → "Acme C0rporation"  # 'o' → '0'
"Tech Solutions" → "Tech S0lutions"      # 'o' → '0'
"Data Systems" → "D@ta Systems"          # 'a' → '@'
```

#### 4. Abbreviations
```python
# Original → Modified
"Acme Corporation" → "A C"
"Tech Solutions Inc" → "T S I"
"Global Data Systems" → "G D S"
```

#### 5. Word Order Changes
```python
# Original → Modified
"Acme Corporation" → "Corporation Acme"
"Tech Solutions Inc" → "Solutions Tech Inc"
"Global Data Systems" → "Data Global Systems"
```

### Address Variations

#### 1. Street Suffix Abbreviations
```python
# Original → Modified
"123 Main Street" → "123 Main St"
"456 Oak Avenue" → "456 Oak Ave"
"789 Pine Boulevard" → "789 Pine Blvd"
```

#### 2. Number Formatting
```python
# Original → Modified
"123 Main Street" → "123rd Main Street"
"456 Oak Avenue" → "456th Oak Avenue"
"789 Pine Boulevard" → "789th Pine Boulevard"
```

### Email Variations

#### 1. Domain Changes
```python
# Original → Modified
"john@acme.com" → "john@acme.org"
"jane@tech.com" → "jane@tech.net"
"bob@company.com" → "bob@company.biz"
```

#### 2. Local Part Typos
```python
# Original → Modified
"john@acme.com" → "j0hn@acme.com"    # 'o' → '0'
"jane@tech.com" → "j@ne@tech.com"    # 'a' → '@'
"bob@company.com" → "b0b@company.com" # 'o' → '0'
```

#### 3. Underscore Addition
```python
# Original → Modified
"john@acme.com" → "john_a@acme.com"
"jane@tech.com" → "jane_b@tech.com"
"bob@company.com" → "bob_c@company.com"
```

### Phone Number Variations

#### 1. Format Changes
```python
# Original → Modified
"(555) 123-4567" → "555-123-4567"
"(555) 123-4567" → "555.123.4567"
"(555) 123-4567" → "+1-555-123-4567"
```

#### 2. Digit Typos
```python
# Original → Modified
"(555) 123-4567" → "(555) 123-4568"  # Last digit changed
"(555) 123-4567" → "(555) 124-4567"  # Middle digit changed
"(555) 123-4567" → "(556) 123-4567"  # Area code changed
```

## Testing Strategies

### Test Case Categories

#### 1. Exact Matches (Baseline)
- **Purpose**: Verify perfect match detection
- **Variation**: None (use original data)
- **Expected Result**: 100% confidence match

#### 2. Minor Variations
- **Purpose**: Test tolerance for small changes
- **Variations**: Company suffix changes, address abbreviations
- **Expected Result**: High confidence matches (80-95%)

#### 3. Moderate Variations
- **Purpose**: Test handling of common data entry errors
- **Variations**: Typos, domain changes, phone formatting
- **Expected Result**: Medium confidence matches (60-80%)

#### 4. Major Variations
- **Purpose**: Test algorithm robustness
- **Variations**: Word order changes, significant typos
- **Expected Result**: Low confidence matches (30-60%)

#### 5. Edge Cases
- **Purpose**: Test boundary conditions
- **Variations**: Missing data, partial matches, extreme typos
- **Expected Result**: Very low confidence or no matches

### Variation Intensity Levels

#### Low Intensity (30% variation probability)
- **Use Case**: Testing high-precision matching
- **Best For**: Validating exact and near-exact matches
- **Example**: "Acme Corp" → "Acme Corp Inc"

#### Medium Intensity (60% variation probability)
- **Use Case**: Testing balanced matching
- **Best For**: General testing and validation
- **Example**: "Acme Corp" → "Acme C0rp Inc"

#### High Intensity (80% variation probability)
- **Use Case**: Testing algorithm robustness
- **Best For**: Stress testing and edge case validation
- **Example**: "Acme Corp" → "C0rp Acme Inc"

## API Testing Methods

### 1. Direct API Testing

```python
import requests

# Create incoming customer via API
def create_test_customer_via_api(customer_data):
    response = requests.post(
        "http://localhost:8000/api/v1/customers/incoming",
        json=customer_data
    )
    return response.json()

# Example usage
test_customer = {
    "company_name": "Acme Corp Inc",  # Modified from "Acme Corp"
    "contact_name": "John Smith",
    "email": "john.smith@acme.com",
    "phone": "(555) 123-4567",
    "address_line1": "123 Main St",  # Modified from "123 Main Street"
    "city": "New York",
    "country": "USA"
}

result = create_test_customer_via_api(test_customer)
print(f"Created incoming customer with ID: {result['request_id']}")
```

### 2. Matching API Testing

```python
# Test matching with generated data
def test_matching(incoming_customer_id):
    response = requests.post(
        "http://localhost:8000/api/v1/matching/match",
        json={"incoming_customer_id": incoming_customer_id}
    )
    return response.json()

# Test similarity search
def test_similarity_search(query_text, threshold=0.8):
    response = requests.post(
        "http://localhost:8000/api/v1/customers/search",
        json={
            "query_text": query_text,
            "similarity_threshold": threshold,
            "max_results": 10
        }
    )
    return response.json()
```

## Database Integration

### 1. Direct Database Insertion

```python
from app.core.database import get_db
from app.models.database import IncomingCustomer
from app.services.embedding_service import embedding_service

def create_test_incoming_customer(base_customer_data, modifications):
    """Create incoming customer with specific modifications"""
    with get_db() as db:
        # Apply modifications
        test_data = base_customer_data.copy()
        test_data.update(modifications)
        
        # Generate embeddings
        company_embedding, profile_embedding = embedding_service.generate_customer_embeddings(test_data)
        
        # Create record
        incoming_customer = IncomingCustomer(
            **test_data,
            company_name_embedding=company_embedding,
            full_profile_embedding=profile_embedding
        )
        
        db.add(incoming_customer)
        db.commit()
        return incoming_customer

# Example usage
base_data = {
    "company_name": "Acme Corporation",
    "contact_name": "John Smith",
    "email": "john@acme.com"
}

modifications = {
    "company_name": "Acme Corp Inc",
    "email": "john@acme.org"
}

test_customer = create_test_incoming_customer(base_data, modifications)
```

### 2. Batch Processing

```python
def create_batch_test_customers(base_customers, modification_sets):
    """Create multiple test customers with different modification sets"""
    results = []
    
    for base_customer, modifications in zip(base_customers, modification_sets):
        test_customer = create_test_incoming_customer(base_customer, modifications)
        results.append(test_customer)
    
    return results
```

## Monitoring and Validation

### 1. Query Generated Test Data

```sql
-- Check generated test data
SELECT 
    ic.request_id,
    ic.company_name,
    ic.processing_status,
    ic.request_date,
    COUNT(mr.match_id) as match_count
FROM customer_data.incoming_customers ic
LEFT JOIN customer_data.matching_results mr ON ic.request_id = mr.incoming_customer_id
WHERE ic.request_date >= CURRENT_DATE
GROUP BY ic.request_id, ic.company_name, ic.processing_status, ic.request_date
ORDER BY ic.request_date DESC;
```

### 2. Match Quality Analysis

```sql
-- Analyze matching results
SELECT 
    ic.company_name as incoming_name,
    c.company_name as matched_name,
    mr.similarity_score,
    mr.confidence_level,
    mr.match_type,
    mr.created_date
FROM customer_data.incoming_customers ic
JOIN customer_data.matching_results mr ON ic.request_id = mr.incoming_customer_id
JOIN customer_data.customers c ON mr.matched_customer_id = c.customer_id
WHERE ic.request_date >= CURRENT_DATE
ORDER BY mr.similarity_score DESC;
```

### 3. Performance Monitoring

```sql
-- Monitor processing performance
SELECT 
    DATE(ic.request_date) as test_date,
    COUNT(*) as total_incoming,
    AVG(EXTRACT(EPOCH FROM (ic.processed_date - ic.request_date))) as avg_processing_time_seconds,
    COUNT(CASE WHEN ic.processing_status = 'completed' THEN 1 END) as completed_count
FROM customer_data.incoming_customers ic
WHERE ic.request_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(ic.request_date)
ORDER BY test_date DESC;
```

## Best Practices

### 1. Systematic Testing

- **Test each variation type independently**
- **Use consistent base data for comparison**
- **Document expected match confidence levels**
- **Test both positive and negative cases**

### 2. Performance Testing

- **Generate larger datasets (100+ records) for performance testing**
- **Monitor embedding generation time**
- **Test matching algorithm scalability**
- **Measure response times under load**

### 3. Quality Assurance

- **Validate generated data quality**
- **Check for realistic variations**
- **Ensure proper error handling**
- **Test edge cases and boundary conditions**

### 4. Data Management

- **Use separate test environments when possible**
- **Clean up test data regularly**
- **Backup production data before testing**
- **Document test scenarios and results**

### 5. Continuous Integration

- **Automate test data generation in CI/CD pipelines**
- **Include matching algorithm tests in automated testing**
- **Monitor test results over time**
- **Alert on significant performance regressions**

## Troubleshooting

### Common Issues

#### 1. No Existing Customers Found
```
Error: No existing customers found in database
```
**Solution**: Ensure you have customer data in the database before generating test data.

#### 2. Database Connection Issues
```
Error: Connection to database failed
```
**Solution**: Check database URL and connection settings in `app/core/config.py`.

#### 3. Embedding Generation Failures
```
Error: Failed to generate embeddings
```
**Solution**: Verify OpenAI API key and service configuration.

#### 4. Memory Issues with Large Datasets
```
Error: Memory allocation failed
```
**Solution**: Reduce batch size or process data in smaller chunks.

### Debugging Tips

1. **Enable verbose logging**:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check database state**:
   ```sql
   SELECT COUNT(*) FROM customer_data.customers;
   SELECT COUNT(*) FROM customer_data.incoming_customers;
   ```

3. **Validate embeddings**:
   ```python
   # Check if embeddings are generated correctly
   customer = db.query(IncomingCustomer).first()
   print(f"Company embedding shape: {len(customer.company_name_embedding)}")
   print(f"Profile embedding shape: {len(customer.full_profile_embedding)}")
   ```

4. **Test individual components**:
   ```python
   # Test embedding service directly
   from app.services.embedding_service import embedding_service
   test_text = "Acme Corporation"
   embedding = embedding_service.generate_text_embedding(test_text)
   print(f"Embedding generated: {len(embedding)} dimensions")
   ```

### Performance Optimization

1. **Batch processing**: Process multiple records in batches
2. **Connection pooling**: Use database connection pooling for better performance
3. **Async processing**: Consider async operations for large datasets
4. **Caching**: Cache frequently used embeddings

## Conclusion

This testing guide provides a comprehensive framework for generating and testing incoming customer data. By following these practices, you can ensure thorough testing of your customer matching algorithms across various scenarios and edge cases.

The automated script provides a robust, scalable solution for generating test data, while the manual methods offer flexibility for specific testing scenarios. Regular monitoring and validation ensure the quality and performance of your matching system.

For additional support or questions, refer to the main project documentation or contact the development team.
