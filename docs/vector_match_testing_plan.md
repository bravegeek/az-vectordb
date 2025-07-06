# Test vector matching

1. Use records from Incoming Customers table for data
2. Only use records that have a processing_status of 'pending'
   1. limit 5
3. If no pending records exist, create some with generate_incoming_customers
   1. Insert those into the Incoming Customers table
   2. Generate 5 records each of low, medium, and high variation intensity
4. Use vector_matcher to find matches
5. Save results with result_processor
6. Test error scenarios:
   1. Records with NULL embeddings
   2. Database connection failures
   3. Invalid customer_id references
7. Validate results:
   1. Check that all processed records have status = 'processed'
   2. Verify similarity scores are within expected ranges (0.0-1.0)
   3. Confirm no duplicate matches for same customer
8. Monitor performance:
   1. Track processing time per record
   2. Monitor database query performance
   3. Check for any timeout issues
9. Reset test data (optional):
   1. Option to reset processing_status back to 'pending' for re-testing
   2. Clear matching_results for test records

---

## AI Agent Implementation Checklist

### Pre-Testing Setup

- [X] Verify database connection is working
- [X] Check that vector_matcher service is properly configured
- [X] Confirm result_processor service is available
- [X] Validate environment variables are set correctly
- [X] Ensure pgvector extension is enabled in PostgreSQL

### Step 1: Data Source Verification

- [X] Query Incoming Customers table to confirm it exists
- [X] Check table structure and required columns
- [X] Verify data types match expected schema
- [X] Confirm table has records available for testing

### Step 2: Pending Records Check

- [X] Execute query: `SELECT COUNT(*) FROM incoming_customers WHERE processing_status = 'pending'`
- [X] Store the count as `pending_count`
- [X] If `pending_count` >= 5: proceed to Step 4
- [X] If `pending_count` < 5: proceed to Step 3
- [X] Log the number of pending records found: `{pending_count}`

### Step 3: Test Data Generation

- [ ] Check if generate_incoming_customers.py script exists
- [ ] Verify script dependencies are installed
- [ ] Run script with parameters: `--count 5 --variation-intensity low`
- [ ] Run script with parameters: `--count 5 --variation-intensity medium`
- [ ] Run script with parameters: `--count 5 --variation-intensity high`
- [ ] Query to verify records created: `SELECT processing_status, COUNT(*) FROM incoming_customers WHERE created_date >= NOW() - INTERVAL '1 hour' GROUP BY processing_status`
- [ ] Verify total new records = 15 (5 low + 5 medium + 5 high)
- [ ] Confirm new records have processing_status = 'pending'
- [ ] Log actual counts for each variation intensity created

### Step 4: Vector Matching Execution

- [ ] Import vector_matcher module
- [ ] Initialize VectorMatcher instance
- [ ] Query to get pending records: `SELECT * FROM incoming_customers WHERE processing_status = 'pending' LIMIT 5`
- [ ] Store the actual number of records to process as `records_to_process`
- [ ] For each pending record (up to `records_to_process`):
  - [ ] Load record from database
  - [ ] Call `find_matches(record, db)`
  - [ ] Log number of matches found for record ID: `{record.request_id}`
  - [ ] Verify matches contain expected fields (customer_id, similarity_score, etc.)
- [ ] Handle any exceptions during matching process
- [ ] Log total records processed: `{records_to_process}`

### Step 5: Result Processing

- [ ] Import result_processor module
- [ ] Initialize ResultProcessor instance
- [ ] For each record with matches:
  - [ ] Call `process_results(matches, request_id, db)`
  - [ ] Verify results are stored in database
  - [ ] Confirm processing_status is updated to 'processed'
  - [ ] Log processing completion for each record

### Step 6: Error Scenario Testing

- [ ] **NULL Embeddings Test:**
  - [ ] Find or create record with NULL full_profile_embedding
  - [ ] Attempt vector matching on NULL embedding record
  - [ ] Verify system handles gracefully (returns empty results or error message)
  - [ ] Log error handling behavior
- [ ] **Database Connection Failure Test:**
  - [ ] Simulate database connection issue (if possible)
  - [ ] Verify system provides appropriate error message
  - [ ] Confirm no partial data corruption occurs
- [ ] **Invalid Customer ID Test:**
  - [ ] Check for any matching results with invalid customer_id references
  - [ ] Verify referential integrity is maintained
  - [ ] Log any data integrity issues found

### Step 7: Result Validation

- [ ] **Status Verification:**
  - [ ] Query: `SELECT COUNT(*) FROM incoming_customers WHERE processing_status = 'processed'`
  - [ ] Store processed count as `processed_count`
  - [ ] Verify `processed_count` matches `records_to_process` from Step 4
  - [ ] Log status verification results: `{processed_count} records processed`
- [ ] **Similarity Score Validation:**
  - [ ] Query: `SELECT COUNT(*) FROM matching_results WHERE similarity_score < 0.0 OR similarity_score > 1.0`
  - [ ] Verify count = 0 (no invalid scores)
  - [ ] Log score validation results
- [ ] **Duplicate Detection:**
  - [ ] Execute duplicate detection query
  - [ ] Verify no duplicate matches exist for same customer
  - [ ] Log duplicate check results

### Step 8: Performance Monitoring

- [ ] **Processing Time Tracking:**
  - [ ] Measure execution time for each record processing
  - [ ] Calculate average processing time
  - [ ] Log performance metrics
- [ ] **Database Query Performance:**
  - [ ] Monitor vector similarity query execution times
  - [ ] Check for any slow queries (>5 seconds)
  - [ ] Log query performance data
- [ ] **Timeout Detection:**
  - [ ] Monitor for any timeout errors
  - [ ] Verify system handles long-running queries appropriately
  - [ ] Log timeout incidents

### Step 9: Test Data Reset (Optional)

- [ ] **Status Reset:**
  - [ ] Update processing_status back to 'pending' for test records
  - [ ] Clear processed_date for reset records
  - [ ] Verify reset was successful
- [ ] **Result Cleanup:**
  - [ ] Delete matching_results for test records
  - [ ] Verify cleanup was successful
  - [ ] Log reset completion

### Final Verification

- [ ] Generate summary report of all test results
- [ ] Document any issues or anomalies found
- [ ] Verify all checklist items are completed
- [ ] Log final test completion status

### Error Handling

- [ ] If any step fails, log detailed error information
- [ ] Attempt to continue with remaining steps where possible
- [ ] Provide clear error messages for debugging
- [ ] Ensure database remains in consistent state

### Success Criteria

- [ ] All pending records processed successfully
- [ ] No data integrity issues detected
- [ ] Performance within acceptable limits
- [ ] Error scenarios handled gracefully
- [ ] All validation checks passed
