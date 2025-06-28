"""Customer matching service with multiple strategies"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
import numpy as np

from models import Customer, IncomingCustomer, MatchingResult
from embedding_service import embedding_service
from config import settings

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for customer matching using multiple strategies"""
    
    def __init__(self):
        self.embedding_service = embedding_service
    
    def match_customer_hybrid(self, request_id: int, db: Session) -> List[Dict]:
        """Match customer using hybrid approach (exact + vector + fuzzy)"""
        try:
            # Get incoming customer
            incoming_customer = db.query(IncomingCustomer).filter(
                IncomingCustomer.request_id == request_id
            ).first()
            
            if not incoming_customer:
                raise ValueError(f"Incoming customer with ID {request_id} not found")
            
            matches = []
            
            # Step 1: Exact matching (highest priority)
            if settings.enable_exact_matching:
                exact_matches = self._find_exact_matches(incoming_customer, db)
                matches.extend(exact_matches)
                logger.info(f"Found {len(exact_matches)} exact matches for request {request_id}")
            
            # Step 2: Vector similarity matching
            if settings.enable_vector_matching and not matches:
                vector_matches = self._find_vector_matches(incoming_customer, db)
                matches.extend(vector_matches)
                logger.info(f"Found {len(vector_matches)} vector matches for request {request_id}")
            
            # Step 3: Fuzzy string matching
            if settings.enable_fuzzy_matching and not matches:
                fuzzy_matches = self._find_fuzzy_matches(incoming_customer, db)
                matches.extend(fuzzy_matches)
                logger.info(f"Found {len(fuzzy_matches)} fuzzy matches for request {request_id}")
            
            # Step 4: Apply business rules
            if settings.enable_business_rules:
                matches = self._apply_business_rules(incoming_customer, matches, db)
            
            # Step 5: Save matches to database
            self._save_matches(request_id, matches, db)
            
            # Step 6: Update processing status
            setattr(incoming_customer, 'processing_status', 'processed')
            setattr(incoming_customer, 'processed_date', datetime.now())
            db.commit()
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in hybrid matching: {e}")
            db.rollback()
            raise
    
    def match_customer_exact(self, request_id: int, db: Session) -> List[Dict]:
        """Match customer using only exact field matching"""
        try:
            incoming_customer = db.query(IncomingCustomer).filter(
                IncomingCustomer.request_id == request_id
            ).first()
            
            if not incoming_customer:
                raise ValueError(f"Incoming customer with ID {request_id} not found")
            
            matches = self._find_exact_matches(incoming_customer, db)
            self._save_matches(request_id, matches, db)
            
            # Update processing status
            setattr(incoming_customer, 'processing_status', 'processed')
            setattr(incoming_customer, 'processed_date', datetime.now())
            db.commit()
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in exact matching: {e}")
            db.rollback()
            raise
    
    def match_customer_vector(self, request_id: int, db: Session) -> List[Dict]:
        """Match customer using only vector similarity"""
        try:
            incoming_customer = db.query(IncomingCustomer).filter(
                IncomingCustomer.request_id == request_id
            ).first()
            
            if not incoming_customer:
                raise ValueError(f"Incoming customer with ID {request_id} not found")
            
            matches = self._find_vector_matches(incoming_customer, db)
            self._save_matches(request_id, matches, db)
            
            # Update processing status
            setattr(incoming_customer, 'processing_status', 'processed')
            setattr(incoming_customer, 'processed_date', datetime.now())
            db.commit()
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in vector matching: {e}")
            db.rollback()
            raise
    
    def _find_exact_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[Dict]:
        """Find exact matches based on key fields"""
        matches = []
        
        # Build query for exact matches
        query = db.query(Customer)
        conditions = []
        
        # Company name exact match (case insensitive)
        if getattr(incoming_customer, 'company_name', None):
            conditions.append(Customer.company_name.ilike(getattr(incoming_customer, 'company_name')))
        
        # Email exact match (case insensitive)
        if getattr(incoming_customer, 'email', None):
            conditions.append(Customer.email.ilike(getattr(incoming_customer, 'email')))
        
        if conditions:
            # Use OR logic for exact matches
            from sqlalchemy import or_
            query = query.filter(or_(*conditions))
            
            exact_customers = query.all()
            
            for customer in exact_customers:
                match_score = 0.0
                match_criteria = {}
                
                # Calculate match score
                incoming_company = getattr(incoming_customer, 'company_name', None)
                customer_company = getattr(customer, 'company_name', None)
                if (incoming_company and customer_company and 
                    customer_company.lower() == incoming_company.lower()):
                    match_score += settings.exact_company_name_weight
                    match_criteria['exact_company_name'] = True
                
                incoming_email = getattr(incoming_customer, 'email', None)
                customer_email = getattr(customer, 'email', None)
                if (incoming_email and customer_email and 
                    customer_email.lower() == incoming_email.lower()):
                    match_score += settings.exact_email_weight
                    match_criteria['exact_email'] = True
                
                incoming_phone = getattr(incoming_customer, 'phone', None)
                customer_phone = getattr(customer, 'phone', None)
                if (incoming_phone and customer_phone and
                    self._normalize_phone(incoming_phone) == self._normalize_phone(customer_phone)):
                    match_score += settings.exact_phone_weight
                    match_criteria['exact_phone'] = True
                
                if match_score >= settings.exact_match_min_score:
                    matches.append({
                        'customer_id': getattr(customer, 'customer_id'),
                        'company_name': getattr(customer, 'company_name'),
                        'contact_name': getattr(customer, 'contact_name'),
                        'email': getattr(customer, 'email'),
                        'similarity_score': match_score,
                        'match_type': 'exact',
                        'confidence_level': match_score,
                        'match_criteria': match_criteria,
                        'match_method': 'exact_fields'
                    })
        
        return matches
    
    def _find_vector_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[Dict]:
        """Find matches using vector similarity"""
        matches = []
        
        profile_embedding = getattr(incoming_customer, 'full_profile_embedding', None)
        if not profile_embedding:
            logger.warning("No profile embedding available for vector matching")
            return matches
        
        # Use PostgreSQL function for vector similarity search
        result = db.execute(
            text("""
                SELECT * FROM customer_data.find_similar_customers(
                    :query_embedding::vector,
                    :threshold,
                    :max_results
                )
            """),
            {
                "query_embedding": profile_embedding,
                "threshold": settings.vector_similarity_threshold,
                "max_results": settings.vector_max_results
            }
        )
        
        for row in result:
            # Determine match type based on similarity score
            if row.similarity_score >= settings.exact_match_threshold:
                match_type = 'exact'
            elif row.similarity_score >= settings.high_confidence_threshold:
                match_type = 'high_confidence'
            elif row.similarity_score >= settings.potential_match_threshold:
                match_type = 'potential'
            else:
                match_type = 'low_confidence'
            
            matches.append({
                'customer_id': row.customer_id,
                'company_name': row.company_name,
                'contact_name': row.contact_name,
                'email': row.email,
                'similarity_score': float(row.similarity_score),
                'match_type': match_type,
                'confidence_level': float(row.similarity_score),
                'match_criteria': {
                    'vector_similarity': float(row.similarity_score),
                    'matched_company': row.company_name,
                    'matched_contact': row.contact_name
                },
                'match_method': 'vector_similarity'
            })
        
        return matches
    
    def _find_fuzzy_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[Dict]:
        """Find matches using fuzzy string matching"""
        matches = []
        
        company_name = getattr(incoming_customer, 'company_name', None)
        if not company_name:
            return matches
        
        contact_name = getattr(incoming_customer, 'contact_name', None) or ''
        
        # Use PostgreSQL similarity function
        result = db.execute(
            text("""
                SELECT 
                    customer_id,
                    company_name,
                    contact_name,
                    email,
                    GREATEST(
                        similarity(LOWER(company_name), LOWER(:company_name)),
                        similarity(LOWER(COALESCE(contact_name, '')), LOWER(COALESCE(:contact_name, '')))
                    ) as similarity_score
                FROM customer_data.customers
                WHERE similarity(LOWER(company_name), LOWER(:company_name)) >= :threshold
                ORDER BY similarity_score DESC
                LIMIT :max_results
            """),
            {
                "company_name": company_name,
                "contact_name": contact_name,
                "threshold": settings.fuzzy_similarity_threshold,
                "max_results": settings.fuzzy_max_results
            }
        )
        
        for row in result:
            matches.append({
                'customer_id': row.customer_id,
                'company_name': row.company_name,
                'contact_name': row.contact_name,
                'email': row.email,
                'similarity_score': float(row.similarity_score),
                'match_type': 'potential',
                'confidence_level': float(row.similarity_score),
                'match_criteria': {
                    'fuzzy_company_name': True,
                    'similarity_score': float(row.similarity_score)
                },
                'match_method': 'fuzzy_string'
            })
        
        return matches
    
    def _apply_business_rules(self, incoming_customer: IncomingCustomer, matches: List[Dict], db: Session) -> List[Dict]:
        """Apply business rules to adjust confidence levels"""
        for match in matches:
            # Get the matched customer details
            customer = db.query(Customer).filter(Customer.customer_id == match['customer_id']).first()
            if not customer:
                continue
            
            # Industry match boost
            incoming_industry = getattr(incoming_customer, 'industry', None)
            customer_industry = getattr(customer, 'industry', None)
            if (incoming_industry and customer_industry and
                incoming_industry.lower() == customer_industry.lower()):
                match['confidence_level'] *= settings.industry_match_boost
                match['match_criteria']['industry_match'] = True
            
            # Location match boost
            incoming_city = getattr(incoming_customer, 'city', None)
            customer_city = getattr(customer, 'city', None)
            if (incoming_city and customer_city and
                incoming_city.lower() == customer_city.lower()):
                match['confidence_level'] *= settings.location_match_boost
                match['match_criteria']['location_match'] = True
            
            # Country mismatch penalty
            incoming_country = getattr(incoming_customer, 'country', None)
            customer_country = getattr(customer, 'country', None)
            if (incoming_country and customer_country and
                incoming_country.lower() != customer_country.lower()):
                match['confidence_level'] *= settings.country_mismatch_penalty
                match['match_criteria']['country_mismatch'] = True
            
            # Revenue size similarity boost
            if settings.revenue_size_boost:
                incoming_revenue = getattr(incoming_customer, 'annual_revenue', None)
                customer_revenue = getattr(customer, 'annual_revenue', None)
                if incoming_revenue and customer_revenue:
                    revenue_ratio = min(incoming_revenue, customer_revenue) / max(incoming_revenue, customer_revenue)
                    if revenue_ratio > 0.8:  # Similar revenue size
                        match['confidence_level'] *= 1.1
                        match['match_criteria']['revenue_similar'] = True
        
        return matches
    
    def _save_matches(self, request_id: int, matches: List[Dict], db: Session):
        """Save matches to the database"""
        for match_data in matches:
            match_result = MatchingResult(
                incoming_customer_id=request_id,
                matched_customer_id=match_data['customer_id'],
                similarity_score=match_data['similarity_score'],
                match_type=match_data['match_type'],
                confidence_level=match_data['confidence_level'],
                match_criteria=match_data['match_criteria']
            )
            db.add(match_result)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number by removing non-digits"""
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, phone))


# Global matching service instance
matching_service = MatchingService() 