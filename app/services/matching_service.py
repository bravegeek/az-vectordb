"""Customer matching service for Customer Matching POC - DEPRECATED"""
# This file is deprecated. Use the new modular matching service in app/services/matching/
# The new service provides better separation of concerns and maintainability.

import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.database import IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema
from app.services.matching import MatchingService

logger = logging.getLogger(__name__)


class MatchingService:
    """DEPRECATED: Service for customer matching using multiple strategies"""
    
    def __init__(self):
        """Initialize the matching service"""
        logger.warning("Using deprecated MatchingService. Please use app.services.matching.MatchingService instead.")
        self._new_service = MatchingService()
    
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using the default hybrid approach"""
        return self._new_service.find_matches(incoming_customer, db)
    
    def find_matches_hybrid(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using hybrid approach (exact + vector + fuzzy)"""
        return self._new_service.find_matches_hybrid(incoming_customer, db)
    
    def find_exact_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using exact matching only"""
        return self._new_service.find_exact_matches(incoming_customer, db)
    
    # All private methods have been moved to the new modular service
    # This class now acts as a compatibility wrapper
    

    

    

# Global service instance (deprecated - use app.services.matching.matching_service instead)
matching_service = MatchingService() 