# Enhanced Database View Implementation

## Overview

This directory contains the enhanced database view implementation for the customer matching display system. The implementation provides comprehensive side-by-side comparison capabilities, field-level matching analysis, and performance-optimized queries for displaying matching results.

## Files Structure

```
sql/
├── 01-setup-pgvector.sql           # Base database schema and initial views
├── 02-functions.sql                # Database functions for matching
├── 03-create-test-results-table.sql # Test results table schema
├── 04-enhanced-display-view.sql     # ✨ Enhanced view implementation
├── exec-sql-file.sh                 # SQL file execution script
└── README.md                        # This documentation
```

## Enhanced Views

### 1. `customer_data.v_detailed_matches`

The main enhanced view providing comprehensive matching details with side-by-side comparison capabilities.

**Key Features:**
- **Side-by-side comparison**: All fields from both incoming and matched customers
- **Field comparison flags**: Exact, similar, different, missing classifications
- **Confidence categorization**: High, Medium, Low, Very Low categories
- **Match quality scoring**: 0-100 calculated score based on field matches
- **Recommendation engine**: Auto-approve, Review recommended, Needs review, Needs attention
- **Performance metrics**: Processing time calculations
- **Statistical aggregations**: Match counts and distributions

**Example Query:**
```sql
SELECT 
    request_id,
    incoming_company,
    matched_company,
    confidence_level,
    confidence_category,
    company_name_match,
    email_match,
    phone_match,
    match_quality_score,
    recommendation
FROM customer_data.v_detailed_matches
WHERE confidence_level >= 0.8
ORDER BY confidence_level DESC, match_quality_score DESC;
```

### 2. `customer_data.v_matching_summary`

Summary statistics view providing aggregated information about matching performance.

**Key Features:**
- **Overall statistics**: Total customers, processed, pending
- **Confidence distribution**: Breakdown by confidence levels
- **Match type distribution**: Count by match types
- **Performance metrics**: Average processing times
- **Date ranges**: Earliest and latest processing dates

**Example Query:**
```sql
SELECT 
    total_incoming_customers,
    processed_customers,
    pending_customers,
    high_confidence_matches,
    avg_confidence_level,
    avg_processing_time_ms
FROM customer_data.v_matching_summary;
```

## Field Comparison Logic

The enhanced view includes sophisticated field comparison logic for each customer attribute:

### Company Name Matching
- **Exact**: Case-insensitive exact match
- **Similar**: Similarity score >= 0.8
- **Related**: Similarity score >= 0.6
- **Different**: Similarity score < 0.6

### Email Matching
- **Exact**: Case-insensitive exact match
- **Similar**: Partial string match (contains)
- **Same Domain**: Same email domain
- **Different**: No match
- **Missing**: One or both values are NULL

### Phone Matching
- **Exact**: Normalized phone numbers match exactly
- **Similar**: Last 10 digits match (handles different formatting)
- **Different**: No match
- **Missing**: One or both values are NULL

### Revenue/Employee Count Matching
- **Exact**: Identical values
- **Similar**: Within 10% (revenue) or 20% (employee count)
- **Related**: Within 25% (revenue) or 50% (employee count)
- **Different**: Outside tolerance ranges
- **Missing**: One or both values are NULL

## Match Quality Scoring

The view calculates a comprehensive match quality score (0-100) based on weighted field matches:

- **Company Name**: 25 points (exact), 20 points (similar), 15 points (related)
- **Email**: 20 points (exact), 10 points (same domain)
- **Contact Name**: 15 points (exact), 12 points (similar), 8 points (related)
- **Phone**: 15 points (exact), 10 points (similar)
- **Industry**: 10 points (exact), 8 points (similar)
- **City**: 10 points (exact), 8 points (similar)
- **Country**: 5 points (exact)

## Confidence Categorization

The system categorizes matches into confidence levels:

| Category | Confidence Range | Indicator | Recommendation |
|----------|------------------|-----------|----------------|
| High | 0.9 - 1.0 | 🟢 | Auto-approve (≥0.95) / Review recommended (≥0.85) |
| Medium | 0.7 - 0.9 | 🟡 | Needs review |
| Low | 0.5 - 0.7 | 🟠 | Needs attention |
| Very Low | < 0.5 | 🔴 | Needs attention |

## Performance Optimizations

### Indexes Created
- `idx_matching_results_confidence_desc`: Confidence level descending
- `idx_matching_results_similarity_desc`: Similarity score descending
- `idx_matching_results_incoming_confidence`: Incoming customer + confidence
- `idx_matching_results_type_confidence`: Match type + confidence
- `idx_matching_results_created_date`: Creation date descending
- `idx_incoming_customers_processed_date`: Processing date descending
- `idx_incoming_customers_processing_status`: Processing status

### Query Performance
- **Target Response Time**: < 500ms for standard queries
- **Pagination Support**: Built-in support for LIMIT/OFFSET
- **Filtering Optimization**: Indexed fields for common filters
- **Sorting Performance**: Optimized for confidence and quality sorting

