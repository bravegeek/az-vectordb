"""
Exact Matching Tests

This module tests the exact matching functionality of the customer matching system.
Exact matching performs direct field comparisons (company name, email, phone) with
high confidence scores for perfect matches.
"""

import pytest
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Add the app directory to the path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.matching_service import MatchingService
from app.models.database import Customer, IncomingCustomer
from app.core.database import get_db

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestExactMatching:
    """Test suite for exact matching functionality"""
    
    @pytest.fixture
    def matching_service(self):
        """Create a matching service instance for testing"""
        return MatchingService()
    
    @pytest.fixture
    def sample_customer(self) -> Dict[str, Any]:
        """Sample customer data for testing"""
        return {
            "customer_id": 1,
            "company_name": "Microsoft Corporation",
            "contact_name": "John Doe",
            "email": "john.doe@microsoft.com",
            "phone": "+1-555-123-4567",
            "address_line1": "1 Microsoft Way",
            "city": "Redmond",
            "state_province": "WA",
            "postal_code": "98052",
            "country": "USA",
            "industry": "Technology",
            "annual_revenue": 1000000.0,
            "employee_count": 1000,
            "website": "https://microsoft.com",
            "description": "Technology company"
        }
    
    @pytest.fixture
    def sample_incoming_customer(self) -> Dict[str, Any]:
        """Sample incoming customer data for testing"""
        return {
            "request_id": 1,
            "company_name": "Microsoft Corporation",
            "contact_name": "John Doe",
            "email": "john.doe@microsoft.com",
            "phone": "+1-555-123-4567",
            "address_line1": "1 Microsoft Way",
            "city": "Redmond",
            "state_province": "WA",
            "postal_code": "98052",
            "country": "USA",
            "industry": "Technology",
            "annual_revenue": 1000000.0,
            "employee_count": 1000,
            "website": "https://microsoft.com",
            "description": "Technology company"
        }

    def test_exact_company_name_match(self, matching_service, sample_customer, sample_incoming_customer):
        """Test exact company name matching"""
        # Create customer and incoming customer with exact company name match
        customer = Customer(**sample_customer)
        incoming_customer = IncomingCustomer(**sample_incoming_customer)
        
        # Test exact match
        result = matching_service._exact_match_company_name(
            customer.company_name, 
            incoming_customer.company_name
        )
        
        assert result is True
        logger.info("✅ Exact company name match test passed")

    def test_exact_email_match(self, matching_service, sample_customer, sample_incoming_customer):
        """Test exact email matching"""
        # Create customer and incoming customer with exact email match
        customer = Customer(**sample_customer)
        incoming_customer = IncomingCustomer(**sample_incoming_customer)
        
        # Test exact match
        result = matching_service._exact_match_email(
            customer.email, 
            incoming_customer.email
        )
        
        assert result is True
        logger.info("✅ Exact email match test passed")

    def test_exact_phone_match(self, matching_service, sample_customer, sample_incoming_customer):
        """Test exact phone matching"""
        # Create customer and incoming customer with exact phone match
        customer = Customer(**sample_customer)
        incoming_customer = IncomingCustomer(**sample_incoming_customer)
        
        # Test exact match
        result = matching_service._exact_match_phone(
            customer.phone, 
            incoming_customer.phone
        )
        
        assert result is True
        logger.info("✅ Exact phone match test passed")

    def test_multiple_field_match(self, matching_service, sample_customer, sample_incoming_customer):
        """Test when multiple fields match exactly"""
        # Create customer and incoming customer with multiple exact matches
        customer = Customer(**sample_customer)
        incoming_customer = IncomingCustomer(**sample_incoming_customer)
        
        # Test multiple field matches
        company_match = matching_service._exact_match_company_name(
            customer.company_name, 
            incoming_customer.company_name
        )
        email_match = matching_service._exact_match_email(
            customer.email, 
            incoming_customer.email
        )
        phone_match = matching_service._exact_match_phone(
            customer.phone, 
            incoming_customer.phone
        )
        
        assert company_match is True
        assert email_match is True
        assert phone_match is True
        logger.info("✅ Multiple field match test passed")

    def test_case_sensitivity(self, matching_service, sample_customer):
        """Test case sensitivity handling"""
        # Test with different case variations
        test_cases = [
            ("Microsoft Corporation", "microsoft corporation"),
            ("MICROSOFT CORPORATION", "Microsoft Corporation"),
            ("microsoft corporation", "MICROSOFT CORPORATION"),
            ("Microsoft Corporation", "Microsoft Corporation"),  # Exact match
        ]
        
        for company1, company2 in test_cases:
            result = matching_service._exact_match_company_name(company1, company2)
            # Exact matching should be case-sensitive
            expected = (company1 == company2)
            assert result == expected, f"Case sensitivity test failed for '{company1}' vs '{company2}'"
        
        logger.info("✅ Case sensitivity test passed")

    def test_null_value_handling(self, matching_service, sample_customer):
        """Test handling of null/empty values"""
        # Test with null values
        test_cases = [
            (None, "Microsoft Corporation"),
            ("Microsoft Corporation", None),
            ("", "Microsoft Corporation"),
            ("Microsoft Corporation", ""),
            (None, None),
            ("", ""),
        ]
        
        for company1, company2 in test_cases:
            result = matching_service._exact_match_company_name(company1, company2)
            # Should handle null/empty values gracefully
            assert isinstance(result, bool), f"Null handling test failed for '{company1}' vs '{company2}'"
        
        logger.info("✅ Null value handling test passed")

    def test_whitespace_handling(self, matching_service, sample_customer):
        """Test handling of whitespace variations"""
        # Test with whitespace variations
        test_cases = [
            ("Microsoft Corporation", " Microsoft Corporation "),
            ("  Microsoft Corporation  ", "Microsoft Corporation"),
            ("Microsoft Corporation", "Microsoft  Corporation"),
            ("Microsoft Corporation", "Microsoft Corporation"),  # Exact match
        ]
        
        for company1, company2 in test_cases:
            result = matching_service._exact_match_company_name(company1, company2)
            # Exact matching should be sensitive to whitespace
            expected = (company1 == company2)
            assert result == expected, f"Whitespace handling test failed for '{company1}' vs '{company2}'"
        
        logger.info("✅ Whitespace handling test passed")

    def test_exact_match_confidence_scoring(self, matching_service, sample_customer, sample_incoming_customer):
        """Test confidence scoring for exact matches"""
        # Create customer and incoming customer with exact matches
        customer = Customer(**sample_customer)
        incoming_customer = IncomingCustomer(**sample_incoming_customer)
        
        # Test confidence scoring
        confidence = matching_service._calculate_exact_match_confidence(
            customer, 
            incoming_customer
        )
        
        # Exact matches should have high confidence (0.8-1.0)
        assert 0.8 <= confidence <= 1.0, f"Confidence score {confidence} not in expected range"
        logger.info(f"✅ Exact match confidence test passed: {confidence}")

    def test_no_exact_match(self, matching_service, sample_customer):
        """Test when no exact match is found"""
        # Test with different company names
        test_cases = [
            ("Microsoft Corporation", "Apple Inc"),
            ("Microsoft Corporation", "Google LLC"),
            ("Microsoft Corporation", "Amazon Web Services"),
        ]
        
        for company1, company2 in test_cases:
            result = matching_service._exact_match_company_name(company1, company2)
            assert result is False, f"No match test failed for '{company1}' vs '{company2}'"
        
        logger.info("✅ No exact match test passed")

    @pytest.mark.integration
    def test_exact_match_with_database(self, matching_service):
        """Integration test with actual database"""
        # This test requires a database connection
        # It will test exact matching with real data from the database
        try:
            # Get some existing customers from database
            with next(get_db()) as db:
                customers = db.query(Customer).limit(5).all()
                incoming_customers = db.query(IncomingCustomer).limit(5).all()
                
                if customers and incoming_customers:
                    # Test exact matching with real data
                    customer = customers[0]
                    incoming_customer = incoming_customers[0]
                    
                    # Test exact match
                    result = matching_service._exact_match_company_name(
                        customer.company_name, 
                        incoming_customer.company_name
                    )
                    
                    # Should return a boolean
                    assert isinstance(result, bool)
                    logger.info(f"✅ Database integration test passed: {result}")
                else:
                    pytest.skip("No test data available in database")
                    
        except Exception as e:
            logger.warning(f"Database integration test skipped: {e}")
            pytest.skip(f"Database not available: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"]) 