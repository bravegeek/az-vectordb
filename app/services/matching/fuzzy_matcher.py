"""Fuzzy string matching strategy for customer matching"""
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from app.core.config import settings
from app.models.database import Customer, IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema
from .base_matcher import BaseMatcher
from .utils import MatchingUtils

logger = logging.getLogger(__name__)


class FuzzyMatcher(BaseMatcher):
    """Handles fuzzy string matching for company names"""
    
    def is_enabled(self) -> bool:
        """Check if fuzzy matching is enabled"""
        return settings.enable_fuzzy_matching
    
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using fuzzy string matching"""
        if not self.is_enabled():
            return []
        
        if incoming_customer.company_name is None:
            return []
        
        matches = []
        customers = db.query(Customer).all()
        
        for customer in customers:
            company_similarity = self._calculate_company_similarity(
                incoming_customer.company_name, 
                customer.company_name
            )
            
            if company_similarity >= settings.fuzzy_similarity_threshold:
                match_type = self._determine_match_type(company_similarity)
                
                matches.append(MatchResultSchema(
                    match_id=0,
                    matched_customer_id=getattr(customer, 'customer_id'),
                    matched_company_name=getattr(customer, 'company_name'),
                    matched_contact_name=getattr(customer, 'contact_name'),
                    matched_email=getattr(customer, 'email'),
                    similarity_score=company_similarity,
                    match_type=match_type,
                    confidence_level=company_similarity,
                    match_criteria={"fuzzy_match": True, "company_similarity": company_similarity},
                    created_date=datetime.now()
                ))
        
        # Sort by similarity and limit results
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:settings.fuzzy_max_results]
    
    def _calculate_company_similarity(self, incoming_name: str, customer_name: str) -> float:
        """Calculate fuzzy similarity for company names"""
        if not customer_name:
            return 0.0
        
        return SequenceMatcher(
            None, 
            incoming_name.lower(), 
            customer_name.lower()
        ).ratio()
    
    def _determine_match_type(self, score: float) -> str:
        """Determine match type based on similarity score"""
        return MatchingUtils.determine_match_type(
            score, 
            settings.high_confidence_threshold,
            settings.default_similarity_threshold,
            settings.potential_match_threshold
        ) 