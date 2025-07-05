"""Tests for the refactored matching service"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from app.services.matching import (
    MatchingService, 
    ExactMatcher, 
    VectorMatcher, 
    FuzzyMatcher,
    BusinessRulesEngine,
    ResultProcessor
)
from app.models.database import IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema


class TestRefactoredMatching:
    """Test the refactored matching service components"""
    
    def test_matching_service_initialization(self):
        """Test that the main matching service initializes correctly"""
        service = MatchingService()
        
        assert isinstance(service.exact_matcher, ExactMatcher)
        assert isinstance(service.vector_matcher, VectorMatcher)
        assert isinstance(service.fuzzy_matcher, FuzzyMatcher)
        assert isinstance(service.result_processor, ResultProcessor)
    
    def test_exact_matcher_initialization(self):
        """Test that exact matcher initializes correctly"""
        matcher = ExactMatcher()
        assert matcher is not None
    
    def test_vector_matcher_initialization(self):
        """Test that vector matcher initializes correctly"""
        matcher = VectorMatcher()
        assert matcher is not None
        assert isinstance(matcher.business_rules, BusinessRulesEngine)
    
    def test_fuzzy_matcher_initialization(self):
        """Test that fuzzy matcher initializes correctly"""
        matcher = FuzzyMatcher()
        assert matcher is not None
    
    def test_business_rules_engine_initialization(self):
        """Test that business rules engine initializes correctly"""
        engine = BusinessRulesEngine()
        assert engine is not None
    
    def test_result_processor_initialization(self):
        """Test that result processor initializes correctly"""
        processor = ResultProcessor()
        assert processor is not None
    
    def test_result_processor_deduplication(self):
        """Test that result processor correctly deduplicates matches"""
        processor = ResultProcessor()
        
        # Create test matches with duplicate customer_id
        match1 = MatchResultSchema(
            match_id=1,
            matched_customer_id=123,
            matched_company_name="Test Company",
            matched_contact_name="John Doe",
            matched_email="john@test.com",
            similarity_score=0.9,
            match_type="high_confidence",
            confidence_level=0.9,
            match_criteria={"exact_match": True},
            created_date=datetime.now()
        )
        
        match2 = MatchResultSchema(
            match_id=2,
            matched_customer_id=123,  # Same customer_id
            matched_company_name="Test Company",
            matched_contact_name="John Doe",
            matched_email="john@test.com",
            similarity_score=0.8,
            match_type="potential",
            confidence_level=0.8,
            match_criteria={"vector_similarity": True},
            created_date=datetime.now()
        )
        
        match3 = MatchResultSchema(
            match_id=3,
            matched_customer_id=456,  # Different customer_id
            matched_company_name="Another Company",
            matched_contact_name="Jane Smith",
            matched_email="jane@another.com",
            similarity_score=0.7,
            match_type="potential",
            confidence_level=0.7,
            match_criteria={"fuzzy_match": True},
            created_date=datetime.now()
        )
        
        matches = [match1, match2, match3]
        unique_matches = processor.deduplicate_matches(matches)
        
        # Should have 2 unique matches (customer_id 123 and 456)
        assert len(unique_matches) == 2
        assert unique_matches[0].matched_customer_id == 123
        assert unique_matches[1].matched_customer_id == 456
    
    def test_result_processor_sorting(self):
        """Test that result processor correctly sorts matches by confidence"""
        processor = ResultProcessor()
        
        # Create test matches with different confidence levels
        match1 = MatchResultSchema(
            match_id=1,
            matched_customer_id=123,
            matched_company_name="Test Company",
            matched_contact_name="John Doe",
            matched_email="john@test.com",
            similarity_score=0.7,
            match_type="potential",
            confidence_level=0.7,
            match_criteria={"fuzzy_match": True},
            created_date=datetime.now()
        )
        
        match2 = MatchResultSchema(
            match_id=2,
            matched_customer_id=456,
            matched_company_name="Another Company",
            matched_contact_name="Jane Smith",
            matched_email="jane@another.com",
            similarity_score=0.9,
            match_type="high_confidence",
            confidence_level=0.9,
            match_criteria={"exact_match": True},
            created_date=datetime.now()
        )
        
        match3 = MatchResultSchema(
            match_id=3,
            matched_customer_id=789,
            matched_company_name="Third Company",
            matched_contact_name="Bob Wilson",
            matched_email="bob@third.com",
            similarity_score=0.8,
            match_type="potential",
            confidence_level=0.8,
            match_criteria={"vector_similarity": True},
            created_date=datetime.now()
        )
        
        matches = [match1, match2, match3]  # Unsorted
        sorted_matches = processor.sort_matches(matches)
        
        # Should be sorted by confidence level (descending)
        assert len(sorted_matches) == 3
        assert sorted_matches[0].confidence_level == 0.9  # Highest
        assert sorted_matches[1].confidence_level == 0.8  # Middle
        assert sorted_matches[2].confidence_level == 0.7  # Lowest
    
    def test_business_rules_engine_returns_float(self):
        """Test that business rules engine returns a valid float value"""
        engine = BusinessRulesEngine()
        
        # Simple unit test - just verify the method returns a float
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
        
        # Should return a float between 0 and 1
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1 