"""
Generate customer data in CSV and JSON formats without database dependencies
"""
import os
import json
import csv
import random
import logging
from datetime import datetime
from decimal import Decimal
from faker import Faker
import numpy as np

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
    
    logger.info(f"Generating {count} customer records...")
    
    for i in range(count):
        # Generate a realistic company name
        company_name = fake.company()
        
        # Generate other customer fields
        customer = {
            "customer_id": i + 1,
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
            "annual_revenue": round(random.uniform(100000, 10000000), 2),
            "employee_count": random.randint(5, 10000),
            "website": f"https://www.{company_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
            "description": fake.paragraph(nb_sentences=5),
            "created_date": datetime.now().isoformat(),
        }
        
        # Add vector embeddings (as separate files to keep CSV clean)
        customer["company_name_embedding"] = generate_random_vector(1536)
        customer["full_profile_embedding"] = generate_random_vector(1536)
        
        customers.append(customer)
        
        # Log progress
        if (i + 1) % 50 == 0:
            logger.info(f"Generated {i + 1}/{count} customer records...")
    
    logger.info(f"Successfully generated {len(customers)} customer records")
    return customers

def save_to_json(customers, output_path):
    """Save customer data to JSON file"""
    try:
        # Convert Decimal to float for JSON serialization
        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(customers, f, default=decimal_default, indent=2)
        
        logger.info(f"Saved customer data to JSON: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to JSON: {e}")
        return False

def save_to_csv(customers, output_path):
    """Save customer data to CSV file (excluding vector embeddings)"""
    try:
        # Extract keys excluding embeddings
        keys = [k for k in customers[0].keys() if 'embedding' not in k]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            
            # Write each customer, excluding embedding fields
            for customer in customers:
                row = {k: customer[k] for k in keys}
                writer.writerow(row)
        
        logger.info(f"Saved customer data to CSV: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        return False

def save_embeddings(customers, output_dir):
    """Save embeddings to separate files"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Save company name embeddings
        company_embeddings = {str(c["customer_id"]): c["company_name_embedding"] for c in customers}
        with open(os.path.join(output_dir, "company_name_embeddings.json"), 'w') as f:
            json.dump(company_embeddings, f)
        
        # Save full profile embeddings
        profile_embeddings = {str(c["customer_id"]): c["full_profile_embedding"] for c in customers}
        with open(os.path.join(output_dir, "full_profile_embeddings.json"), 'w') as f:
            json.dump(profile_embeddings, f)
        
        logger.info(f"Saved embeddings to directory: {output_dir}")
        return True
    except Exception as e:
        logger.error(f"Error saving embeddings: {e}")
        return False

def main(count=500, output_dir="data"):
    """Main function to generate and save customer records"""
    logger.info(f"Starting generation of {count} customer records")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate customer data
    customers = generate_customer_data(count)
    
    # Save to different formats
    save_to_json(customers, os.path.join(output_dir, "customers.json"))
    save_to_csv(customers, os.path.join(output_dir, "customers.csv"))
    save_embeddings(customers, os.path.join(output_dir, "embeddings"))
    
    logger.info(f"Customer data generation complete. Files saved to '{output_dir}' directory")
    
    return {
        "json_path": os.path.join(output_dir, "customers.json"),
        "csv_path": os.path.join(output_dir, "customers.csv"),
        "embeddings_dir": os.path.join(output_dir, "embeddings")
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample customer records")
    parser.add_argument("--count", type=int, default=300, help="Number of customer records to generate")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory for generated files")
    
    args = parser.parse_args()
    main(count=args.count, output_dir=args.output_dir)
