# Vector Matching Testing Plan

## Overview

This document provides a comprehensive testing strategy specifically for the vector matching functionality in the Customer Matching POC. Vector matching uses semantic similarity with embeddings to find matches based on meaning rather than exact text matches, making it crucial for handling variations in company names, industry terminology, and business descriptions.

## Vector Matching Architecture

### Current Implementation
- **Service**: `VectorMatcher` class in `app/services/matching/vector_matcher.py`
- **Database**: PostgreSQL with pgvector extension for vector similarity queries
- **Embedding Model**: OpenAI text-embedding-ada-002 (1536 dimensions)
- **Similarity Metric**: Cosine distance using pgvector's `<=>` operator
- **Threshold**: Configurable via `settings.vector_similarity_threshold`

### Key Components
1. **Embedding Generation**: Full profile embeddings from customer data
2. **Vector Query**: PostgreSQL query with pgvector similarity search
3. **Match Type Determination**: Based on similarity score thresholds
4. **Business Rules**: Confidence adjustment based on business logic
5. **Result Processing**: Match result creation with metadata

## Test Categories

### 1. Semantic Similarity Tests

#### A. Company Name Variations
**Objective**: Test semantic understanding of company name variations

**Test Implementation**: Use `scripts/generate_semantic_test_data.py` to generate controlled semantic variations

**Test Cases**:
```python
test_cases = [
    # Abbreviations
    ("Microsoft Corp", "Microsoft Corporation"),
    ("IBM Inc", "International Business Machines Incorporated"),
    ("Apple Inc", "Apple Incorporated"),
    
    # Industry terminology
    ("Tech Solutions", "Technology Solutions"),
    ("Software Dev Corp", "Software Development Corporation"),
    ("Digital Marketing Agency", "Online Marketing Services"),
    
    # Word order variations
    ("Global Tech Solutions", "Tech Solutions Global"),
    ("Consulting Group International", "International Consulting Group"),
    
    # Common business suffixes
    ("Acme Solutions", "Acme Solutions LLC"),
    ("Innovation Labs", "Innovation Laboratories"),
]
```

**Automated Test Execution**:
```bash
# Generate semantic test data with different intensities
python scripts/generate_semantic_test_data.py --count-per-intensity 20

# Run comprehensive semantic similarity tests
python scripts/run_semantic_similarity_tests.py --count-per-intensity 20 --output-json semantic_test_results.json
```

**Expected Results**:
- High similarity scores (>0.8) for semantic variations
- Lower scores for completely different companies
- Consistent ranking of similar companies

#### B. Industry-Specific Terminology
**Objective**: Test understanding of industry-specific language

**Test Cases**:
```python
industry_cases = [
    # Technology
    ("Software Engineering", "Software Development"),
    ("Cloud Computing", "Cloud Services"),
    ("AI Solutions", "Artificial Intelligence Services"),
    
    # Healthcare
    ("Medical Devices", "Healthcare Equipment"),
    ("Pharmaceutical Research", "Drug Development"),
    ("Clinical Services", "Medical Services"),
    
    # Financial
    ("Investment Banking", "Financial Services"),
    ("Asset Management", "Wealth Management"),
    ("Insurance Solutions", "Risk Management"),
]
```

### 2. Embedding Quality Tests

#### A. Embedding Consistency
**Objective**: Ensure embeddings are generated consistently

**Test Scenarios**:
1. **Same Input, Same Output**: Verify identical text produces identical embeddings
2. **Case Sensitivity**: Test embedding consistency across case variations
3. **Whitespace Handling**: Test embedding consistency with extra whitespace
4. **Special Characters**: Test embedding handling of special characters

**Test Implementation**:
```python
def test_embedding_consistency():
    """Test that identical inputs produce identical embeddings"""
    text1 = "Microsoft Corporation"
    text2 = "Microsoft Corporation"
    
    embedding1 = generate_embedding(text1)
    embedding2 = generate_embedding(text2)
    
    # Should be identical
    assert embedding1 == embedding2
    
def test_case_insensitivity():
    """Test embedding consistency across case variations"""
    text1 = "Microsoft Corporation"
    text2 = "microsoft corporation"
    
    embedding1 = generate_embedding(text1)
    embedding2 = generate_embedding(text2)
    
    # Should be very similar (not necessarily identical due to tokenization)
    similarity = cosine_similarity(embedding1, embedding2)
    assert similarity > 0.95
```

#### B. Embedding Dimensions
**Objective**: Verify embedding vector properties

