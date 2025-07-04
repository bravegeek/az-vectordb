# Customer Matching Testing Plan

## Overview

This document outlines a comprehensive testing strategy for evaluating the three different matching approaches implemented in the Customer Matching POC:

1. **Exact Matching** - Direct field comparisons (company name, email, phone)
2. **Vector Matching** - Semantic similarity using embeddings
3. **Fuzzy Matching** - String similarity using sequence matching

## Test Data Strategy

### 1. Test Data Generation

#### A. Controlled Test Scenarios
Use the existing `generate_incoming_customers.py` script to create test data with known variations:

```bash
# Generate test data with different variation intensities
python scripts/generate_incoming_customers.py --count 50 --variation-intensity low
python scripts/generate_incoming_customers.py --count 50 --variation-intensity medium  
python scripts/generate_incoming_customers.py --count 50 --variation-intensity high
```

#### B. Manual Test Cases
Create specific test cases for each matching approach:

**Exact Match Test Cases:**
- Perfect company name match
- Perfect email match
- Perfect phone match
- Multiple field matches
- Case sensitivity variations

**Vector Match Test Cases:**
- Semantic variations (e.g., "Microsoft Corp" vs "Microsoft Corporation")
- Industry-specific terminology
- Abbreviated vs full company names
- Different contact names but same company

**Fuzzy Match Test Cases:**
- Typographical errors
- Abbreviations (Inc. vs Incorporated)
- Word order changes
- Extra/missing words

### 2. Test Data Categories

| Category | Description | Expected Match Type | Count |
|----------|-------------|-------------------|-------|
| **Exact Matches** | Perfect field matches | Exact | 20 |
| **High Similarity** | Minor variations | High Confidence | 30 |
| **Medium Similarity** | Moderate variations | Potential | 30 |
| **Low Similarity** | Significant variations | Low Confidence | 20 |
| **No Match** | Completely different | No Match | 20 |

## Testing Framework

### 1. Individual Approach Testing

#### A. Exact Matching Tests

**Test Script:** `tests/test_exact_matching.py`

```python
def test_exact_company_name_match():
    """Test exact company name matching"""
    
def test_exact_email_match():
    """Test exact email matching"""
    
def test_exact_phone_match():
    """Test exact phone matching"""
    
def test_multiple_field_match():
    """Test when multiple fields match exactly"""
    
def test_case_sensitivity():
    """Test case sensitivity handling"""
```

**Test Cases:**
- Company name: "Microsoft Corporation" vs "Microsoft Corporation"
- Email: "john.doe@microsoft.com" vs "john.doe@microsoft.com"
- Phone: "+1-555-123-4567" vs "+1-555-123-4567"
- Multiple fields: Company + Email match

#### B. Vector Matching Tests

**Test Script:** `tests/test_vector_matching.py`

```python
def test_semantic_similarity():
    """Test semantic similarity matching"""
    
def test_industry_terminology():
    """Test industry-specific terminology matching"""
    
def test_abbreviation_handling():
    """Test abbreviation vs full name matching"""
    
def test_threshold_variations():
    """Test different similarity thresholds"""
```

**Test Cases:**
- "Microsoft Corp" vs "Microsoft Corporation"
- "Tech Solutions Inc" vs "Technology Solutions Incorporated"
- "Global Consulting Group" vs "International Consulting Services"

#### C. Fuzzy Matching Tests

**Test Script:** `tests/test_fuzzy_matching.py`

```python
def test_typo_handling():
    """Test typographical error handling"""
    
def test_abbreviation_matching():
    """Test abbreviation matching"""
    
def test_word_order():
    """Test word order variations"""
    
def test_threshold_sensitivity():
    """Test fuzzy threshold sensitivity"""
```

**Test Cases:**
- "Microsft" vs "Microsoft" (typo)
- "Microsoft Inc" vs "Microsoft Incorporated"
- "Global Tech Solutions" vs "Tech Solutions Global"

