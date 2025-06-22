"""
Script to generate sample customer records for the vector database
"""
import random
import logging
from datetime import datetime
from decimal import Decimal
from faker import Faker
from sqlalchemy.orm import Session
import numpy as np

from database import SessionLocal, engine, initialize_database, create_tables
from models import Customer
from embedding_service import get_embedding_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure output goes to console
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Industry options for more realistic data
INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Manufacturing", "Retail", 
    "Education", "Energy", "Transportation", "Hospitality", "Construction",
    "Agriculture", "Entertainment", "Telecommunications", "Consulting", 
    "Real Estate", "Automotive", "Aerospace", "Pharmaceuticals", "Media"
]

def generate_random_vector(dim=1536):
    """Generate a random vector with the specified dimension"""
    # Generate random vector and normalize it
    vec = np.random.randn(dim)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()

def generate_customer_data(count=1):
    """Generate a list of customer data dictionaries"""
    customers = []
    
    for _ in range(count):
        # Generate a realistic company name
        company_name = fake.company()
        
        # Generate other customer fields
        customer = {
            "company_name": company_name,
            "contact_name": fake.name(),
            "email": fake.company_email(),
            "phone": fake.phone_number(),
            "address_line1": fake.street_address(),
            "address_line2": fake.secondary_address() if random.random() > 0.7 else None,
            "city": fake.city(),
            "state_province": fake.state(),
            "postal_code": fake.postcode(),
            "country": fake.country(),
            "industry": random.choice(INDUSTRIES),
            "annual_revenue": Decimal(str(round(random.uniform(100000, 10000000), 2))),
            "employee_count": random.randint(5, 10000),
            "website": f"https://www.{company_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
            "description": fake.paragraph(nb_sentences=5),
        }
        customers.append(customer)
    
    return customers

def create_customer_records(db: Session, customer_data, embedding_service=None):
    """Create customer records in the database with embeddings"""
    created_count = 0
    
    for data in customer_data:
        try:
            # Generate embeddings if embedding service is provided
            if embedding_service:
                # Company name embedding
                company_name_embedding = embedding_service.get_embedding(data["company_name"])
                
                # Full profile embedding - combine all text fields
                profile_text = (
                    f"{data['company_name']} {data.get('description', '')} "
                    f"{data['industry']} {data.get('city', '')} {data.get('country', '')}"
                )
                full_profile_embedding = embedding_service.get_embedding(profile_text)
            else:
                # Use random vectors if no embedding service
                company_name_embedding = generate_random_vector()
                full_profile_embedding = generate_random_vector()
            
            # Create customer record
            customer = Customer(
                **data,
                company_name_embedding=company_name_embedding,
                full_profile_embedding=full_profile_embedding
            )
            
            db.add(customer)
            created_count += 1
            
            # Commit in batches to avoid memory issues
            if created_count % 50 == 0:
                db.commit()
                logger.info(f"Created {created_count} customer records so far...")
                
        except Exception as e:
            logger.error(f"Error creating customer record: {e}")
            db.rollback()
    
    # Final commit for any remaining records
    db.commit()
    logger.info(f"Successfully created {created_count} customer records")
    return created_count

def main(count=500, use_real_embeddings=False):
    """Main function to generate and insert customer records"""
    logger.info(f"Starting generation of {count} customer records")
    
    # Initialize database
    initialize_database()
    create_tables()
    
    # Generate customer data
    customer_data = generate_customer_data(count)
    logger.info(f"Generated {len(customer_data)} customer data records")
    
    # Initialize embedding service if using real embeddings
    embedding_service = None
    if use_real_embeddings:
        try:
            embedding_service = get_embedding_service()
        except Exception as e:
            logger.warning(f"Could not initialize embedding service: {e}")
            logger.warning("Falling back to random vector embeddings")
    
    # Create database session and insert records
    db = SessionLocal()
    try:
        created_count = create_customer_records(db, customer_data, embedding_service)
        logger.info(f"Successfully created {created_count} customer records")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample customer records")
    parser.add_argument("--count", type=int, default=500, help="Number of customer records to generate")
    parser.add_argument("--real-embeddings", action="store_true", help="Use real embeddings instead of random vectors")
    
    args = parser.parse_args()
    main(count=args.count, use_real_embeddings=args.real_embeddings)
