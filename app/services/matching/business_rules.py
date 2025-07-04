"""Business rules engine for customer matching confidence calculation"""
import logging
from typing import Any

from app.core.config import settings
from app.models.database import IncomingCustomer

logger = logging.getLogger(__name__)


class BusinessRulesEngine:
    """Applies business rules to adjust confidence scores"""
    
    def apply_rules(self, base_score: float, incoming: IncomingCustomer, customer_row: Any) -> float:
        """Apply business rules to adjust confidence score"""
        confidence = base_score
        
        if not settings.enable_business_rules:
            return confidence
        
        # Industry match boost
        confidence = self._apply_industry_rule(confidence, incoming, customer_row)
        
        # Location match boost/penalty
        confidence = self._apply_location_rule(confidence, incoming, customer_row)
        
        # Revenue size boost
        confidence = self._apply_revenue_rule(confidence, incoming, customer_row)
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _apply_industry_rule(self, confidence: float, incoming: IncomingCustomer, customer_row: Any) -> float:
        """Apply industry match boost"""
        if (incoming.industry is not None and 
            hasattr(customer_row, 'industry') and 
            customer_row.industry is not None and 
            incoming.industry.lower() == customer_row.industry.lower()):
            confidence *= settings.industry_match_boost
        
        return confidence
    
    def _apply_location_rule(self, confidence: float, incoming: IncomingCustomer, customer_row: Any) -> float:
        """Apply location match boost or penalty"""
        if (incoming.country is not None and 
            hasattr(customer_row, 'country') and 
            customer_row.country is not None and 
            incoming.country.lower() == customer_row.country.lower()):
            confidence *= settings.location_match_boost
        else:
            # Country mismatch penalty
            confidence *= settings.country_mismatch_penalty
        
        return confidence
    
    def _apply_revenue_rule(self, confidence: float, incoming: IncomingCustomer, customer_row: Any) -> float:
        """Apply revenue size boost"""
        if not settings.revenue_size_boost:
            return confidence
        
        if (incoming.annual_revenue is not None and 
            hasattr(customer_row, 'annual_revenue') and 
            customer_row.annual_revenue is not None):
            
            try:
                incoming_revenue = float(incoming.annual_revenue)  # type: ignore
                customer_revenue = float(customer_row.annual_revenue)
                revenue_ratio = min(incoming_revenue, customer_revenue) / max(incoming_revenue, customer_revenue)
                
                if revenue_ratio > 0.8:  # Within 20% of each other
                    confidence *= 1.1
            except (ValueError, ZeroDivisionError):
                logger.warning("Error calculating revenue ratio for business rules")
        
        return confidence 