### 2. Hybrid Approach Testing

#### A. Combined Strategy Tests

**Test Script:** `tests/test_hybrid_matching.py`

```python
def test_hybrid_priority_order():
    """Test that exact matches take priority over vector matches"""
    
def test_duplicate_elimination():
    """Test duplicate removal across different approaches"""
    
def test_confidence_scoring():
    """Test confidence level calculations"""
    
def test_business_rules_application():
    """Test business rules impact on confidence"""
```

### 3. Performance Testing

#### A. Response Time Tests

**Test Script:** `tests/test_performance.py`

```python
def test_single_request_performance():
    """Test single request response time"""
    
def test_batch_request_performance():
    """Test batch processing performance"""
    
def test_concurrent_request_performance():
    """Test concurrent request handling"""
    
def test_database_query_optimization():
    """Test database query performance"""
```

**Performance Benchmarks:**
- Single request: < 2 seconds
- Batch of 10 requests: < 10 seconds
- Concurrent requests: < 5 seconds per request

## Test Execution Plan

### Phase 1: Individual Approach Validation

#### Week 1: Exact Matching
1. **Setup Test Data**
   ```bash
   # Generate exact match test cases
   python scripts/generate_incoming_customers.py --count 20 --variation-intensity low
   ```

2. **Run Exact Match Tests**
   ```bash
   # Test exact matching only
   python -m pytest tests/test_exact_matching.py -v
   ```

3. **Validate Results**
   - Verify exact matches are found
   - Check confidence scores (should be 0.8-1.0)
   - Confirm match criteria are correct

#### Week 2: Vector Matching
1. **Setup Test Data**
   ```bash
   # Generate semantic variation test cases
   python scripts/generate_incoming_customers.py --count 30 --variation-intensity medium
   ```

2. **Run Vector Match Tests**
   ```bash
   # Test vector matching only
   python -m pytest tests/test_vector_matching.py -v
   ```

3. **Validate Results**
   - Verify semantic similarities are captured
   - Check embedding generation
   - Validate similarity thresholds

#### Week 3: Fuzzy Matching
1. **Setup Test Data**
   ```bash
   # Generate fuzzy match test cases
   python scripts/generate_incoming_customers.py --count 30 --variation-intensity high
   ```

2. **Run Fuzzy Match Tests**
   ```bash
   # Test fuzzy matching only
   python -m pytest tests/test_fuzzy_matching.py -v
   ```

3. **Validate Results**
   - Verify typo handling
   - Check abbreviation matching
   - Validate similarity calculations

### Phase 2: Hybrid Approach Testing

#### Week 4: Combined Strategy
1. **Setup Comprehensive Test Data**
   ```bash
   # Generate mixed test cases
   python scripts/generate_incoming_customers.py --count 100 --variation-intensity mixed
   ```

2. **Run Hybrid Tests**
   ```bash
   # Test hybrid matching
   python -m pytest tests/test_hybrid_matching.py -v
   ```

3. **Validate Results**
   - Verify priority ordering (exact > vector > fuzzy)
   - Check duplicate elimination
   - Validate confidence scoring

### Phase 3: Performance and Integration Testing

#### Week 5: Performance Testing
1. **Run Performance Tests**
   ```bash
   # Test performance benchmarks
   python -m pytest tests/test_performance.py -v
   ```

2. **Load Testing**
   ```bash
   # Run load tests
   python scripts/load_test.py --requests 100 --concurrent 10
   ```

#### Week 6: Integration Testing
1. **API Integration Tests**
   ```bash
   # Test API endpoints
   python -m pytest tests/integration/test_api.py -v
   ```

2. **End-to-End Testing**
   ```bash
   # Test complete workflow
   python scripts/e2e_test.py
   ```

## Test Data Management

### 1. Test Data Sources

#### A. Generated Test Data
- Use `generate_incoming_customers.py` for controlled variations
- Store test data in `data/test_cases/` directory
- Version control test data for reproducibility

