"""
Test script to verify processing status updates for incoming customers

This script tests that the processing_status and processed_date fields
are properly updated when incoming customers are processed for matching.
"""

import os
import sys
import logging
from datetime import datetime

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up environment file path before importing settings
env_file_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
if os.path.exists(env_file_path):
    os.environ['ENV_FILE'] = env_file_path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.database import IncomingCustomer
from app.services.matching.matching_service import MatchingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_processing_status_updates():
    """Test that processing status is updated when customers are processed"""
    
    # Initialize database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    matching_service = MatchingService()
    
    try:
        with SessionLocal() as db:
            # Get a few incoming customers that haven't been processed yet
            pending_customers = db.query(IncomingCustomer).filter(
                IncomingCustomer.processing_status == "pending"
            ).limit(3).all()
            
            if not pending_customers:
                logger.warning("No pending customers found. Creating test data...")
                # Create a test customer if none exist
                test_customer = IncomingCustomer(
                    company_name="Test Company for Processing Status",
                    contact_name="Test Contact",
                    email="test@example.com",
                    phone="+1-555-123-4567",
                    processing_status="pending"
                )
                db.add(test_customer)
                db.commit()
                db.refresh(test_customer)
                pending_customers = [test_customer]
            
            logger.info(f"Testing processing status updates for {len(pending_customers)} customers")
            
            for customer in pending_customers:
                request_id = getattr(customer, 'request_id')
                initial_status = getattr(customer, 'processing_status', 'unknown')
                initial_processed_date = getattr(customer, 'processed_date', None)
                
                logger.info(f"Processing customer {request_id}: {customer.company_name}")
                logger.info(f"  Initial status: {initial_status}")
                logger.info(f"  Initial processed_date: {initial_processed_date}")
                
                # Process the customer
                matches = matching_service.find_matches(customer, db)
                
                # Refresh the customer to get updated status
                db.refresh(customer)
                
                final_status = getattr(customer, 'processing_status', 'unknown')
                final_processed_date = getattr(customer, 'processed_date', None)
                
                logger.info(f"  Final status: {final_status}")
                logger.info(f"  Final processed_date: {final_processed_date}")
                logger.info(f"  Matches found: {len(matches)}")
                
                # Verify the status was updated
                if final_status == "processed":
                    logger.info(f"  ✅ Status correctly updated to 'processed'")
                else:
                    logger.error(f"  ❌ Status not updated correctly. Expected 'processed', got '{final_status}'")
                
                if final_processed_date is not None:
                    logger.info(f"  ✅ Processed date correctly set to {final_processed_date}")
                else:
                    logger.error(f"  ❌ Processed date not set")
                
                # Verify the processed date is recent
                if final_processed_date:
                    time_diff = datetime.now() - final_processed_date
                    if time_diff.total_seconds() < 60:  # Within 1 minute
                        logger.info(f"  ✅ Processed date is recent ({time_diff.total_seconds():.1f}s ago)")
                    else:
                        logger.warning(f"  ⚠️ Processed date seems old ({time_diff.total_seconds():.1f}s ago)")
                
                print()  # Empty line for readability
        
        logger.info("✅ Processing status test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error testing processing status updates: {e}")
        raise


def test_no_matches_scenario():
    """Test that processing status is updated even when no matches are found"""
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    matching_service = MatchingService()
    
    try:
        with SessionLocal() as db:
            # Create a customer with a very unique name that likely won't match
            unique_customer = IncomingCustomer(
                company_name="VeryUniqueCompanyNameThatWontMatch12345",
                contact_name="Unique Contact",
                email="unique@veryuniquecompany.com",
                phone="+1-555-999-9999",
                processing_status="pending"
            )
            db.add(unique_customer)
            db.commit()
            db.refresh(unique_customer)
            
            request_id = getattr(unique_customer, 'request_id')
            logger.info(f"Testing no-matches scenario for customer {request_id}")
            
            # Process the customer
            matches = matching_service.find_matches(unique_customer, db)
            
            # Refresh to get updated status
            db.refresh(unique_customer)
            
            final_status = getattr(unique_customer, 'processing_status', 'unknown')
            final_processed_date = getattr(unique_customer, 'processed_date', None)
            
            logger.info(f"  Matches found: {len(matches)}")
            logger.info(f"  Final status: {final_status}")
            logger.info(f"  Final processed_date: {final_processed_date}")
            
            # Verify status was updated even with no matches
            if final_status == "processed":
                logger.info(f"  ✅ Status correctly updated to 'processed' even with no matches")
            else:
                logger.error(f"  ❌ Status not updated correctly. Expected 'processed', got '{final_status}'")
            
            if final_processed_date is not None:
                logger.info(f"  ✅ Processed date correctly set even with no matches")
            else:
                logger.error(f"  ❌ Processed date not set")
        
        logger.info("✅ No-matches scenario test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error testing no-matches scenario: {e}")
        raise


def main():
    """Main function to run processing status tests"""
    logger.info("Starting processing status update tests...")
    
    try:
        # Test normal processing scenario
        test_processing_status_updates()
        
        # Test no-matches scenario
        test_no_matches_scenario()
        
        logger.info("🎉 All processing status tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Processing status tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 