**Test Requirements**:
- Vector dimension: 1536 (OpenAI ada-002)
- Data type: float32 or float64
- Normalization: Vectors should be normalized
- Range: Values typically between -1 and 1

### 3. Threshold and Scoring Tests

#### A. Similarity Threshold Testing
**Objective**: Test different similarity thresholds and their impact

**Test Scenarios**:
```python
threshold_tests = [
    # High threshold (0.9) - Very strict matching
    {"threshold": 0.9, "expected_matches": "Few, high-quality matches"},
    
    # Medium threshold (0.7) - Balanced matching
    {"threshold": 0.7, "expected_matches": "Moderate number of matches"},
    
    # Low threshold (0.5) - Broad matching
    {"threshold": 0.5, "expected_matches": "Many matches, may include false positives"},
]
```

#### B. Score Distribution Analysis
**Objective**: Analyze similarity score distributions

**Metrics to Track**:
- Score distribution histogram
- Mean, median, standard deviation
- Outlier detection
- Score correlation with match quality

### 4. Performance Tests

#### A. Query Performance
**Objective**: Test vector query performance under different conditions

**Test Scenarios**:
1. **Small Dataset** (< 1,000 customers)
   - Expected response time: < 100ms
   - Memory usage: < 50MB

2. **Medium Dataset** (1,000 - 10,000 customers)
   - Expected response time: < 500ms
   - Memory usage: < 200MB

3. **Large Dataset** (> 10,000 customers)
   - Expected response time: < 2 seconds
   - Memory usage: < 500MB

#### B. Index Performance
**Objective**: Test pgvector index performance

**Test Implementation**:
```python
def test_vector_index_performance():
    """Test vector index query performance"""
    # Test with and without vector index
    # Measure query execution time
    # Verify index is being used (EXPLAIN ANALYZE)
    
def test_index_maintenance():
    """Test index maintenance operations"""
    # Test index creation time
    # Test index size
    # Test index rebuild performance
```

### 5. Edge Case Tests

#### A. Empty and Null Values
**Objective**: Test handling of missing or empty data

**Test Cases**:
```python
edge_cases = [
    # Empty company names
    {"company_name": "", "expected": "No matches or low confidence"},
    
    # Null embeddings
    {"embedding": None, "expected": "Graceful handling, no errors"},
    
    # Very short names
    {"company_name": "A", "expected": "Low similarity scores"},
    
    # Very long names
    {"company_name": "Very long company name with many words...", "expected": "Normal processing"},
]
```

#### B. Special Characters and Languages
**Objective**: Test handling of special characters and non-English text

**Test Cases**:
```python
special_cases = [
    # Special characters
    "Company & Associates, Inc.",
    "Tech-Solutions (International)",
    "Digital@Marketing",
    
    # Non-English text
    "Technologie Solutions GmbH",
    "Consultoría Internacional S.A.",
    "株式会社テクノロジー",
]
```

### 6. Integration Tests

#### A. Database Integration
**Objective**: Test vector matching with real database

**Test Setup**:
```python
@pytest.mark.integration
def test_vector_match_with_database():
    """Test vector matching with actual database"""
    # Setup test data in database
    # Execute vector matching
    # Verify results
    # Cleanup test data
```

#### B. API Integration
**Objective**: Test vector matching through API endpoints

**Test Endpoints**:
- `POST /api/v1/matching/match` - Single customer matching
- `POST /api/v1/matching/batch` - Batch customer matching

### 7. Business Logic Tests

#### A. Confidence Scoring
**Objective**: Test business rules impact on confidence scores

**Test Scenarios**:
```python
confidence_tests = [
    # High similarity, same industry
    {"similarity": 0.9, "industry_match": True, "expected_confidence": "High"},
    
    # High similarity, different industry
    {"similarity": 0.9, "industry_match": False, "expected_confidence": "Medium"},
    
    # Low similarity, same industry
    {"similarity": 0.6, "industry_match": True, "expected_confidence": "Low"},
]
```

#### B. Match Type Classification
**Objective**: Test match type determination logic

**Test Cases**:
```python
match_type_tests = [
    {"score": 0.95, "expected_type": "Exact Match"},
    {"score": 0.85, "expected_type": "High Confidence"},
    {"score": 0.75, "expected_type": "Potential Match"},
    {"score": 0.65, "expected_type": "Low Confidence"},
    {"score": 0.45, "expected_type": "No Match"},
]
```

## Testing Scripts

### 1. Semantic Test Data Generation
**Script**: `scripts/generate_semantic_test_data.py`

**Purpose**: Generate incoming customers with controlled semantic variations for testing vector matching