## Deployment

### Prerequisites
- PostgreSQL 12+ with pgvector extension
- Customer data schema with existing tables
- Azure CLI (for using exec-sql-file.sh)
- Environment variables configured in `app/.env`

### Quick Deployment
```bash
# Navigate to sql directory
cd sql

# Execute the enhanced view script
./exec-sql-file.sh 04-enhanced-display-view.sql
```

### Manual Deployment
```bash
# Connect to PostgreSQL
psql -h your-host -p 5432 -U your-user -d your-database

# Execute the enhanced view script
\i 04-enhanced-display-view.sql
```

## Testing

### Manual Testing
After deployment, you can validate the view functionality using these queries:
```sql
-- Test basic view functionality
SELECT COUNT(*) FROM customer_data.v_detailed_matches;

-- Test confidence categorization
SELECT confidence_category, COUNT(*) 
FROM customer_data.v_detailed_matches 
GROUP BY confidence_category;

-- Test field comparison flags
SELECT company_name_match, email_match, COUNT(*) 
FROM customer_data.v_detailed_matches 
GROUP BY company_name_match, email_match;

-- Test summary view
SELECT * FROM customer_data.v_matching_summary;
```

## API Integration

### Recommended Usage Patterns

#### For Detailed Match Display
```sql
-- Get detailed matches for a specific incoming customer
SELECT * FROM customer_data.v_detailed_matches 
WHERE request_id = ? 
ORDER BY confidence_level DESC, match_quality_score DESC;
```

#### For Summary Dashboard
```sql
-- Get summary statistics
SELECT * FROM customer_data.v_matching_summary;
```

#### For Filtering and Pagination
```sql
-- Filter by confidence and paginate
SELECT * FROM customer_data.v_detailed_matches 
WHERE confidence_category = 'High' 
  AND match_quality_score >= 80
ORDER BY confidence_level DESC 
LIMIT 25 OFFSET 0;
```

#### For Export Functionality
```sql
-- Export matches with specific criteria
SELECT 
    request_id,
    incoming_company,
    matched_company,
    confidence_level,
    match_quality_score,
    recommendation,
    processing_time_ms
FROM customer_data.v_detailed_matches 
WHERE confidence_level >= 0.7
ORDER BY confidence_level DESC;
```

## Troubleshooting

### Common Issues

#### 1. View Creation Fails
- **Cause**: Missing base tables or functions
- **Solution**: Ensure `01-setup-pgvector.sql` and `02-functions.sql` are executed first

#### 2. Slow Query Performance
- **Cause**: Missing indexes or large dataset
- **Solution**: Verify indexes are created, consider adding LIMIT clauses

#### 3. Unexpected NULL Values
- **Cause**: Data quality issues in source tables
- **Solution**: Check source data integrity, consider adding COALESCE functions

#### 4. Memory Usage Issues
- **Cause**: Large result sets without pagination
- **Solution**: Use LIMIT/OFFSET for pagination, add filtering criteria

### Performance Tuning

#### Query Optimization
```sql
-- Use indexes effectively
SELECT * FROM customer_data.v_detailed_matches 
WHERE confidence_level >= 0.8  -- Uses index
ORDER BY confidence_level DESC; -- Uses index

-- Avoid full table scans
SELECT * FROM customer_data.v_detailed_matches 
WHERE incoming_company LIKE '%Company%'  -- Consider full-text search instead
```

#### Memory Management
```sql
-- Use pagination for large results
SELECT * FROM customer_data.v_detailed_matches 
ORDER BY confidence_level DESC 
LIMIT 100 OFFSET 0;

-- Use specific columns instead of SELECT *
SELECT request_id, incoming_company, matched_company, confidence_level
FROM customer_data.v_detailed_matches;
```

## Monitoring

### Performance Metrics
```sql
-- Monitor query performance
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE query LIKE '%v_detailed_matches%'
ORDER BY total_time DESC;

-- Monitor index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read
FROM pg_stat_user_indexes 
WHERE schemaname = 'customer_data'
ORDER BY idx_scan DESC;
```

### Health Checks
```sql
-- Check view health
SELECT 
    'v_detailed_matches' as view_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT request_id) as unique_requests,
    AVG(confidence_level) as avg_confidence
FROM customer_data.v_detailed_matches;
```

## Next Steps

1. **API Implementation**: Create FastAPI endpoints using these views
2. **User Interface**: Build display components for web interface
3. **Export Features**: Implement CSV/Excel export functionality
4. **Monitoring**: Set up query performance monitoring
5. **Data Validation**: Add data quality checks and alerts

## Support

For issues or questions regarding the enhanced database view implementation:

1. Check the troubleshooting section above
2. Verify all prerequisite scripts have been executed successfully
3. Test the view manually using the provided example queries
4. Check the Azure CLI output for any deployment errors

---

*This implementation provides a robust foundation for displaying customer matching results with comprehensive comparison capabilities and performance optimization.* 