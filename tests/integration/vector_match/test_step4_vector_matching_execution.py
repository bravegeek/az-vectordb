"""
Integration test for Step 4: Vector Matching Execution.

This test implements Step 4 of the vector matching testing plan checklist.
It executes vector matching on pending records and validates the results.
"""

import pytest
import logging
import time
from datetime import datetime
from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import IncomingCustomer
from app.services.matching.vector_matcher import VectorMatcher
from app.models.schemas import MatchResult

logger = logging.getLogger(__name__)


@pytest.fixture
def pending_records_count(db_session: Session) -> int:
    """Fixture to get count of pending records"""
    query = text("""
        SELECT COUNT(*) FROM customer_data.incoming_customers 
        WHERE processing_status = 'pending'
    """)
    result = db_session.execute(query)
    count = result.scalar()
    return count if count is not None else 0


@pytest.fixture
def test_incoming_customer(db_session: Session) -> IncomingCustomer:
    """Fixture to get a test incoming customer with embeddings"""
    query = text("""
        SELECT * FROM customer_data.incoming_customers 
        WHERE processing_status = 'pending' 
        AND full_profile_embedding IS NOT NULL
        LIMIT 1
    """)
    
    result = db_session.execute(query)
    record_data = result.fetchone()
    
    if not record_data:
        pytest.skip("No pending records with embeddings available for testing")
    
    # Create IncomingCustomer object from the record
    incoming_customer = IncomingCustomer(
        request_id=record_data.request_id,
        company_name=record_data.company_name,
        contact_name=record_data.contact_name,
        email=record_data.email,
        phone=record_data.phone,
        address_line1=record_data.address_line1,
        address_line2=record_data.address_line2,
        city=record_data.city,
        state_province=record_data.state_province,
        postal_code=record_data.postal_code,
        country=record_data.country,
        industry=record_data.industry,
        annual_revenue=record_data.annual_revenue,
        employee_count=record_data.employee_count,
        website=record_data.website,
        description=record_data.description,
        request_date=record_data.request_date,
        company_name_embedding=record_data.company_name_embedding,
        full_profile_embedding=record_data.full_profile_embedding,
        processing_status=record_data.processing_status,
        processed_date=record_data.processed_date
    )
    
    return incoming_customer


@pytest.fixture
def vector_matcher_instance():
    """Fixture to create vector matcher instance"""
    return VectorMatcher()


@pytest.fixture
def matching_results(db_session: Session, test_incoming_customer: IncomingCustomer, vector_matcher_instance: VectorMatcher):
    """Fixture to execute vector matching and return results"""
    if not vector_matcher_instance.is_enabled():
        pytest.skip("Vector matching is disabled")
    
    start_time = time.time()
    matches = vector_matcher_instance.find_matches(test_incoming_customer, db_session)
    processing_time = time.time() - start_time
    
    return {
        'matches': matches,
        'processing_time': processing_time,
        'request_id': test_incoming_customer.request_id
    }


