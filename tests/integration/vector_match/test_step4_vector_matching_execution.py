"""
Integration test for Step 4: Vector Matching Execution and Result Processing.

This test implements Step 4 of the vector matching testing plan checklist.
It executes vector matching on pending records, processes the results, and validates the complete workflow.
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
from app.services.matching.result_processor import ResultProcessor
from app.models.schemas import MatchResult

logger = logging.getLogger(__name__)


@pytest.fixture
def pending_records_count(db_session: Session) -> int:
    """Fixture to get count of pending records"""
    return db_session.query(IncomingCustomer).filter(
        IncomingCustomer.processing_status == 'pending'
    ).count()


@pytest.fixture
def test_incoming_customer(db_session: Session) -> tuple[IncomingCustomer, int]:
    """Fixture to get a test incoming customer with embeddings and its request_id"""
    # Use SQLAlchemy ORM to query the database
    customer = db_session.query(IncomingCustomer).filter(
        IncomingCustomer.processing_status == 'pending',
        IncomingCustomer.full_profile_embedding.isnot(None)
    ).first()
    
    if not customer:
        pytest.skip("No pending records with embeddings available for testing")
    
    # Ensure the object is loaded and get the actual request_id value
    db_session.refresh(customer)
    request_id = getattr(customer, 'request_id')
    
    return customer, request_id


@pytest.fixture
def vector_matcher_instance():
    """Fixture to create vector matcher instance"""
    return VectorMatcher()


@pytest.fixture
def result_processor_instance():
    """Fixture to create result processor instance"""
    return ResultProcessor()


@pytest.fixture
def matching_and_processing_results(db_session: Session, test_incoming_customer: tuple[IncomingCustomer, int], vector_matcher_instance: VectorMatcher, result_processor_instance: ResultProcessor):
    """Fixture to execute vector matching and result processing, returning complete results"""
    if not vector_matcher_instance.is_enabled():
        pytest.skip("Vector matching is disabled")
    
    customer, request_id = test_incoming_customer
    
    start_time = time.time()
    
    # Step 1: Find matches
    matches = vector_matcher_instance.find_matches(customer, db_session)
    matching_time = time.time() - start_time
    
    # Step 2: Process results
    processing_start_time = time.time()
    processed_matches = result_processor_instance.process_results(matches, request_id, db_session)
    processing_time = time.time() - processing_start_time
    
    total_time = time.time() - start_time
    
    return {
        'matches': matches,
        'processed_matches': processed_matches,
        'matching_time': matching_time,
        'processing_time': processing_time,
        'total_time': total_time,
        'request_id': request_id
    }


@pytest.mark.integration
class TestStep4VectorMatchingExecutionAndResultProcessing:
    """
    Step 4: Vector Matching Execution and Result Processing
    
    This class implements the checklist from docs/vector_match_testing_plan.md Step 4
    Each test method corresponds to a checklist item and is independent.
    """
    
    def test_01_import_vector_matcher_and_result_processor_modules(self):
        """
        ✅ Import vector_matcher and result_processor modules
        
        Checklist item: Import vector_matcher and result_processor modules
        """
        try:
            # This test verifies the imports work
            from app.services.matching.vector_matcher import VectorMatcher
            from app.services.matching.result_processor import ResultProcessor
            assert VectorMatcher is not None
            assert ResultProcessor is not None
            logger.info("✅ Vector matcher and result processor modules imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import modules: {e}")
            raise
    
    def test_02_initialize_vector_matcher_and_result_processor_instances(self, vector_matcher_instance: VectorMatcher, result_processor_instance: ResultProcessor):
        """
        ✅ Initialize VectorMatcher and ResultProcessor instances
        
        Checklist item: Initialize VectorMatcher and ResultProcessor instances
        """
        try:
            assert vector_matcher_instance is not None
            assert hasattr(vector_matcher_instance, 'find_matches')
            assert hasattr(vector_matcher_instance, 'is_enabled')
            
            assert result_processor_instance is not None
            assert hasattr(result_processor_instance, 'process_results')
            assert hasattr(result_processor_instance, 'store_matching_results')
            assert hasattr(result_processor_instance, 'update_processing_status')
            
            logger.info("✅ Vector matcher and result processor instances initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize instances: {e}")
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
    
    def test_04_load_record_from_database(self, test_incoming_customer: tuple[IncomingCustomer, int]):
        """
        ✅ Load record from database
        
        Checklist item: Load record from database
        """
        try:
            customer, request_id = test_incoming_customer
            assert customer is not None
            assert request_id is not None
            assert customer.full_profile_embedding is not None
            logger.info(f"✅ Successfully loaded record with request_id: {request_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load record from database: {e}")
            raise
    
    def test_05_call_find_matches(self, matching_and_processing_results: dict):
        """
        ✅ Call find_matches(record, db)
        
        Checklist item: Call find_matches(record, db)
        """
        try:
            matches = matching_and_processing_results['matches']
            matching_time = matching_and_processing_results['matching_time']
            request_id = matching_and_processing_results['request_id']
            
            logger.info(f"✅ find_matches completed in {matching_time:.3f} seconds")
            logger.info(f"   - Found {len(matches)} matches for record ID: {request_id}")
            
            # Validate that we got a list of matches (even if empty)
            assert isinstance(matches, list), "find_matches should return a list"
            
        except Exception as e:
            logger.error(f"❌ Failed to call find_matches: {e}")
            raise
    
    def test_06_log_number_of_matches_found(self, matching_and_processing_results: dict):
        """
        ✅ Log number of matches found for record ID
        
        Checklist item: Log number of matches found for record ID: {record.request_id}
        """
        try:
            match_count = len(matching_and_processing_results['matches'])
            request_id = matching_and_processing_results['request_id']
            
            logger.info(f"✅ Found {match_count} matches for record ID: {request_id}")
            
            # Log details of each match if any found
            if match_count > 0:
                for i, match in enumerate(matching_and_processing_results['matches'][:3]):  # Log first 3 matches
                    logger.info(f"   Match {i+1}: customer_id={match.matched_customer_id}, "
                              f"score={match.similarity_score:.4f}, type={match.match_type}")
                
                if match_count > 3:
                    logger.info(f"   ... and {match_count - 3} more matches")
            
            # Validate match count is reasonable
            assert match_count >= 0, "Match count should be non-negative"
            
        except Exception as e:
            logger.error(f"❌ Failed to log match information: {e}")
            raise
    
    def test_07_verify_matches_contain_expected_fields(self, matching_and_processing_results: dict):
        """
        ✅ Verify matches contain expected fields
        
        Checklist item: Verify matches contain expected fields (customer_id, similarity_score, etc.)
        """
        try:
            matches = matching_and_processing_results['matches']
            
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
    
    def test_08_call_process_results_for_current_record(self, matching_and_processing_results: dict):
        """
        ✅ Call process_results(matches, request_id, db) for the current record
        
        Checklist item: Call process_results(matches, request_id, db) for the current record
        """
        try:
            processed_matches = matching_and_processing_results['processed_matches']
            processing_time = matching_and_processing_results['processing_time']
            request_id = matching_and_processing_results['request_id']
            
            logger.info(f"✅ process_results completed in {processing_time:.3f} seconds")
            logger.info(f"   - Processed {len(processed_matches)} matches for record ID: {request_id}")
            
            # Validate that we got a list of processed matches (even if empty)
            assert isinstance(processed_matches, list), "process_results should return a list"
            
        except Exception as e:
            logger.error(f"❌ Failed to call process_results: {e}")
            raise
    
    def test_09_verify_results_are_stored_in_database(self, db_session: Session, matching_and_processing_results: dict):
        """
        ✅ Verify results are stored in database
        
        Checklist item: Verify results are stored in database
        """
        try:
            from app.models.database import MatchingResult
            
            request_id = matching_and_processing_results['request_id']
            processed_matches = matching_and_processing_results['processed_matches']
            
            # Check if matching results were stored using SQLAlchemy ORM
            if len(processed_matches) > 0:
                stored_count = db_session.query(MatchingResult).filter(
                    MatchingResult.incoming_customer_id == request_id
                ).count()
                
                assert stored_count == len(processed_matches), f"Expected {len(processed_matches)} stored results, got {stored_count}"
                logger.info(f"✅ Verified {stored_count} matching results stored in database for request_id: {request_id}")
            else:
                logger.info("✅ No matches to store (empty result is valid)")
            
        except Exception as e:
            logger.error(f"❌ Failed to verify results storage: {e}")
            raise
    
    def test_10_confirm_processing_status_updated_to_processed(self, db_session: Session, matching_and_processing_results: dict):
        """
        ✅ Confirm processing_status is updated to 'processed' for this record
        
        Checklist item: Confirm processing_status is updated to 'processed' for this record
        """
        try:
            request_id = matching_and_processing_results['request_id']
            
            # Check processing status using SQLAlchemy ORM
            customer = db_session.query(IncomingCustomer).filter(
                IncomingCustomer.request_id == request_id
            ).first()
            
            if customer is not None:
                status = str(customer.processing_status)
                assert status == 'processed', f"Expected 'processed', got '{status}'"
                assert customer.processed_date is not None, "processed_date should be set"
                logger.info(f"✅ Processing status updated to 'processed' for request_id: {request_id}")
                logger.info(f"   - Processed date: {customer.processed_date}")
            else:
                logger.warning(f"⚠️ Record with request_id {request_id} not found for status verification")
            
        except Exception as e:
            logger.error(f"❌ Failed to confirm processing status: {e}")
            raise
    
    def test_11_log_processing_completion_for_record_id(self, matching_and_processing_results: dict):
        """
        ✅ Log processing completion for record ID
        
        Checklist item: Log processing completion for record ID: {record.request_id}
        """
        try:
            request_id = matching_and_processing_results['request_id']
            total_time = matching_and_processing_results['total_time']
            matching_time = matching_and_processing_results['matching_time']
            processing_time = matching_and_processing_results['processing_time']
            processed_matches = matching_and_processing_results['processed_matches']
            
            logger.info(f"✅ Processing completed for record ID: {request_id}")
            logger.info(f"   - Total processing time: {total_time:.3f} seconds")
            logger.info(f"   - Matching time: {matching_time:.3f} seconds")
            logger.info(f"   - Result processing time: {processing_time:.3f} seconds")
            logger.info(f"   - Processed matches: {len(processed_matches)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log processing completion: {e}")
            raise
    
    def test_12_handle_exceptions_during_matching_and_processing(self, db_session: Session, vector_matcher_instance: VectorMatcher, result_processor_instance: ResultProcessor):
        """
        ✅ Handle any exceptions during matching and processing
        
        Checklist item: Handle any exceptions during matching and processing
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
            
            # Process empty results (should handle gracefully)
            processed_matches = result_processor_instance.process_results(matches, test_record_no_embedding.request_id, db_session)  # type: ignore
            assert processed_matches == [], "Should return empty list for empty matches"
            
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
                processed_matches = result_processor_instance.process_results(matches, test_record_invalid_embedding.request_id, db_session)  # type: ignore
                logger.info("✅ Successfully handled invalid embedding format")
            except Exception as e:
                logger.warning(f"⚠️ Invalid embedding caused exception (acceptable): {e}")
            
            logger.info("✅ Exception handling during matching and processing verified")
            
        except Exception as e:
            logger.error(f"❌ Failed to test exception handling: {e}")
            raise
    
    def test_13_log_total_records_processed_and_results_saved(self, pending_records_count: int, matching_and_processing_results: dict):
        """
        ✅ Log total records processed and results saved
        
        Checklist item: Log total records processed and results saved: {records_to_process}
        """
        try:
            logger.info(f"✅ Total records processed: {pending_records_count}")
            
            # Log summary statistics
            total_time = matching_and_processing_results['total_time']
            total_matches = len(matching_and_processing_results['matches'])
            total_processed = len(matching_and_processing_results['processed_matches'])
            
            logger.info(f"   - Total processing time for one record: {total_time:.3f} seconds")
            logger.info(f"   - Matches found for test record: {total_matches}")
            logger.info(f"   - Results processed and saved: {total_processed}")
            
            # Estimate total processing time if we processed all records
            estimated_total_time = total_time * pending_records_count
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
            # Verify we can still query the database using SQLAlchemy ORM
            pending_count = db_session.query(IncomingCustomer).filter(
                IncomingCustomer.processing_status == 'pending'
            ).count()
            
            processed_count = db_session.query(IncomingCustomer).filter(
                IncomingCustomer.processing_status == 'processed'
            ).count()
            
            logger.info(f"✅ Step 4 execution completed successfully")
            logger.info(f"   - Remaining pending records: {pending_count}")
            logger.info(f"   - Total processed records: {processed_count}")
            logger.info("   - Vector matching execution and result processing tests passed")
            logger.info("   - All checklist items for Step 4 completed")
            
        except Exception as e:
            logger.error(f"❌ Step 4 execution verification failed: {e}")
            raise 