#### B. Real-World Test Data
- Anonymized customer data (if available)
- Industry-specific test cases
- Edge cases from production

### 2. Test Data Validation

#### A. Data Quality Checks
```python
def validate_test_data():
    """Validate test data quality"""
    # Check for required fields
    # Verify data types
    # Ensure realistic variations
    # Validate embeddings generation
```

#### B. Baseline Establishment
- Establish baseline performance metrics
- Document expected match rates
- Set confidence score thresholds

## Metrics and Success Criteria

### 1. Accuracy Metrics

#### A. Precision and Recall
- **Precision**: Percentage of matches that are correct
- **Recall**: Percentage of correct matches found
- **F1-Score**: Harmonic mean of precision and recall

#### B. Match Type Distribution
- Exact matches: 15-25%
- High confidence: 30-40%
- Potential matches: 25-35%
- Low confidence: 10-20%

### 2. Performance Metrics

#### A. Response Time
- Single request: < 2 seconds
- Batch processing: < 10 seconds for 10 requests
- Concurrent requests: < 5 seconds per request

#### B. Throughput
- Requests per second: > 5
- Database queries: < 100ms average
- Embedding generation: < 1 second

### 3. Quality Metrics

#### A. Confidence Score Distribution
- High confidence (0.9-1.0): 30-40%
- Medium confidence (0.7-0.9): 40-50%
- Low confidence (0.5-0.7): 20-30%

#### B. False Positive Rate
- Target: < 5% false positives
- False negative rate: < 10%

## Test Reporting

### 1. Automated Reports

#### A. Test Execution Reports
```bash
# Generate test reports
python -m pytest --html=reports/test_report.html --self-contained-html
```

#### B. Performance Reports
```bash
# Generate performance reports
python scripts/generate_performance_report.py
```

### 2. Manual Analysis

#### A. Match Quality Review
- Sample review of matches by type
- Confidence score validation
- Business rule impact analysis

#### B. Edge Case Analysis
- Document unexpected matches
- Analyze false positives/negatives
- Identify improvement opportunities

## Continuous Testing

### 1. Automated Testing Pipeline

#### A. Pre-commit Tests
```bash
# Run quick tests before commit
python -m pytest tests/unit/ -v
```

#### B. CI/CD Pipeline
```yaml
# GitHub Actions workflow
- name: Run Tests
  run: |
    python -m pytest tests/ -v
    python scripts/generate_test_report.py
```

### 2. Regression Testing

#### A. Baseline Comparison
- Compare results against established baselines
- Track performance over time
- Alert on significant changes

#### B. A/B Testing
- Test new algorithms against current
- Measure improvement in accuracy
- Validate performance impact

## Troubleshooting Guide

### 1. Common Issues

#### A. No Matches Found
- Check embedding generation
- Verify similarity thresholds
- Review test data quality

#### B. Poor Performance
- Check database indexes
- Review query optimization
- Monitor resource usage

#### C. Inconsistent Results
- Check random seed settings
- Verify test data consistency
- Review algorithm parameters

### 2. Debug Tools

#### A. Logging
```python
# Enable debug logging
logging.getLogger('app.services.matching_service').setLevel(logging.DEBUG)
```

#### B. Query Analysis
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM customer_data.customers WHERE ...;
```

## Conclusion

This testing plan provides a comprehensive framework for validating the customer matching system. The phased approach ensures thorough testing of each component before moving to integration testing. Regular execution of these tests will help maintain system quality and identify areas for improvement.

### Next Steps

1. **Implement Test Scripts**: Create the test scripts outlined in this plan
2. **Generate Test Data**: Use the existing generator to create comprehensive test cases
3. **Establish Baselines**: Run initial tests to establish performance baselines
4. **Automate Testing**: Set up automated testing pipeline
5. **Monitor and Improve**: Continuously monitor results and improve algorithms 