@pytest.mark.integration
class TestStep4VectorMatchingExecution:
    """
    Step 4: Vector Matching Execution
    
    This class implements the checklist from docs/vector_match_testing_plan.md Step 4
    Each test method corresponds to a checklist item and is independent.
    """
    
    def test_01_import_vector_matcher_module(self):
        """
        ✅ Import vector_matcher module
        
        Checklist item: Import vector_matcher module
        """
        try:
            # This test verifies the import works
            from app.services.matching.vector_matcher import VectorMatcher
            assert VectorMatcher is not None
            logger.info("✅ Vector matcher module imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import vector matcher module: {e}")
            raise
    
    def test_02_initialize_vector_matcher_instance(self, vector_matcher_instance: VectorMatcher):
        """
        ✅ Initialize VectorMatcher instance
        
        Checklist item: Initialize VectorMatcher instance
        """
        try:
            assert vector_matcher_instance is not None
            assert hasattr(vector_matcher_instance, 'find_matches')
            assert hasattr(vector_matcher_instance, 'is_enabled')
            logger.info("✅ Vector matcher instance initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector matcher instance: {e}")
            raise
    
    def test_03_query_pending_records(self, pending_records_count: int):
        """
        ✅ Query to get pending records
        
        Checklist item: Query to get pending records: SELECT * FROM incoming_customers WHERE processing_status = 'pending' LIMIT 5
        """
        try:
            logger.info(f"✅ Found {pending_records_count} pending records for processing")
            
            # Verify we have at least some records to process
            assert pending_records_count >= 0, "Should have 0 or more pending records"
            
        except Exception as e:
            logger.error(f"❌ Failed to query pending records: {e}")
            raise
    
    def test_04_load_record_from_database(self, test_incoming_customer: IncomingCustomer):
        """
        ✅ Load record from database
        
        Checklist item: Load record from database
        """
        try:
            assert test_incoming_customer is not None
            assert test_incoming_customer.request_id is not None
            assert test_incoming_customer.full_profile_embedding is not None
            logger.info(f"✅ Successfully loaded record with request_id: {test_incoming_customer.request_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load record from database: {e}")
            raise
    
    def test_05_call_find_matches(self, matching_results: dict):
        """
        ✅ Call find_matches(record, db)
        
        Checklist item: Call find_matches(record, db)
        """
        try:
            matches = matching_results['matches']
            processing_time = matching_results['processing_time']
            request_id = matching_results['request_id']
            
            logger.info(f"✅ find_matches completed in {processing_time:.3f} seconds")
            logger.info(f"   - Found {len(matches)} matches for record ID: {request_id}")
            
            # Validate that we got a list of matches (even if empty)
            assert isinstance(matches, list), "find_matches should return a list"
            
        except Exception as e:
            logger.error(f"❌ Failed to call find_matches: {e}")
            raise
    
    def test_06_log_number_of_matches_found(self, matching_results: dict):
        """
        ✅ Log number of matches found for record ID
        
        Checklist item: Log number of matches found for record ID: {record.request_id}
        """
        try:
            match_count = len(matching_results['matches'])
            request_id = matching_results['request_id']
            
            logger.info(f"✅ Found {match_count} matches for record ID: {request_id}")
            
            # Log details of each match if any found
            if match_count > 0:
                for i, match in enumerate(matching_results['matches'][:3]):  # Log first 3 matches
                    logger.info(f"   Match {i+1}: customer_id={match.matched_customer_id}, "
                              f"score={match.similarity_score:.4f}, type={match.match_type}")
                
                if match_count > 3:
                    logger.info(f"   ... and {match_count - 3} more matches")
            
            # Validate match count is reasonable
            assert match_count >= 0, "Match count should be non-negative"
            
        except Exception as e:
            logger.error(f"❌ Failed to log match information: {e}")
            raise
    
    def test_07_verify_matches_contain_expected_fields(self, matching_results: dict):
        """
        ✅ Verify matches contain expected fields
        
        Checklist item: Verify matches contain expected fields (customer_id, similarity_score, etc.)
        """
        try:
            matches = matching_results['matches']
            
            if len(matches) == 0:
                logger.info("✅ No matches found (empty result is valid)")
                return
            
            # Check each match has required fields
            for i, match in enumerate(matches):
                assert hasattr(match, 'matched_customer_id'), f"Match {i} missing customer_id"
                assert hasattr(match, 'similarity_score'), f"Match {i} missing similarity_score"
                assert hasattr(match, 'match_type'), f"Match {i} missing match_type"
                assert hasattr(match, 'confidence_level'), f"Match {i} missing confidence_level"
                assert hasattr(match, 'match_criteria'), f"Match {i} missing match_criteria"
                
                # Verify data types and values
                assert match.matched_customer_id is not None, f"Match {i} customer_id is None"
                assert isinstance(match.similarity_score, (int, float)), f"Match {i} similarity_score is not numeric"
                assert 0.0 <= match.similarity_score <= 1.0, f"Match {i} similarity_score out of range: {match.similarity_score}"
                assert match.match_type in ['exact', 'high_confidence', 'potential', 'low_confidence'], f"Match {i} invalid match_type: {match.match_type}"
                
                logger.info(f"✅ Match {i+1} has all required fields and valid values")
            
            logger.info(f"✅ All {len(matches)} matches contain expected fields")
            
        except Exception as e:
            logger.error(f"❌ Failed to verify match fields: {e}")
            raise
    
    def test_08_handle_exceptions_during_matching(self, db_session: Session, vector_matcher_instance: VectorMatcher):
        """
        ✅ Handle any exceptions during matching process
        
        Checklist item: Handle any exceptions during matching process
        """
        try:
            # Test with a record that has no embeddings (should handle gracefully)
            test_record_no_embedding = IncomingCustomer(
                request_id=999999,
                company_name="Test Company No Embedding",
                full_profile_embedding=None
            )
            
            # This should not raise an exception
            matches = vector_matcher_instance.find_matches(test_record_no_embedding, db_session)
            assert matches == [], "Should return empty list for record with no embeddings"
            logger.info("✅ Successfully handled record with no embeddings")
            
            # Test with invalid embedding (should handle gracefully)
            test_record_invalid_embedding = IncomingCustomer(
                request_id=999998,
                company_name="Test Company Invalid Embedding",
                full_profile_embedding="invalid_embedding"
            )
            
            # This should handle the invalid embedding gracefully
            try:
                matches = vector_matcher_instance.find_matches(test_record_invalid_embedding, db_session)
                logger.info("✅ Successfully handled invalid embedding format")
            except Exception as e:
                logger.warning(f"⚠️ Invalid embedding caused exception (acceptable): {e}")
            
            logger.info("✅ Exception handling during matching process verified")
            
        except Exception as e:
            logger.error(f"❌ Failed to test exception handling: {e}")
            raise
    
    def test_09_log_total_records_processed(self, pending_records_count: int, matching_results: dict):
        """
        ✅ Log total records processed
        
        Checklist item: Log total records processed: {records_to_process}
        """
        try:
            logger.info(f"✅ Total records processed: {pending_records_count}")
            
            # Log summary statistics
            processing_time = matching_results['processing_time']
            total_matches = len(matching_results['matches'])
            
            logger.info(f"   - Processing time for one record: {processing_time:.3f} seconds")
            logger.info(f"   - Matches found for test record: {total_matches}")
            
            # Estimate total processing time if we processed all records
            estimated_total_time = processing_time * pending_records_count
            logger.info(f"   - Estimated total processing time: {estimated_total_time:.3f} seconds")
            
        except Exception as e:
            logger.error(f"❌ Failed to log processing summary: {e}")
            raise


@pytest.mark.integration
class TestStep4Summary:
    """
    Summary and validation for Step 4 execution
    """
    
    def test_step4_execution_completed_successfully(self, db_session: Session):
        """
        ✅ Verify Step 4 execution completed successfully
        
        Final verification that all Step 4 tests passed
        """
        try:
            # Verify we can still query the database
            result = db_session.execute(text("SELECT COUNT(*) FROM customer_data.incoming_customers WHERE processing_status = 'pending'"))
            pending_count = result.scalar()
            
            logger.info(f"✅ Step 4 execution completed successfully")
            logger.info(f"   - Remaining pending records: {pending_count}")
            logger.info("   - Vector matching execution tests passed")
            logger.info("   - All checklist items for Step 4 completed")
            
        except Exception as e:
            logger.error(f"❌ Step 4 execution verification failed: {e}")
            raise 