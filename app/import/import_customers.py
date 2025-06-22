"""
Script to generate and import customer records for the vector database
"""
import os
import json
import csv
import random
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Union
from faker import Faker
from sqlalchemy.orm import Session
import numpy as np

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def get_data_dir() -> Path:
    """Get the path to the data directory"""
    # Get the project root directory (one level up from the app directory)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    return data_dir

def import_customers_from_json(file_path: Union[str, Path] = None) -> List[Dict[str, Any]]:
    """Import customer data from a JSON file"""
    if file_path is None:
        file_path = get_data_dir() / 'customers.json'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        logger.info(f"Successfully imported {len(customers)} customers from {file_path}")
        return customers
    except Exception as e:
        logger.error(f"Error importing from JSON file {file_path}: {str(e)}")
        return []

def import_customers_from_csv(file_path: Union[str, Path] = None) -> List[Dict[str, Any]]:
    """Import customer data from a CSV file"""
    if file_path is None:
        file_path = get_data_dir() / 'customers.csv'
    
    customers = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields from string to appropriate types
                if 'annual_revenue' in row and row['annual_revenue']:
                    row['annual_revenue'] = Decimal(row['annual_revenue'])
                if 'employee_count' in row and row['employee_count']:
                    row['employee_count'] = int(row['employee_count'])
                customers.append(row)
        
        logger.info(f"Successfully imported {len(customers)} customers from {file_path}")
        return customers
    except Exception as e:
        logger.error(f"Error importing from CSV file {file_path}: {str(e)}")
        return []

def generate_customer_data(count=1) -> List[Dict[str, Any]]:
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

def main(count=500, use_real_embeddings=False, source=None, file_format=None):
    """Main function to generate and insert customer records"""
    # Initialize database
    initialize_database()
    create_tables()
    
    # Initialize embedding service if needed
    embedding_service = None
    if use_real_embeddings:
        try:
            embedding_service = get_embedding_service()
            logger.info("Using real embeddings from OpenAI")
        except Exception as e:
            logger.warning(f"Could not initialize embedding service: {str(e)}. Using random embeddings.")
    
    # Get customer data
    if source:
        logger.info(f"Importing customer data from {source}...")
        customer_data = import_customers(source, file_format)
        if not customer_data:
            logger.warning("No customer data imported. Falling back to generating sample data.")
            customer_data = generate_customer_data(count)
    else:
        logger.info(f"Generating {count} sample customer records...")
        customer_data = generate_customer_data(count)
    
    # Create customer records in the database
    db = SessionLocal()
    try:
        created_count = create_customer_records(db, customer_data, embedding_service)
        db.commit()
        logger.info(f"Successfully created {created_count} customer records")
        return created_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer records: {str(e)}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and import customer records")
    
    # Data source options
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--count", 
        type=int, 
        default=500, 
        help="Number of customer records to generate (default: 500)"
    )
    source_group.add_argument(
        "--source", 
        type=str, 
        help="Path to customer data file (CSV or JSON). Can be absolute or relative to the data directory."
    )
    
    # Optional arguments
    parser.add_argument(
        "--format", 
        choices=['json', 'csv'], 
        help="Explicitly specify the file format (optional, auto-detected from file extension)"
    )
    parser.add_argument(
        "--use-real-embeddings", 
        action="store_true", 
        help="Use real embeddings from OpenAI (requires API key)"
    )
    
    args = parser.parse_args()
    
    main(
        count=args.count,
        use_real_embeddings=args.use_real_embeddings,
        source=args.source,
        file_format=args.format
    )
