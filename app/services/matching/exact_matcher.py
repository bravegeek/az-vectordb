"""Exact matching strategy for customer matching"""
import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.models.database import Customer, IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema
from .base_matcher import BaseMatcher
from .utils import MatchingUtils

logger = logging.getLogger(__name__)


class ExactMatcher(BaseMatcher):
    """Handles exact matching based on company name, email, and phone"""
    
    def is_enabled(self) -> bool:
        """Check if exact matching is enabled"""
        return settings.enable_exact_matching
    
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find exact matches based on company name, email, and phone"""
        if not self.is_enabled():
            return []
        
        matches = []
        exact_criteria = self._build_exact_criteria(incoming_customer)
        
        if not exact_criteria:
            return matches
        
        conditions = self._build_query_conditions(exact_criteria)
        if not conditions:
            return matches
        
        # Query for exact matches
        exact_customers = db.query(Customer).filter(or_(*conditions)).all()
        
        for customer in exact_customers:
            score = self._calculate_exact_match_score(incoming_customer, customer, exact_criteria)
            
            if score >= settings.exact_match_min_score:
                match_type = self._determine_match_type(score)
                confidence = min(score * 1.2, 1.0)  # Boost confidence for exact matches
                
                matches.append(MatchResultSchema(
                    match_id=0,  # Will be set by database
                    matched_customer_id=customer.customer_id,  # type: ignore
                    matched_company_name=customer.company_name,  # type: ignore
                    matched_contact_name=customer.contact_name,  # type: ignore
                    matched_email=customer.email,  # type: ignore
                    similarity_score=score,
                    match_type=match_type,
                    confidence_level=confidence,
                    match_criteria={"exact_match": True, "matched_fields": list(exact_criteria.keys())},
                    created_date=datetime.now()
                ))
        
        return matches
    
    def _build_exact_criteria(self, incoming_customer: IncomingCustomer) -> Dict[str, str]:
        """Build exact match criteria from incoming customer data"""
        exact_criteria = {}
        
        if incoming_customer.company_name is not None:
            exact_criteria['company_name'] = incoming_customer.company_name.strip().lower()
        
        if incoming_customer.email is not None:
            exact_criteria['email'] = incoming_customer.email.strip().lower()
        
        if incoming_customer.phone is not None:
            exact_criteria['phone'] = incoming_customer.phone.strip()
        
        return exact_criteria
    
    def _build_query_conditions(self, exact_criteria: Dict[str, str]) -> List:
        """Build SQLAlchemy query conditions for exact matching"""
        conditions = []
        
        for field, value in exact_criteria.items():
            if field == 'company_name':
                conditions.append(Customer.company_name.ilike(f"%{value}%"))
            elif field == 'email':
                conditions.append(Customer.email.ilike(f"%{value}%"))
            elif field == 'phone':
                conditions.append(Customer.phone.ilike(f"%{value}%"))
        
        return conditions
    
    def _calculate_exact_match_score(self, incoming: IncomingCustomer, customer: Customer, criteria: Dict[str, str]) -> float:
        """Calculate exact match score based on matched fields"""
        total_score = 0.0
        total_weight = 0.0
        
        # Company name matching
        if 'company_name' in criteria:
            incoming_name = criteria['company_name']
            customer_name = customer.company_name.lower() if customer.company_name is not None else ""
            
            if incoming_name in customer_name or customer_name in incoming_name:
                total_score += settings.exact_company_name_weight
            total_weight += settings.exact_company_name_weight
        
        # Email matching
        if 'email' in criteria:
            incoming_email = criteria['email']
            customer_email = customer.email.lower() if customer.email is not None else ""
            
            if incoming_email == customer_email:
                total_score += settings.exact_email_weight
            total_weight += settings.exact_email_weight
        
        # Phone matching
        if 'phone' in criteria:
            incoming_phone = criteria['phone']
            customer_phone = customer.phone if customer.phone is not None else ""
            
            if incoming_phone == customer_phone:
                total_score += settings.exact_phone_weight
            total_weight += settings.exact_phone_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_match_type(self, score: float) -> str:
        """Determine match type based on similarity score"""
        return MatchingUtils.determine_match_type(
            score, 
            settings.high_confidence_threshold,
            settings.default_similarity_threshold,
            settings.potential_match_threshold
        ) 