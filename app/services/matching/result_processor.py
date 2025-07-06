"""Result processing and storage for customer matching"""
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import MatchingResult, IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema

logger = logging.getLogger(__name__)


class ResultProcessor:
    """Handles processing and storage of matching results"""
    
    def deduplicate_matches(self, matches: List[MatchResultSchema]) -> List[MatchResultSchema]:
        """Remove duplicate matches based on customer_id"""
        seen_customers = set()
        unique_matches = []
        
        for match in matches:
            if match.matched_customer_id not in seen_customers:
                seen_customers.add(match.matched_customer_id)
                unique_matches.append(match)
        
        return unique_matches
    
    def sort_matches(self, matches: List[MatchResultSchema]) -> List[MatchResultSchema]:
        """Sort matches by confidence level in descending order"""
        return sorted(matches, key=lambda x: x.confidence_level, reverse=True)
    
    def store_matching_results(self, request_id: int, matches: List[MatchResultSchema], db: Session) -> bool:
        """Store matching results in database"""
        try:
            # Store matching results
            for match in matches:
                db_result = MatchingResult(
                    incoming_customer_id=request_id,
                    matched_customer_id=match.matched_customer_id,
                    similarity_score=match.similarity_score,
                    match_type=match.match_type,
                    match_criteria=match.match_criteria,
                    confidence_level=match.confidence_level
                )
                db.add(db_result)
            
            # Update incoming customer processing status
            self.update_processing_status(request_id, "processed", db)
            
            db.commit()
            logger.info(f"Stored {len(matches)} matching results for request_id {request_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing matching results: {e}")
            return False
    
    def process_results(self, matches: List[MatchResultSchema], request_id: int, db: Session) -> List[MatchResultSchema]:
        """Process and store matching results"""
        # Deduplicate matches
        unique_matches = self.deduplicate_matches(matches)
        
        # Sort by confidence
        sorted_matches = self.sort_matches(unique_matches)
        
        # Store in database (this will also update processing status)
        self.store_matching_results(request_id, sorted_matches, db)
        
        return sorted_matches
    
    def update_processing_status(self, request_id: int, status: str, db: Session) -> bool:
        """Update processing status for incoming customer"""
        try:
            incoming_customer = db.query(IncomingCustomer).filter(IncomingCustomer.request_id == request_id).first()
            if incoming_customer:
                setattr(incoming_customer, 'processing_status', status)
                if status == "processed":
                    setattr(incoming_customer, 'processed_date', datetime.now())
                logger.info(f"Updated processing status for request_id {request_id}: {status}")
                db.commit()
                return True
            else:
                logger.warning(f"Incoming customer with request_id {request_id} not found for status update")
                return False
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating processing status: {e}")
            return False 