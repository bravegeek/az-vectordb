"""Customer matching service for Customer Matching POC"""
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, and_, or_
from difflib import SequenceMatcher

from app.core.config import settings
from app.models.database import Customer, IncomingCustomer, MatchingResult
from app.models.schemas import MatchResult as MatchResultSchema
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for customer matching using multiple strategies"""
    
    def __init__(self):
        """Initialize the matching service"""
        self.settings = settings
    
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using the default hybrid approach"""
        return self.find_matches_hybrid(incoming_customer, db)
    
    def find_matches_hybrid(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using hybrid approach (exact + vector + fuzzy)"""
        all_matches = []
        
        # 1. Exact matching (highest priority)
        if settings.enable_exact_matching:
            exact_matches = self._find_exact_matches(incoming_customer, db)
            all_matches.extend(exact_matches)
        
        # 2. Vector similarity matching
        if settings.enable_vector_matching:
            vector_matches = self._find_vector_matches(incoming_customer, db)
            all_matches.extend(vector_matches)
        
        # 3. Fuzzy matching
        if settings.enable_fuzzy_matching:
            fuzzy_matches = self._find_fuzzy_matches(incoming_customer, db)
            all_matches.extend(fuzzy_matches)
        
        # Sort by confidence level and remove duplicates
        unique_matches = self._deduplicate_matches(all_matches)
        sorted_matches = sorted(unique_matches, key=lambda x: x.confidence_level, reverse=True)
        
        # Store results in database
        self._store_matching_results(incoming_customer.request_id, sorted_matches, db)  # type: ignore
        
        return sorted_matches
    
    def find_exact_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using exact matching only"""
        matches = self._find_exact_matches(incoming_customer, db)
        
        # Store results in database
        self._store_matching_results(incoming_customer.request_id, matches, db)  # type: ignore
        
        return matches
    
    def _find_exact_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find exact matches based on company name, email, and phone"""
        matches = []
        
        # Build exact match criteria
        exact_criteria = {}
        
        if incoming_customer.company_name is not None:
            exact_criteria['company_name'] = incoming_customer.company_name.strip().lower()
        
        if incoming_customer.email is not None:
            exact_criteria['email'] = incoming_customer.email.strip().lower()
        
        if incoming_customer.phone is not None:
            exact_criteria['phone'] = incoming_customer.phone.strip()
        
        if not exact_criteria:
            return matches
        
        # Build query conditions
        conditions = []
        for field, value in exact_criteria.items():
            if field == 'company_name':
                conditions.append(Customer.company_name.ilike(f"%{value}%"))
            elif field == 'email':
                conditions.append(Customer.email.ilike(f"%{value}%"))
            elif field == 'phone':
                conditions.append(Customer.phone.ilike(f"%{value}%"))
        
        if not conditions:
            return matches
        
        # Query for exact matches
        exact_customers = db.query(Customer).filter(or_(*conditions)).all()
        
        for customer in exact_customers:
            # Calculate exact match score
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
    
    def _find_vector_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using vector similarity"""
        matches = []
        
        if incoming_customer.full_profile_embedding is None:
            return matches
        
        # Query for vector similarity matches
        query = text("""
            SELECT 
                customer_id, company_name, contact_name, email,
                1 - (full_profile_embedding <=> :query_embedding) as similarity_score
            FROM customer_data.customers 
            WHERE 1 - (full_profile_embedding <=> :query_embedding) > :threshold
            ORDER BY full_profile_embedding <=> :query_embedding
            LIMIT :max_results
        """)
        
        results = db.execute(
            query,
            {
                "query_embedding": incoming_customer.full_profile_embedding,
                "threshold": settings.vector_similarity_threshold,
                "max_results": settings.vector_max_results
            }
        ).fetchall()
        
        for row in results:
            similarity_score = float(row.similarity_score)
            match_type = self._determine_match_type(similarity_score)
            
            # Apply business rules for confidence calculation
            confidence = self._apply_business_rules(similarity_score, incoming_customer, row)
            
            matches.append(MatchResultSchema(
                match_id=0,
                matched_customer_id=row.customer_id,
                matched_company_name=row.company_name,
                matched_contact_name=row.contact_name,
                matched_email=row.email,
                similarity_score=similarity_score,
                match_type=match_type,
                confidence_level=confidence,
                match_criteria={"vector_similarity": True, "embedding_score": similarity_score},
                created_date=datetime.now()
            ))
        
        return matches
    
    def _find_fuzzy_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using fuzzy string matching"""
        matches = []
        
        if incoming_customer.company_name is None:
            return matches
        
        # Get all customers for fuzzy matching
        customers = db.query(Customer).all()
        
        for customer in customers:
            # Calculate fuzzy similarity for company name
            company_similarity = SequenceMatcher(
                None, 
                incoming_customer.company_name.lower(), 
                customer.company_name.lower()
            ).ratio()
            
            if company_similarity >= settings.fuzzy_similarity_threshold:
                match_type = self._determine_match_type(company_similarity)
                
                matches.append(MatchResultSchema(
                    match_id=0,
                    matched_customer_id=customer.customer_id,
                    matched_company_name=customer.company_name,
                    matched_contact_name=customer.contact_name,
                    matched_email=customer.email,
                    similarity_score=company_similarity,
                    match_type=match_type,
                    confidence_level=company_similarity,
                    match_criteria={"fuzzy_match": True, "company_similarity": company_similarity},
                    created_date=datetime.now()
                ))
        
        # Sort by similarity and limit results
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:settings.fuzzy_max_results]
    
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
        if score >= settings.high_confidence_threshold:
            return "high_confidence"
        elif score >= settings.default_similarity_threshold:
            return "potential"
        elif score >= settings.potential_match_threshold:
            return "low_confidence"
        else:
            return "no_match"
    
    def _apply_business_rules(self, base_score: float, incoming: IncomingCustomer, customer_row) -> float:
        """Apply business rules to adjust confidence score"""
        confidence = base_score
        
        if not settings.enable_business_rules:
            return confidence
        
        # Industry match boost
        if (incoming.industry is not None and hasattr(customer_row, 'industry') and 
            customer_row.industry is not None and 
            incoming.industry.lower() == customer_row.industry.lower()):
            confidence *= settings.industry_match_boost
        
        # Location match boost
        if (incoming.country is not None and hasattr(customer_row, 'country') and 
            customer_row.country is not None and 
            incoming.country.lower() == customer_row.country.lower()):
            confidence *= settings.location_match_boost
        else:
            # Country mismatch penalty
            confidence *= settings.country_mismatch_penalty
        
        # Revenue size boost
        if settings.revenue_size_boost:
            if (incoming.annual_revenue is not None and hasattr(customer_row, 'annual_revenue') and 
                customer_row.annual_revenue is not None):
                incoming_revenue = float(incoming.annual_revenue)  # type: ignore
                customer_revenue = float(customer_row.annual_revenue)
                revenue_ratio = min(incoming_revenue, customer_revenue) / max(incoming_revenue, customer_revenue)
                if revenue_ratio > 0.8:  # Within 20% of each other
                    confidence *= 1.1
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _deduplicate_matches(self, matches: List[MatchResultSchema]) -> List[MatchResultSchema]:
        """Remove duplicate matches based on customer_id"""
        seen_customers = set()
        unique_matches = []
        
        for match in matches:
            if match.matched_customer_id not in seen_customers:
                seen_customers.add(match.matched_customer_id)
                unique_matches.append(match)
        
        return unique_matches
    
    def _store_matching_results(self, request_id: int, matches: List[MatchResultSchema], db: Session):
        """Store matching results in database"""
        try:
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
            
            db.commit()
            logger.info(f"Stored {len(matches)} matching results for request_id {request_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing matching results: {e}")


# Global service instance
matching_service = MatchingService() 