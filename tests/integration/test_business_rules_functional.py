"""Functional tests for business rules engine - testing complete business scenarios"""
import pytest
from unittest.mock import Mock
from datetime import datetime

from app.services.matching import BusinessRulesEngine
from app.models.database import IncomingCustomer, Customer


class TestBusinessRulesEngineFunctional:
    """Functional tests for business rules engine - testing complete business scenarios"""
    
    def test_business_rules_engine_basic_scenario(self):
        """Test basic business rules scenario with no matches"""
        engine = BusinessRulesEngine()
        
        # Mock settings for realistic business configuration
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.core.config.settings.enable_business_rules", True)
            m.setattr("app.core.config.settings.industry_match_boost", 1.1)
            m.setattr("app.core.config.settings.location_match_boost", 1.05)
            m.setattr("app.core.config.settings.country_mismatch_penalty", 0.9)
            m.setattr("app.core.config.settings.revenue_size_boost", False)
            
            # Test basic confidence calculation with realistic data
            base_score = 0.8
            incoming_customer = Mock()
            incoming_customer.industry = None
            incoming_customer.country = None
            incoming_customer.annual_revenue = None
            
            customer_row = Mock()
            customer_row.industry = None
            customer_row.country = None
            customer_row.annual_revenue = None
            
            confidence = engine.apply_rules(base_score, incoming_customer, customer_row)
            
            # Should return a value between 0 and 1
            assert 0 <= confidence <= 1
            assert confidence == pytest.approx(0.72)  # 0.8 * 0.9 (country mismatch penalty)
    
    def test_business_rules_engine_industry_match_scenario(self):
        """Test business rules scenario with industry match boost"""
        engine = BusinessRulesEngine()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.core.config.settings.enable_business_rules", True)
            m.setattr("app.core.config.settings.industry_match_boost", 1.1)
            m.setattr("app.core.config.settings.location_match_boost", 1.05)
            m.setattr("app.core.config.settings.country_mismatch_penalty", 0.9)
            m.setattr("app.core.config.settings.revenue_size_boost", False)
            
            base_score = 0.8
            incoming_customer = Mock()
            incoming_customer.industry = "Technology"
            incoming_customer.country = None
            incoming_customer.annual_revenue = None
            
            customer_row = Mock()
            customer_row.industry = "Technology"
            customer_row.country = None
            customer_row.annual_revenue = None
            
            confidence = engine.apply_rules(base_score, incoming_customer, customer_row)
            
            # Should apply industry boost: 0.8 * 1.1 * 0.9 = 0.792
            assert confidence == pytest.approx(0.792)
    
    def test_business_rules_engine_country_match_scenario(self):
        """Test business rules scenario with country match boost"""
        engine = BusinessRulesEngine()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.core.config.settings.enable_business_rules", True)
            m.setattr("app.core.config.settings.industry_match_boost", 1.1)
            m.setattr("app.core.config.settings.location_match_boost", 1.05)
            m.setattr("app.core.config.settings.country_mismatch_penalty", 0.9)
            m.setattr("app.core.config.settings.revenue_size_boost", False)
            
            base_score = 0.8
            incoming_customer = Mock()
            incoming_customer.industry = None
            incoming_customer.country = "USA"
            incoming_customer.annual_revenue = None
            
            customer_row = Mock()
            customer_row.industry = None
            customer_row.country = "USA"
            customer_row.annual_revenue = None
            
            confidence = engine.apply_rules(base_score, incoming_customer, customer_row)
            
            # Should apply country boost: 0.8 * 1.05 = 0.84
            assert confidence == pytest.approx(0.84)
    
    def test_business_rules_engine_disabled_scenario(self):
        """Test business rules scenario when rules are disabled"""
        engine = BusinessRulesEngine()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.core.config.settings.enable_business_rules", False)
            
            base_score = 0.8
            incoming_customer = Mock()
            customer_row = Mock()
            
            confidence = engine.apply_rules(base_score, incoming_customer, customer_row)
            
            # Should return base score unchanged
            assert confidence == pytest.approx(0.8)
    
    def test_business_rules_engine_complete_match_scenario(self):
        """Test business rules scenario with all matches (industry, country, revenue)"""
        engine = BusinessRulesEngine()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.core.config.settings.enable_business_rules", True)
            m.setattr("app.core.config.settings.industry_match_boost", 1.1)
            m.setattr("app.core.config.settings.location_match_boost", 1.05)
            m.setattr("app.core.config.settings.country_mismatch_penalty", 0.9)
            m.setattr("app.core.config.settings.revenue_size_boost", True)
            
            base_score = 0.8
            incoming_customer = Mock()
            incoming_customer.industry = "Technology"
            incoming_customer.country = "USA"
            incoming_customer.annual_revenue = "1000000"
            
            customer_row = Mock()
            customer_row.industry = "Technology"
            customer_row.country = "USA"
            customer_row.annual_revenue = "950000"
            
            confidence = engine.apply_rules(base_score, incoming_customer, customer_row)
            
            # Should apply all boosts: 0.8 * 1.1 * 1.05 * 1.1 = 1.0164, capped at 1.0
            assert confidence == pytest.approx(1.0)
    
    def test_business_rules_engine_revenue_mismatch_scenario(self):
        """Test business rules scenario with revenue mismatch (no boost)"""
        engine = BusinessRulesEngine()
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr("app.core.config.settings.enable_business_rules", True)
            m.setattr("app.core.config.settings.industry_match_boost", 1.1)
            m.setattr("app.core.config.settings.location_match_boost", 1.05)
            m.setattr("app.core.config.settings.country_mismatch_penalty", 0.9)
            m.setattr("app.core.config.settings.revenue_size_boost", True)
            
            base_score = 0.8
            incoming_customer = Mock()
            incoming_customer.industry = "Technology"
            incoming_customer.country = "USA"
            incoming_customer.annual_revenue = "1000000"
            
            customer_row = Mock()
            customer_row.industry = "Technology"
            customer_row.country = "USA"
            customer_row.annual_revenue = "500000"  # 50% difference - no boost
            
            confidence = engine.apply_rules(base_score, incoming_customer, customer_row)
            
            # Should apply industry and country boosts but no revenue boost: 0.8 * 1.1 * 1.05 = 0.924
            assert confidence == pytest.approx(0.924) 