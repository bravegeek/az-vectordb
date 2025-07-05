"""Integration tests for processing status updates in customer matching"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import IncomingCustomer
from app.services.matching.matching_service import MatchingService


class TestProcessingStatusUpdates:
    """Test class for processing status update functionality"""

    def test_processing_status_updates(self, db_session: Session):
        """Test that processing status is updated when customers are processed"""
        matching_service = MatchingService()
        
        # Get a few incoming customers that haven't been processed yet
        pending_customers = db_session.query(IncomingCustomer).filter(
            IncomingCustomer.processing_status == "pending"
        ).limit(3).all()
        
        if not pending_customers:
            # Create a test customer if none exist
            test_customer = IncomingCustomer(
                company_name="Test Company for Processing Status",
                contact_name="Test Contact",
                email="test@example.com",
                phone="+1-555-123-4567",
                processing_status="pending"
            )
            db_session.add(test_customer)
            db_session.commit()
            db_session.refresh(test_customer)
            pending_customers = [test_customer]
        
        for customer in pending_customers:
            request_id = getattr(customer, 'request_id')
            initial_status = getattr(customer, 'processing_status', 'unknown')
            initial_processed_date = getattr(customer, 'processed_date', None)
            
            # Process the customer
            matches = matching_service.find_matches(customer, db_session)
            
            # Refresh the customer to get updated status
            db_session.refresh(customer)
            
            final_status = getattr(customer, 'processing_status', 'unknown')
            final_processed_date = getattr(customer, 'processed_date', None)
            
            # Verify the status was updated
            assert final_status == "processed", f"Status not updated correctly. Expected 'processed', got '{final_status}'"
            assert final_processed_date is not None, "Processed date not set"
            
            # Verify the processed date is recent (within 1 minute)
            time_diff = datetime.now() - final_processed_date
            assert time_diff.total_seconds() < 60, f"Processed date seems old ({time_diff.total_seconds():.1f}s ago)"

    def test_no_matches_scenario(self, db_session: Session):
        """Test that processing status is updated even when no matches are found"""
        matching_service = MatchingService()
        
        # Create a customer with a very unique name that likely won't match
        unique_customer = IncomingCustomer(
            company_name="VeryUniqueCompanyNameThatWontMatch12345",
            contact_name="Unique Contact",
            email="unique@veryuniquecompany.com",
            phone="+1-555-999-9999",
            processing_status="pending"
        )
        db_session.add(unique_customer)
        db_session.commit()
        db_session.refresh(unique_customer)
        
        request_id = getattr(unique_customer, 'request_id')
        
        # Process the customer
        matches = matching_service.find_matches(unique_customer, db_session)
        
        # Refresh to get updated status
        db_session.refresh(unique_customer)
        
        final_status = getattr(unique_customer, 'processing_status', 'unknown')
        final_processed_date = getattr(unique_customer, 'processed_date', None)
        
        # Verify status was updated even with no matches
        assert final_status == "processed", f"Status not updated correctly. Expected 'processed', got '{final_status}'"
        assert final_processed_date is not None, "Processed date not set"
        
        # Verify the processed date is recent
        time_diff = datetime.now() - final_processed_date
        assert time_diff.total_seconds() < 60, f"Processed date seems old ({time_diff.total_seconds():.1f}s ago)"

    def test_processing_status_transition(self, db_session: Session):
        """Test the complete processing status transition from pending to processed"""
        matching_service = MatchingService()
        
        # Create a customer with pending status
        test_customer = IncomingCustomer(
            company_name="Status Transition Test Company",
            contact_name="Transition Contact",
            email="transition@testcompany.com",
            phone="+1-555-111-2222",
            processing_status="pending"
        )
        db_session.add(test_customer)
        db_session.commit()
        db_session.refresh(test_customer)
        
        # Verify initial state
        assert test_customer.processing_status == "pending"
        assert test_customer.processed_date is None
        
        # Process the customer
        matches = matching_service.find_matches(test_customer, db_session)
        
        # Refresh to get updated state
        db_session.refresh(test_customer)
        
        # Verify final state
        assert test_customer.processing_status == "processed"
        assert test_customer.processed_date is not None
        
        # Verify processed date is recent
        time_diff = datetime.now() - test_customer.processed_date
        assert time_diff.total_seconds() < 60

    def test_multiple_customers_processing(self, db_session: Session):
        """Test processing multiple customers and verify all status updates"""
        matching_service = MatchingService()
        
        # Create multiple test customers
        test_customers = []
        for i in range(3):
            customer = IncomingCustomer(
                company_name=f"Multi Test Company {i}",
                contact_name=f"Contact {i}",
                email=f"contact{i}@testcompany.com",
                phone=f"+1-555-{100+i:03d}-{200+i:04d}",
                processing_status="pending"
            )
            test_customers.append(customer)
            db_session.add(customer)
        
        db_session.commit()
        
        # Process all customers
        for customer in test_customers:
            db_session.refresh(customer)
            matches = matching_service.find_matches(customer, db_session)
            db_session.refresh(customer)
            
            # Verify each customer was processed
            assert customer.processing_status == "processed"
            assert customer.processed_date is not None
            
            # Verify processed date is recent
            time_diff = datetime.now() - customer.processed_date
            assert time_diff.total_seconds() < 60

    def test_processing_status_persistence(self, db_session: Session):
        """Test that processing status persists after database operations"""
        matching_service = MatchingService()
        
        # Create and process a customer
        test_customer = IncomingCustomer(
            company_name="Persistence Test Company",
            contact_name="Persistence Contact",
            email="persistence@testcompany.com",
            phone="+1-555-333-4444",
            processing_status="pending"
        )
        db_session.add(test_customer)
        db_session.commit()
        db_session.refresh(test_customer)
        
        # Process the customer
        matches = matching_service.find_matches(test_customer, db_session)
        db_session.refresh(test_customer)
        
        # Verify status was updated
        assert test_customer.processing_status == "processed"
        assert test_customer.processed_date is not None
        
        # Query the customer again to verify persistence
        persisted_customer = db_session.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == test_customer.request_id
        ).first()
        
        assert persisted_customer is not None
        assert persisted_customer.processing_status == "processed"
        assert persisted_customer.processed_date is not None
        assert persisted_customer.processed_date == test_customer.processed_date 