**Features**:
- **Intensity Levels**: Low, medium, and high variation intensities
- **Semantic Patterns**: Company suffixes, industry terms, abbreviations, synonyms
- **Industry-Specific**: Technology, healthcare, finance, manufacturing variations
- **Database Integration**: Automatically saves to `incoming_customers` table with embeddings

**Usage**:
```bash
# Generate 20 customers per intensity level
python scripts/generate_semantic_test_data.py --count-per-intensity 20

# Generate with custom count
python scripts/generate_semantic_test_data.py --count-per-intensity 50

# Save to JSON for review
python scripts/generate_semantic_test_data.py --count-per-intensity 20 --output-json test_data.json
```

### 2. Semantic Similarity Test Runner
**Script**: `scripts/run_semantic_similarity_tests.py`

**Purpose**: Run comprehensive semantic similarity tests and generate detailed analysis

**Features**:
- **Automated Testing**: Tests all generated incoming customers against existing customers
- **Performance Metrics**: Response time, similarity scores, confidence levels
- **Pattern Analysis**: Company name patterns, industry-specific variations
- **Detailed Reporting**: JSON output with comprehensive results and recommendations

**Usage**:
```bash
# Run tests with generated data
python scripts/run_semantic_similarity_tests.py --count-per-intensity 20

# Use existing data (skip generation)
python scripts/run_semantic_similarity_tests.py --skip-generation

# Custom output file
python scripts/run_semantic_similarity_tests.py --output-json my_test_results.json
```

**Output Analysis**:
```bash
# View overall summary
cat semantic_test_results.json | jq '.overall_summary'

# View intensity-specific results
cat semantic_test_results.json | jq '.intensity_results.low'
cat semantic_test_results.json | jq '.intensity_results.medium'
cat semantic_test_results.json | jq '.intensity_results.high'

# View recommendations
cat semantic_test_results.json | jq '.analysis.recommendations'
```

## Test Data Strategy

### 1. Synthetic Test Data
**Generation Script**: `scripts/generate_semantic_test_data.py`

**Data Categories**:
```python
test_data_categories = {
    "exact_variations": {
        "count": 50,
        "description": "Companies with exact name variations",
        "examples": ["Microsoft Corp", "Microsoft Corporation"]
    },
    "semantic_variations": {
        "count": 100,
        "description": "Companies with semantic name variations",
        "examples": ["Tech Solutions", "Technology Solutions"]
    },
    "industry_variations": {
        "count": 75,
        "description": "Companies with industry-specific variations",
        "examples": ["Software Dev", "Software Development"]
    },
    "negative_cases": {
        "count": 50,
        "description": "Companies that should not match",
        "examples": ["Microsoft", "Apple"]
    }
}
```

### 2. Real-World Test Data
**Sources**:
- Anonymized customer data (if available)
- Public company databases
- Industry-specific datasets

**Validation**:
- Data quality checks
- Embedding generation verification
- Similarity score validation

## Test Execution Plan

### Phase 1: Semantic Similarity Testing (Week 1)
**Focus**: Comprehensive semantic similarity testing with controlled variations

**Tasks**:
1. **Generate Semantic Test Data**
   ```bash
   # Generate 20 customers per intensity level (low, medium, high)
   python scripts/generate_semantic_test_data.py --count-per-intensity 20
   ```

2. **Run Semantic Similarity Tests**
   ```bash
   # Run comprehensive tests and generate detailed report
   python scripts/run_semantic_similarity_tests.py --count-per-intensity 20 --output-json semantic_test_results.json
   ```

3. **Analyze Results**
   ```bash
   # Review test results and analysis
   cat semantic_test_results.json | jq '.overall_summary'
   cat semantic_test_results.json | jq '.intensity_results'
   ```

### Phase 2: Unit Testing (Week 2)
**Focus**: Individual component testing

**Tasks**:
1. **Embedding Tests**
   ```bash
   python -m pytest tests/unit/test_vector_matching.py::TestVectorMatching::test_embedding_quality -v
   ```

2. **Similarity Tests**
   ```bash
   python -m pytest tests/unit/test_vector_matching.py::TestVectorMatching::test_semantic_similarity -v
   ```

3. **Threshold Tests**
   ```bash
   python -m pytest tests/unit/test_vector_matching.py::TestVectorMatching::test_threshold_variations -v
   ```

### Phase 2: Integration Testing (Week 2)
**Focus**: Database and API integration

