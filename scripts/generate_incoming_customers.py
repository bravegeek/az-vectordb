"""
Generate incoming customer test data with slight modifications from existing customers
for testing customer matching algorithms.

This script creates realistic test scenarios by:
1. Reading existing customers from the database
2. Creating variations with controlled modifications
3. Generating incoming customer records for testing
"""

import os
import sys
import logging
import random
import string
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up environment file path before importing settings
env_file_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
if os.path.exists(env_file_path):
    os.environ['ENV_FILE'] = env_file_path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.database import Customer, IncomingCustomer
from app.services.embedding_service import embedding_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IncomingCustomerGenerator:
    """Expert class for generating incoming customer test data with controlled variations"""
    
    def __init__(self, db_url: str):
        """Initialize the generator with database connection"""
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Common company name variations for realistic testing
        self.company_suffixes = [
            " Inc.", " LLC", " Corp.", " Ltd.", " Co.", " & Associates",
            " Group", " Solutions", " Technologies", " Systems", " Services"
        ]
        
        self.company_prefixes = [
            "Advanced ", "Global ", "Premier ", "Elite ", "Professional ",
            "Innovative ", "Strategic ", "Dynamic ", "Modern ", "Next-Gen "
        ]
        
        # Common typos and variations
        self.common_typos = {
            'a': ['@', '4'],
            'e': ['3'],
            'i': ['1', '!'],
            'o': ['0'],
            's': ['$', '5'],
            't': ['7']
        }
        
        # Address variations
        self.street_suffixes = {
            'Street': ['St', 'St.', 'ST'],
            'Avenue': ['Ave', 'Ave.', 'AV'],
            'Road': ['Rd', 'Rd.', 'RD'],
            'Boulevard': ['Blvd', 'Blvd.', 'BL'],
            'Drive': ['Dr', 'Dr.', 'DR']
        }

    def get_existing_customers(self, limit: int = 50) -> List[Customer]:
        """Retrieve existing customers from database for base data"""
        try:
            with self.SessionLocal() as db:
                customers = db.query(Customer).limit(limit).all()
                logger.info(f"Retrieved {len(customers)} existing customers for base data")
                return customers
        except Exception as e:
            logger.error(f"Error retrieving existing customers: {e}")
            raise

    def create_company_name_variation(self, original_name: str, variation_type: str) -> str:
        """Create realistic company name variations for testing"""
        if variation_type == "suffix_change":
            # Add or change company suffix
            for suffix in self.company_suffixes:
                if original_name.endswith(suffix):
                    # Remove existing suffix and add new one
                    base_name = original_name[:-len(suffix)]
                    return base_name + random.choice([s for s in self.company_suffixes if s != suffix])
            # Add suffix if none exists
            return original_name + random.choice(self.company_suffixes)
            
        elif variation_type == "prefix_add":
            # Add company prefix
            return random.choice(self.company_prefixes) + original_name
            
        elif variation_type == "typo":
            # Introduce realistic typos
            if len(original_name) > 3:
                pos = random.randint(0, len(original_name) - 1)
                char = original_name[pos].lower()
                if char in self.common_typos:
                    return original_name[:pos] + random.choice(self.common_typos[char]) + original_name[pos + 1:]
            return original_name
            
        elif variation_type == "abbreviation":
            # Create abbreviation
            words = original_name.split()
            if len(words) > 1:
                return " ".join([word[0] for word in words])
            return original_name
            
        elif variation_type == "word_order":
            # Change word order
            words = original_name.split()
            if len(words) > 1:
                random.shuffle(words)
                return " ".join(words)
            return original_name
            
        else:
            return original_name

    def create_address_variation(self, original_address: str, variation_type: str) -> str:
        """Create address variations for testing"""
        if not original_address:
            return original_address
            
        if variation_type == "suffix_abbreviation":
            # Abbreviate street suffixes
            for full_suffix, abbreviations in self.street_suffixes.items():
                if full_suffix in original_address:
                    return original_address.replace(full_suffix, random.choice(abbreviations))
            return original_address
            
        elif variation_type == "number_format":
            # Change number formatting (e.g., "123" to "123rd" or "123rd St")
            import re
            numbers = re.findall(r'\b\d+\b', original_address)
            if numbers:
                number = numbers[0]
                if number.endswith('1') and number != '11':
                    suffix = 'st'
                elif number.endswith('2') and number != '12':
                    suffix = 'nd'
                elif number.endswith('3') and number != '13':
                    suffix = 'rd'
                else:
                    suffix = 'th'
                return original_address.replace(number, f"{number}{suffix}")
            return original_address
            
        else:
            return original_address

    def create_email_variation(self, original_email: str, variation_type: str) -> str:
        """Create email variations for testing"""
        if not original_email:
            return original_email
            
        if '@' not in original_email:
            return original_email
            
        local_part, domain = original_email.split('@')
        
        if variation_type == "domain_change":
            # Change domain
            new_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'company.com', 'business.net']
            return f"{local_part}@{random.choice(new_domains)}"
            
        elif variation_type == "local_part_typo":
            # Add typo to local part
            if len(local_part) > 2:
                pos = random.randint(0, len(local_part) - 1)
                char = local_part[pos].lower()
                if char in self.common_typos:
                    return f"{local_part[:pos]}{random.choice(self.common_typos[char])}{local_part[pos + 1:]}@{domain}"
            return original_email
            
        elif variation_type == "underscore_add":
            # Add underscore to local part
            if '_' not in local_part:
                return f"{local_part}_{random.choice(string.ascii_lowercase)}@{domain}"
            return original_email
            
        else:
            return original_email

    def create_phone_variation(self, original_phone: str, variation_type: str) -> str:
        """Create phone number variations for testing"""
        if not original_phone:
            return original_phone
            
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, original_phone))
        
        if len(digits) < 10:
            return original_phone
            
        if variation_type == "format_change":
            # Change formatting
            if len(digits) == 10:
                formats = [
                    f"({digits[:3]}) {digits[3:6]}-{digits[6:]}",
                    f"{digits[:3]}-{digits[3:6]}-{digits[6:]}",
                    f"{digits[:3]}.{digits[3:6]}.{digits[6:]}",
                    f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
                ]
                return random.choice(formats)
            return original_phone
            
        elif variation_type == "digit_typo":
            # Change one digit
            if len(digits) >= 10:
                pos = random.randint(0, len(digits) - 1)
                new_digit = str(random.randint(0, 9))
                new_digits = digits[:pos] + new_digit + digits[pos + 1:]
                return f"({new_digits[:3]}) {new_digits[3:6]}-{new_digits[6:]}"
            return original_phone
            
        else:
            return original_phone

    def generate_incoming_customer(self, base_customer: Customer, variation_intensity: str = "medium") -> Dict[str, Any]:
        """Generate an incoming customer with controlled variations from base customer"""
        
        # Define variation probabilities based on intensity
        variation_probs = {
            "low": {"company_name": 0.3, "address": 0.2, "email": 0.2, "phone": 0.2},
            "medium": {"company_name": 0.6, "address": 0.4, "email": 0.4, "phone": 0.4},
            "high": {"company_name": 0.8, "address": 0.7, "email": 0.7, "phone": 0.7}
        }
        
        probs = variation_probs[variation_intensity]
        
        # Start with base customer data
        incoming_data = {
            "company_name": base_customer.company_name,
            "contact_name": base_customer.contact_name,
            "email": base_customer.email,
            "phone": base_customer.phone,
            "address_line1": base_customer.address_line1,
            "address_line2": base_customer.address_line2,
            "city": base_customer.city,
            "state_province": base_customer.state_province,
            "postal_code": base_customer.postal_code,
            "country": base_customer.country,
            "industry": base_customer.industry,
            "annual_revenue": float(str(base_customer.annual_revenue)) if base_customer.annual_revenue is not None else None,
            "employee_count": base_customer.employee_count,
            "website": base_customer.website,
            "description": base_customer.description
        }
        
        # Apply variations based on probabilities
        if random.random() < probs["company_name"] and incoming_data["company_name"] is not None:
            variation_types = ["suffix_change", "prefix_add", "typo", "abbreviation", "word_order"]
            incoming_data["company_name"] = self.create_company_name_variation(
                incoming_data["company_name"], 
                random.choice(variation_types)
            )
        
        if random.random() < probs["address"] and incoming_data["address_line1"] is not None:
            variation_types = ["suffix_abbreviation", "number_format"]
            incoming_data["address_line1"] = self.create_address_variation(
                incoming_data["address_line1"],
                random.choice(variation_types)
            )
        
        if random.random() < probs["email"] and incoming_data["email"] is not None:
            variation_types = ["domain_change", "local_part_typo", "underscore_add"]
            incoming_data["email"] = self.create_email_variation(
                incoming_data["email"],
                random.choice(variation_types)
            )
        
        if random.random() < probs["phone"] and incoming_data["phone"] is not None:
            variation_types = ["format_change", "digit_typo"]
            incoming_data["phone"] = self.create_phone_variation(
                incoming_data["phone"],
                random.choice(variation_types)
            )
        
        return incoming_data

    def create_incoming_customers(self, count: int = 10, variation_intensity: str = "medium") -> List[Dict[str, Any]]:
        """Create multiple incoming customers with variations"""
        logger.info(f"Generating {count} incoming customers with {variation_intensity} variation intensity")
        
        # Get base customers
        base_customers = self.get_existing_customers(limit=count * 2)  # Get extra for variety
        
        if not base_customers:
            raise ValueError("No existing customers found in database")
        
        incoming_customers = []
        
        for i in range(count):
            # Select random base customer
            base_customer = random.choice(base_customers)
            
            # Generate variation
            incoming_data = self.generate_incoming_customer(base_customer, variation_intensity)
            
            # Add metadata
            incoming_data["base_customer_id"] = base_customer.customer_id
            incoming_data["variation_intensity"] = variation_intensity
            incoming_data["generated_at"] = datetime.now().isoformat()
            
            incoming_customers.append(incoming_data)
            
            logger.info(f"Generated incoming customer {i+1}/{count}: {incoming_data['company_name']}")
        
        return incoming_customers

    def save_to_database(self, incoming_customers: List[Dict[str, Any]]) -> List[IncomingCustomer]:
        """Save incoming customers to database with embeddings"""
        logger.info(f"Saving {len(incoming_customers)} incoming customers to database")
        
        saved_customers = []
        
        try:
            with self.SessionLocal() as db:
                for customer_data in incoming_customers:
                    # Remove metadata fields
                    base_customer_id = customer_data.pop("base_customer_id", None)
                    variation_intensity = customer_data.pop("variation_intensity", None)
                    generated_at = customer_data.pop("generated_at", None)
                    
                    # Generate embeddings
                    company_embedding, profile_embedding = embedding_service.generate_customer_embeddings(
                        customer_data
                    )
                    
                    # Create incoming customer record
                    db_incoming = IncomingCustomer(
                        **customer_data,
                        company_name_embedding=company_embedding,
                        full_profile_embedding=profile_embedding,
                        processing_status="pending"
                    )
                    
                    db.add(db_incoming)
                    saved_customers.append(db_incoming)
                
                db.commit()
                
                # Refresh all records to get IDs
                for customer in saved_customers:
                    db.refresh(customer)
                
                logger.info(f"Successfully saved {len(saved_customers)} incoming customers to database")
                return saved_customers
                
        except Exception as e:
            logger.error(f"Error saving incoming customers to database: {e}")
            raise

    def save_to_json(self, incoming_customers: List[Dict[str, Any]], output_path: str) -> bool:
        """Save incoming customers to JSON file for review"""
        try:
            import json
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(incoming_customers, f, indent=2, default=str)
            
            logger.info(f"Saved incoming customers to JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False


def main():
    """Main function to generate and save incoming customer test data"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate incoming customer test data")
    parser.add_argument("--count", type=int, default=10, help="Number of incoming customers to generate")
    parser.add_argument("--intensity", choices=["low", "medium", "high"], default="medium", 
                       help="Variation intensity level")
    parser.add_argument("--output-json", type=str, help="Optional JSON output file for review")
    parser.add_argument("--db-url", type=str, help="Database URL (defaults to settings)")
    
    args = parser.parse_args()
    
    # Use provided DB URL or default from settings
    try:
        db_url = args.db_url or settings.database_url
        logger.info(f"Using database URL: {db_url}")
    except Exception as e:
        logger.error(f"Failed to get database URL from settings: {e}")
        logger.error("Please ensure app/.env file exists and contains database configuration")
        sys.exit(1)
    
    try:
        # Initialize generator
        generator = IncomingCustomerGenerator(db_url)
        
        # Generate incoming customers
        incoming_customers = generator.create_incoming_customers(
            count=args.count,
            variation_intensity=args.intensity
        )
        
        # Save to database
        saved_customers = generator.save_to_database(incoming_customers)
        
        # Optionally save to JSON for review
        if args.output_json:
            generator.save_to_json(incoming_customers, args.output_json)
        
        # Print summary
        print(f"\n✅ Successfully generated {len(saved_customers)} incoming customers")
        print(f"📊 Variation intensity: {args.intensity}")
        print(f"💾 Saved to database with request IDs: {[c.request_id for c in saved_customers]}")
        
        if args.output_json:
            print(f"📄 Review data saved to: {args.output_json}")
        
        print("\n🎯 Ready for matching tests!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
