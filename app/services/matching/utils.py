"""Utility functions for customer matching"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MatchingUtils:
    """Utility functions for customer matching operations"""
    
    @staticmethod
    def exact_match_company_name(customer_name: str, incoming_name: str) -> bool:
        """Check if company names match exactly"""
        if not customer_name or not incoming_name:
            return False
        return customer_name.strip() == incoming_name.strip()
    
    @staticmethod
    def exact_match_email(customer_email: str, incoming_email: str) -> bool:
        """Check if emails match exactly"""
        if not customer_email or not incoming_email:
            return False
        return customer_email.strip().lower() == incoming_email.strip().lower()
    
    @staticmethod
    def exact_match_phone(customer_phone: str, incoming_phone: str) -> bool:
        """Check if phone numbers match exactly"""
        if not customer_phone or not incoming_phone:
            return False
        return customer_phone.strip() == incoming_phone.strip()
    
    @staticmethod
    def calculate_exact_match_confidence(customer, incoming_customer) -> float:
        """Calculate confidence score for exact matches"""
        matches = 0
        total_fields = 0
        
        # Check company name
        if getattr(customer, 'company_name') and getattr(incoming_customer, 'company_name'):
            total_fields += 1
            if MatchingUtils.exact_match_company_name(
                getattr(customer, 'company_name'), 
                getattr(incoming_customer, 'company_name')
            ):
                matches += 1
        
        # Check email
        if getattr(customer, 'email') and getattr(incoming_customer, 'email'):
            total_fields += 1
            if MatchingUtils.exact_match_email(
                getattr(customer, 'email'), 
                getattr(incoming_customer, 'email')
            ):
                matches += 1
        
        # Check phone
        if getattr(customer, 'phone') and getattr(incoming_customer, 'phone'):
            total_fields += 1
            if MatchingUtils.exact_match_phone(
                getattr(customer, 'phone'), 
                getattr(incoming_customer, 'phone')
            ):
                matches += 1
        
        if total_fields == 0:
            return 0.0
        
        # Calculate confidence (0.8-1.0 for exact matches)
        base_confidence = matches / total_fields
        return 0.8 + (base_confidence * 0.2)  # Scale to 0.8-1.0 range
    
    @staticmethod
    def determine_match_type(score: float, high_threshold: float, default_threshold: float, potential_threshold: float) -> str:
        """Determine match type based on similarity score"""
        if score >= high_threshold:
            return "high_confidence"
        elif score >= default_threshold:
            return "potential"
        elif score >= potential_threshold:
            return "low_confidence"
        else:
            return "no_match" 