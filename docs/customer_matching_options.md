# Customer Matching Options

This document outlines the various strategies available for matching incoming customer records to existing customers in your database.

## Overview

Your system supports multiple customer matching strategies, from simple exact field matching to sophisticated AI-powered vector similarity matching. You can use these strategies individually or combine them in a hybrid approach for optimal results.

## Available Matching Strategies

### 1. **Exact Field Matching**
- **Purpose**: Find customers with identical key fields
- **Best for**: High-confidence matches when data quality is good
- **Fields matched**: Company name, email, phone number
- **Scoring**: Weighted scoring based on number of exact matches
- **API Endpoint**: `POST /customers/match-exact/{request_id}`

**Example Use Case**:
```bash
curl -X POST "http://localhost:8000/customers/match-exact/1"
```

**Configuration**:
- `exact_company_name_weight`: 0.4 (40% of total score)
- `exact_email_weight`: 0.4 (40% of total score)  
- `exact_phone_weight`: 0.2 (20% of total score)
- `exact_match_min_score`: 0.4 (minimum score to consider a match)

### 2. **Vector Similarity Matching**
- **Purpose**: Find semantically similar customers using AI embeddings
- **Best for**: Fuzzy matching when exact matches aren't available
- **Technology**: Azure OpenAI embeddings + PostgreSQL pgvector
- **Scoring**: Cosine similarity (0.0 to 1.0)
- **API Endpoint**: `POST /customers/match/{request_id}`

**Example Use Case**:
```bash
curl -X POST "http://localhost:8000/customers/match/1"
```

**Configuration**:
- `vector_similarity_threshold`: 0.7 (minimum similarity)
- `vector_max_results`: 5 (maximum matches returned)
- `exact_match_threshold`: 0.95 (exact match)
- `high_confidence_threshold`: 0.9 (high confidence)
- `potential_match_threshold`: 0.75 (potential match)

### 3. **Fuzzy String Matching**
- **Purpose**: Find customers with similar text using string similarity
- **Best for**: Company name variations and typos
- **Technology**: PostgreSQL similarity functions
- **Scoring**: String similarity (0.0 to 1.0)
- **API Endpoint**: Available through hybrid matching

**Configuration**:
- `fuzzy_similarity_threshold`: 0.8 (minimum similarity)
- `fuzzy_max_results`: 10 (maximum matches returned)

### 4. **Hybrid Matching (Recommended)**
- **Purpose**: Combine all strategies for optimal results
- **Best for**: Production environments requiring high accuracy
- **Strategy**: Exact → Vector → Fuzzy (in order of priority)
- **API Endpoint**: `POST /customers/match-hybrid/{request_id}`

**Example Use Case**:
```bash
curl -X POST "http://localhost:8000/customers/match-hybrid/1"
```

## Match Types and Confidence Levels

### Match Types
- **exact**: ≥0.95 similarity or exact field matches
- **high_confidence**: ≥0.85 similarity
- **potential**: ≥0.75 similarity
- **low_confidence**: <0.75 similarity

### Business Rules
The system applies business rules to adjust confidence levels:

- **Industry Match Boost**: +20% confidence for same industry
- **Location Match Boost**: +10% confidence for same city
- **Country Mismatch Penalty**: -20% confidence for different countries
- **Revenue Size Boost**: +10% confidence for similar revenue size

## Configuration Options

### Environment Variables
```bash
# Matching Strategy Settings
DEFAULT_SIMILARITY_THRESHOLD=0.8
HIGH_CONFIDENCE_THRESHOLD=0.9
POTENTIAL_MATCH_THRESHOLD=0.75
EXACT_MATCH_THRESHOLD=0.95

# Exact Matching Weights
EXACT_COMPANY_NAME_WEIGHT=0.4
EXACT_EMAIL_WEIGHT=0.4
EXACT_PHONE_WEIGHT=0.2
EXACT_MATCH_MIN_SCORE=0.4

# Fuzzy Matching Settings
FUZZY_SIMILARITY_THRESHOLD=0.8
FUZZY_MAX_RESULTS=10

# Vector Matching Settings
VECTOR_SIMILARITY_THRESHOLD=0.7
VECTOR_MAX_RESULTS=5

# Hybrid Matching Settings
ENABLE_EXACT_MATCHING=true
ENABLE_VECTOR_MATCHING=true
ENABLE_FUZZY_MATCHING=true

# Business Rules
ENABLE_BUSINESS_RULES=true
INDUSTRY_MATCH_BOOST=1.2
LOCATION_MATCH_BOOST=1.1
COUNTRY_MISMATCH_PENALTY=0.8
REVENUE_SIZE_BOOST=true
```

