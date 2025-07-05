"""Main matching service that orchestrates different matching strategies"""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.database import IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema
from .exact_matcher import ExactMatcher
from .vector_matcher import VectorMatcher
from .fuzzy_matcher import FuzzyMatcher
from .result_processor import ResultProcessor

logger = logging.getLogger(__name__)


class MatchingService:
    """Main service for customer matching using multiple strategies"""
    
    def __init__(self):
        """Initialize the matching service with all matchers"""
        self.exact_matcher = ExactMatcher()
        self.vector_matcher = VectorMatcher()
        self.fuzzy_matcher = FuzzyMatcher()
        self.result_processor = ResultProcessor()
    
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using the default hybrid approach"""
        return self.find_matches_hybrid(incoming_customer, db)
    
    def find_matches_hybrid(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using hybrid approach (exact + vector + fuzzy)"""
        all_matches = []
        
        # 1. Exact matching (highest priority)
        exact_matches = self.exact_matcher.find_matches(incoming_customer, db)
        all_matches.extend(exact_matches)
        
        # 2. Vector similarity matching
        vector_matches = self.vector_matcher.find_matches(incoming_customer, db)
        all_matches.extend(vector_matches)
        
        # 3. Fuzzy matching
        fuzzy_matches = self.fuzzy_matcher.find_matches(incoming_customer, db)
        all_matches.extend(fuzzy_matches)
        
        # Process and store results
        processed_matches = self.result_processor.process_results(all_matches, incoming_customer.request_id, db)  # type: ignore
        
        # If no matches found, still update processing status
        if not processed_matches:
            request_id = getattr(incoming_customer, 'request_id')
            self.result_processor.update_processing_status(request_id, "processed", db)
        
        return processed_matches
    
    def find_exact_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using exact matching only"""
        matches = self.exact_matcher.find_matches(incoming_customer, db)
        processed_matches = self.result_processor.process_results(matches, getattr(incoming_customer, 'request_id'), db)  # type: ignore
        
        # If no matches found, still update processing status
        if not processed_matches:
            request_id = getattr(incoming_customer, 'request_id')
            self.result_processor.update_processing_status(request_id, "processed", db)
        
        return processed_matches
    
    def find_vector_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using vector matching only"""
        matches = self.vector_matcher.find_matches(incoming_customer, db)
        processed_matches = self.result_processor.process_results(matches, getattr(incoming_customer, 'request_id'), db)  # type: ignore
        
        # If no matches found, still update processing status
        if not processed_matches:
            request_id = getattr(incoming_customer, 'request_id')
            self.result_processor.update_processing_status(request_id, "processed", db)
        
        return processed_matches
    
    def find_fuzzy_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using fuzzy matching only"""
        matches = self.fuzzy_matcher.find_matches(incoming_customer, db)
        processed_matches = self.result_processor.process_results(matches, getattr(incoming_customer, 'request_id'), db)  # type: ignore
        
        # If no matches found, still update processing status
        if not processed_matches:
            request_id = getattr(incoming_customer, 'request_id')
            self.result_processor.update_processing_status(request_id, "processed", db)
        
        return processed_matches


# Global service instance
matching_service = MatchingService() 