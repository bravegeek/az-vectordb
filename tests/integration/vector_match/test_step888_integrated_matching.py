"""
Integration test for Step 4.01: Integrated Vector Matching and Result Processing.

This test implements Step 4.01 of the vector matching testing plan checklist.
It executes the integrated workflow where vector matching and result processing
happen together for each record in a streamlined approach.
"""

import pytest
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.database import IncomingCustomer, MatchingResult
from app.services.matching.vector_matcher import VectorMatcher
from app.services.matching.result_processor import ResultProcessor
from app.models.schemas import MatchResult as MatchResultSchema

logger = logging.getLogger(__name__)


class TestStep401IntegratedVectorMatching:
    """
    Step 4.01: Integrated Vector Matching and Result Processing
    
    This test implements the integrated workflow where matching and processing
    happen together for each record, following the simplified step 4.01 approach.
    """
    
    @pytest.fixture
    def vector_matcher(self) -> VectorMatcher:
        """Import and initialize VectorMatcher instance"""
        # ✅ Import vector_matcher module
        # ✅ Initialize VectorMatcher instance
        return VectorMatcher()
    
    @pytest.fixture
    def result_processor(self) -> ResultProcessor:
        """Import and initialize ResultProcessor instance"""
        # ✅ Import result_processor module
        # ✅ Initialize ResultProcessor instance
        return ResultProcessor()
    
    @pytest.fixture
    def pending_records_for_test(self, db_session_persistent: Session) -> List[IncomingCustomer]:
        """Query and hold pending records for the duration of the test"""
        # ✅ Query to get pending records: SELECT * FROM incoming_customers WHERE processing_status = 'pending' LIMIT 5
        # ✅ Hold these records for the duration of the test
        
        records = db_session_persistent.query(IncomingCustomer).filter(
            IncomingCustomer.processing_status == 'pending',
            IncomingCustomer.full_profile_embedding.isnot(None)
        ).limit(20).all()
        
        # Ensure records are properly loaded
        for record in records:
            db_session_persistent.refresh(record)
        
        logger.info(f"✅ Retrieved {len(records)} pending records for integrated processing")
        return records
    
    @pytest.fixture
    def processing_metrics(self) -> Dict[str, Any]:
        """Initialize metrics tracking dictionary"""
        return {
            'total_processed': 0,
            'total_matches_found': 0,
            'processing_times': [],
            'successful_records': [],
            'failed_records': [],
            'start_time': None,
            'end_time': None
        }
    
    @pytest.mark.integration
    def test_integrated_workflow_execution(
        self, 
        db_session_persistent: Session, 
        vector_matcher: VectorMatcher, 
        result_processor: ResultProcessor,
        pending_records_for_test: List[IncomingCustomer],
        processing_metrics: Dict[str, Any]
    ):
        """
        Execute the complete integrated workflow for Step 4.01
        
        This test processes each pending record through the complete workflow:
        1. Vector matching execution
        2. Result processing (integrated)
        3. Verification and logging
        """
        
        # Skip if vector matching is disabled
        if not vector_matcher.is_enabled():
            pytest.skip("Vector matching is disabled")
        
        # Skip if no pending records available
        if not pending_records_for_test:
            pytest.skip("No pending records with embeddings available for testing")
        
        processing_metrics['start_time'] = time.time()
        
        logger.info(f"🚀 Starting integrated workflow for {len(pending_records_for_test)} pending records")
        
        # ✅ For each pending record
        for record in pending_records_for_test:
            record_start_time = time.time()
            
            try:
                # Extract request_id
                request_id = getattr(record, 'request_id')
                
                # ✅ Call find_matches(record, db)
                matches = vector_matcher.find_matches(record, db_session_persistent)
                
                # ✅ Log number of matches found for record ID
                matches_count = len(matches)
                processing_metrics['total_matches_found'] += matches_count
                logger.info(f"📊 Found {matches_count} matches for record ID: {request_id}")
                
                # ✅ Result Processing (Integrated):
                # ✅ Call process_results(matches, request_id, db) for the current record
                processed_matches = result_processor.process_results(matches, request_id, db_session_persistent)
                
                # ✅ Verify results are stored in the table matching_results
                stored_results = db_session_persistent.query(MatchingResult).filter(
                    MatchingResult.incoming_customer_id == request_id
                ).all()
                
                assert len(stored_results) == len(processed_matches), \
                    f"Expected {len(processed_matches)} stored results, got {len(stored_results)} for record {request_id}"
                
                # ✅ Confirm processing_status is updated to 'processed' for this record
                db_session_persistent.refresh(record)
                updated_status = getattr(record, 'processing_status')
                assert updated_status == 'processed', \
                    f"Expected processing_status 'processed', got '{updated_status}' for record {request_id}"
                
                # ✅ Log processing completion for record ID
                record_processing_time = time.time() - record_start_time
                processing_metrics['processing_times'].append(record_processing_time)
                processing_metrics['successful_records'].append(request_id)
                processing_metrics['total_processed'] += 1
                
                logger.info(f"✅ Processing completed for record ID: {request_id} in {record_processing_time:.3f}s")
                
            except Exception as e:
                # ✅ Handle any exceptions during matching and processing
                processing_metrics['failed_records'].append({
                    'request_id': getattr(record, 'request_id', 'unknown'),
                    'error': str(e),
                    'timestamp': datetime.now()
                })
                logger.error(f"❌ Processing failed for record ID: {getattr(record, 'request_id', 'unknown')}: {e}")
                # Continue processing other records
                continue
        
        processing_metrics['end_time'] = time.time()
        
        # ✅ Log total records processed and results saved
        total_time = processing_metrics['end_time'] - processing_metrics['start_time']
        avg_time = sum(processing_metrics['processing_times']) / len(processing_metrics['processing_times']) if processing_metrics['processing_times'] else 0
        
        logger.info(f"🎯 INTEGRATED WORKFLOW SUMMARY:")
        logger.info(f"   - Total records processed: {processing_metrics['total_processed']}")
        logger.info(f"   - Total matches found: {processing_metrics['total_matches_found']}")
        logger.info(f"   - Total processing time: {total_time:.3f}s")
        logger.info(f"   - Average time per record: {avg_time:.3f}s")
        logger.info(f"   - Successful records: {processing_metrics['successful_records']}")
        
        if processing_metrics['failed_records']:
            logger.warning(f"   - Failed records: {len(processing_metrics['failed_records'])}")
            for failure in processing_metrics['failed_records']:
                logger.warning(f"     * {failure['request_id']}: {failure['error']}")
        
        # Verify at least one record was processed successfully
        assert processing_metrics['total_processed'] > 0, "No records were processed successfully"
        
        # Verify no more than expected failures
        failure_rate = len(processing_metrics['failed_records']) / len(pending_records_for_test)
        assert failure_rate < 0.5, f"Too many failures: {failure_rate:.2%} failure rate"
    