## API Usage Examples

### 1. Submit Incoming Customer
```bash
curl -X POST "http://localhost:8000/customers/incoming" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "ACME Corp",
    "contact_name": "John Smith",
    "email": "john.smith@acme.com",
    "phone": "555-123-4567",
    "city": "New York",
    "industry": "Technology",
    "annual_revenue": 1000000
  }'
```

### 2. Process Hybrid Matching
```bash
curl -X POST "http://localhost:8000/customers/match-hybrid/1"
```

### 3. Get Matching Results
```bash
curl -X GET "http://localhost:8000/matches/1"
```

## Response Format

```json
{
  "incoming_customer": {
    "request_id": 1,
    "company_name": "ACME Corp",
    "contact_name": "John Smith",
    "email": "john.smith@acme.com",
    "processing_status": "processed"
  },
  "matches": [
    {
      "match_id": 1,
      "matched_customer_id": 123,
      "matched_company_name": "Acme Corporation",
      "matched_contact_name": "John Smith",
      "matched_email": "john.smith@acme.com",
      "similarity_score": 0.95,
      "match_type": "exact",
      "confidence_level": 0.95,
      "match_criteria": {
        "exact_company_name": true,
        "exact_email": true,
        "industry_match": true
      },
      "created_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total_matches": 1,
  "processing_time_ms": 245.67
}
```

## Performance Considerations

### Database Indexes
- **Vector Indexes**: HNSW indexes for fast similarity search
- **Text Indexes**: GIN indexes for full-text search
- **Field Indexes**: B-tree indexes on key fields

### Optimization Tips
1. **Batch Processing**: Process multiple customers in batches
2. **Caching**: Cache embeddings for frequently accessed data
3. **Thresholds**: Adjust similarity thresholds based on your data quality
4. **Indexing**: Ensure proper database indexes are in place

## Choosing the Right Strategy

### Use Exact Matching When:
- Data quality is high
- You need deterministic results
- Processing speed is critical
- False positives are costly

### Use Vector Matching When:
- Data has natural language variations
- You want semantic understanding
- Exact matches are rare
- You have rich descriptive data

### Use Hybrid Matching When:
- You want the best of all worlds
- Data quality varies
- You need high accuracy
- You can tolerate slightly slower processing

### Use Fuzzy Matching When:
- Company names have typos or variations
- You want to catch spelling differences
- Exact matching is too restrictive

## Monitoring and Tuning

### Key Metrics to Monitor
- **Match Accuracy**: Percentage of correct matches
- **Processing Time**: Time to process each request
- **Match Distribution**: Distribution across match types
- **False Positives**: Incorrect matches
- **False Negatives**: Missed matches

### Tuning Parameters
1. **Similarity Thresholds**: Adjust based on your data quality
2. **Weights**: Modify exact matching weights based on field reliability
3. **Business Rules**: Customize rules based on your domain
4. **Batch Sizes**: Optimize for your processing requirements

## Troubleshooting

### Common Issues
1. **No Matches Found**: Lower similarity thresholds
2. **Too Many Matches**: Increase similarity thresholds
3. **Slow Performance**: Check database indexes
4. **Poor Accuracy**: Review business rules and weights

### Debugging
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Check match criteria in response
- Review similarity scores
- Analyze business rule impacts

## Future Enhancements

### Potential Improvements
1. **Machine Learning Models**: Train custom models for your domain
2. **Real-time Learning**: Update models based on user feedback
3. **Multi-language Support**: Handle international customers
4. **Advanced Business Rules**: More sophisticated rule engines
5. **A/B Testing**: Compare different matching strategies

### Integration Options
1. **Webhook Notifications**: Real-time match notifications
2. **Batch Processing**: Process large datasets efficiently
3. **API Rate Limiting**: Handle high-volume requests
4. **Audit Logging**: Track all matching decisions 