**Tasks**:
1. **Database Integration**
   ```bash
   python -m pytest tests/unit/test_vector_matching.py::TestVectorMatching::test_vector_match_with_database -v
   ```

2. **API Integration**
   ```bash
   python -m pytest tests/integration/test_api.py -k "vector" -v
   ```

### Phase 3: Performance Testing (Week 3)
**Focus**: Performance and scalability

**Tasks**:
1. **Load Testing**
   ```bash
   python scripts/load_test_vector_matching.py --requests 1000 --concurrent 10
   ```

2. **Performance Benchmarking**
   ```bash
   python scripts/benchmark_vector_matching.py
   ```

### Phase 4: Edge Case Testing (Week 4)
**Focus**: Edge cases and error handling

**Tasks**:
1. **Edge Case Validation**
   ```bash
   python -m pytest tests/unit/test_vector_matching.py -k "edge" -v
   ```

2. **Error Handling**
   ```bash
   python -m pytest tests/unit/test_vector_matching.py -k "error" -v
   ```

## Success Criteria

### 1. Accuracy Metrics
- **Precision**: > 85% for high-confidence matches
- **Recall**: > 80% for semantic variations
- **F1-Score**: > 82% overall

### 2. Performance Metrics
- **Response Time**: < 2 seconds for single requests
- **Throughput**: > 10 requests/second
- **Memory Usage**: < 500MB for large datasets

### 3. Quality Metrics
- **False Positive Rate**: < 5%
- **False Negative Rate**: < 10%
- **Confidence Score Distribution**: Balanced across confidence levels

## Monitoring and Reporting

### 1. Test Reports
**Automated Reporting**:
```bash
# Generate comprehensive test report
python -m pytest tests/unit/test_vector_matching.py --html=reports/vector_matching_report.html --self-contained-html
```

**Performance Reports**:
```bash
# Generate performance report
python scripts/generate_vector_performance_report.py
```

### 2. Continuous Monitoring
**Metrics to Track**:
- Daily test execution results
- Performance trend analysis
- Accuracy metrics over time
- Error rate monitoring

### 3. Alerting
**Triggers**:
- Test failure rate > 5%
- Performance degradation > 20%
- Accuracy drop > 10%

## Troubleshooting Guide

### 1. Common Issues

#### A. Low Similarity Scores
**Symptoms**: All matches have low confidence scores
**Causes**:
- Embedding model issues
- Data preprocessing problems
- Threshold too high

**Solutions**:
```python
# Check embedding generation
def debug_embedding_quality():
    # Verify embedding dimensions
    # Check for NaN values
    # Validate embedding normalization
```

#### B. Poor Performance
**Symptoms**: Slow query execution
**Causes**:
- Missing vector index
- Large dataset without optimization
- Database connection issues

**Solutions**:
```sql
-- Check if vector index exists
SELECT * FROM pg_indexes WHERE indexname LIKE '%vector%';

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM customer_data.customers WHERE ...;
```

#### C. Inconsistent Results
**Symptoms**: Same input produces different results
**Causes**:
- Non-deterministic embedding generation
- Database state changes
- Configuration issues

**Solutions**:
```python
# Enable debug logging
logging.getLogger('app.services.matching.vector_matcher').setLevel(logging.DEBUG)

# Check configuration
print(f"Vector threshold: {settings.vector_similarity_threshold}")
print(f"Max results: {settings.vector_max_results}")
```

### 2. Debug Tools

#### A. Vector Similarity Debugger
```python
def debug_vector_similarity(query_embedding, candidate_embedding):
    """Debug vector similarity calculation"""
    similarity = cosine_similarity(query_embedding, candidate_embedding)
    print(f"Similarity score: {similarity}")
    print(f"Query embedding shape: {len(query_embedding)}")
    print(f"Candidate embedding shape: {len(candidate_embedding)}")
    return similarity
```

#### B. Query Analyzer
```python
def analyze_vector_query(query_embedding, threshold):
    """Analyze vector query execution"""
    # Log query parameters
    # Execute with EXPLAIN ANALYZE
    # Return performance metrics
```

## Conclusion

This vector matching testing plan provides a comprehensive framework for validating the semantic similarity functionality. The plan covers all aspects from unit testing to performance optimization, ensuring robust and reliable vector matching capabilities.

Key success factors:
1. **Thorough semantic testing** with diverse company name variations
2. **Performance optimization** for production-scale datasets
3. **Continuous monitoring** of accuracy and performance metrics
4. **Comprehensive edge case handling** for real-world scenarios

Regular execution of these tests will help maintain high-quality vector matching and identify opportunities for improvement. 