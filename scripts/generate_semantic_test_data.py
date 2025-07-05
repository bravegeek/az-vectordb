"""
Generate semantic similarity test data for vector matching

This script creates incoming customers with controlled semantic variations
to test vector matching functionality across different intensity levels.
"""

import os
import sys
import logging
import random
import json
import argparse
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


class SemanticTestDataGenerator:
    """Generate semantic similarity test data with controlled variations"""
    
    def __init__(self, db_url: str):
        """Initialize the generator with database connection"""
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Semantic variation patterns for testing
        self.semantic_variations = {
            "low": {
                "company_suffixes": [
                    (" Inc.", " Incorporated"),
                    (" Corp.", " Corporation"),
                    (" LLC", " Limited Liability Company"),
                    (" Ltd.", " Limited"),
                    (" Co.", " Company")
                ],
                "industry_terms": [
                    ("Tech", "Technology"),
                    ("Solutions", "Services"),
                    ("Systems", "Platforms"),
                    ("Group", "Partners"),
                    ("Agency", "Consulting")
                ],
                "common_abbreviations": [
                    ("International", "Int'l"),
                    ("Development", "Dev"),
                    ("Management", "Mgmt"),
                    ("Administration", "Admin"),
                    ("Engineering", "Eng")
                ]
            },
            "medium": {
                "company_suffixes": [
                    (" Inc.", " Incorporated"),
                    (" Corp.", " Corporation"),
                    (" LLC", " Limited Liability Company"),
                    (" Ltd.", " Limited"),
                    (" Co.", " Company"),
                    (" & Associates", " Associates"),
                    (" Group", " Partners"),
                    (" Solutions", " Services")
                ],
                "industry_terms": [
                    ("Tech", "Technology"),
                    ("Solutions", "Services"),
                    ("Systems", "Platforms"),
                    ("Group", "Partners"),
                    ("Agency", "Consulting"),
                    ("Software", "Applications"),
                    ("Digital", "Online"),
                    ("Cloud", "Web"),
                    ("AI", "Artificial Intelligence"),
                    ("Data", "Analytics")
                ],
                "common_abbreviations": [
                    ("International", "Int'l"),
                    ("Development", "Dev"),
                    ("Management", "Mgmt"),
                    ("Administration", "Admin"),
                    ("Engineering", "Eng"),
                    ("Information", "Info"),
                    ("Communication", "Comm"),
                    ("Professional", "Prof")
                ]
            },
            "high": {
                "company_suffixes": [
                    (" Inc.", " Incorporated"),
                    (" Corp.", " Corporation"),
                    (" LLC", " Limited Liability Company"),
                    (" Ltd.", " Limited"),
                    (" Co.", " Company"),
                    (" & Associates", " Associates"),
                    (" Group", " Partners"),
                    (" Solutions", " Services"),
                    (" Technologies", " Tech"),
                    (" Systems", " Platforms"),
                    (" Consulting", " Advisory"),
                    (" Services", " Solutions")
                ],
                "industry_terms": [
                    ("Tech", "Technology"),
                    ("Solutions", "Services"),
                    ("Systems", "Platforms"),
                    ("Group", "Partners"),
                    ("Agency", "Consulting"),
                    ("Software", "Applications"),
                    ("Digital", "Online"),
                    ("Cloud", "Web"),
                    ("AI", "Artificial Intelligence"),
                    ("Data", "Analytics"),
                    ("Machine Learning", "ML"),
                    ("Blockchain", "Distributed Ledger"),
                    ("Cybersecurity", "Security"),
                    ("E-commerce", "Online Retail"),
                    ("Fintech", "Financial Technology"),
                    ("Healthtech", "Healthcare Technology"),
                    ("Edtech", "Education Technology"),
                    ("IoT", "Internet of Things")
                ],
                "common_abbreviations": [
                    ("International", "Int'l"),
                    ("Development", "Dev"),
                    ("Management", "Mgmt"),
                    ("Administration", "Admin"),
                    ("Engineering", "Eng"),
                    ("Information", "Info"),
                    ("Communication", "Comm"),
                    ("Professional", "Prof"),
                    ("Enterprise", "Ent"),
                    ("Infrastructure", "Infra"),
                    ("Architecture", "Arch"),
                    ("Implementation", "Impl"),
                    ("Integration", "Integ"),
                    ("Optimization", "Opt"),
                    ("Automation", "Auto")
                ]
            }
        }
        
        # Industry-specific semantic mappings
        self.industry_semantic_mappings = {
            "Technology": {
                "Software": ["Applications", "Platforms", "Systems"],
                "Development": ["Engineering", "Programming", "Coding"],
                "Cloud": ["Web", "Online", "Internet"],
                "AI": ["Artificial Intelligence", "Machine Learning", "ML"],
                "Data": ["Analytics", "Insights", "Intelligence"]
            },
            "Healthcare": {
                "Medical": ["Healthcare", "Clinical", "Patient"],
                "Pharmaceutical": ["Drug", "Medicine", "Therapeutic"],
                "Diagnostic": ["Testing", "Screening", "Analysis"],
                "Treatment": ["Therapy", "Care", "Intervention"]
            },
            "Finance": {
                "Investment": ["Asset Management", "Wealth Management", "Portfolio"],
                "Banking": ["Financial Services", "Lending", "Credit"],
                "Insurance": ["Risk Management", "Protection", "Coverage"],
                "Trading": ["Securities", "Markets", "Exchange"]
            },
            "Manufacturing": {
                "Production": ["Manufacturing", "Fabrication", "Assembly"],
                "Quality": ["Standards", "Compliance", "Certification"],
                "Supply Chain": ["Logistics", "Distribution", "Procurement"]
            }
        }

    def get_existing_customers(self, limit: int = 100) -> List[Customer]:
        """Retrieve existing customers from database for base data"""
        try:
            with self.SessionLocal() as db:
                customers = db.query(Customer).limit(limit).all()
                logger.info(f"Retrieved {len(customers)} existing customers for base data")
                return customers
        except Exception as e:
            logger.error(f"Error retrieving existing customers: {e}")
            raise

    def apply_semantic_variation(self, text: str, intensity: str, variation_type: str) -> str:
        """Apply semantic variation to text based on intensity level"""
        if not text:
            return text
            
        variations = self.semantic_variations[intensity]
        
        if variation_type == "suffix":
            for old_suffix, new_suffix in variations["company_suffixes"]:
                if text.endswith(old_suffix):
                    return text[:-len(old_suffix)] + new_suffix
            # Add random suffix if none exists
            return text + random.choice([v[1] for v in variations["company_suffixes"]])
            
        elif variation_type == "industry_term":
            for old_term, new_term in variations["industry_terms"]:
                if old_term.lower() in text.lower():
                    return text.replace(old_term, new_term)
            return text
            
        elif variation_type == "abbreviation":
            for full_word, abbrev in variations["common_abbreviations"]:
                if full_word.lower() in text.lower():
                    return text.replace(full_word, abbrev)
            return text
            
        elif variation_type == "industry_specific":
            # Apply industry-specific semantic variations
            for industry, mappings in self.industry_semantic_mappings.items():
                for old_term, alternatives in mappings.items():
                    if old_term.lower() in text.lower():
                        return text.replace(old_term, random.choice(alternatives))
            return text
            
        elif variation_type == "word_order":
            # Change word order while maintaining semantic meaning
            words = text.split()
            if len(words) > 2:
                # Keep first and last words, shuffle middle
                first, *middle, last = words
                random.shuffle(middle)
                return " ".join([first] + middle + [last])
            return text
            
        elif variation_type == "synonym":
            # Apply synonym-based variations
            synonyms = {
                "Global": ["International", "Worldwide", "Universal"],
                "Advanced": ["Innovative", "Cutting-edge", "Modern"],
                "Professional": ["Expert", "Specialized", "Skilled"],
                "Comprehensive": ["Complete", "Full-service", "Integrated"],
                "Strategic": ["Tactical", "Planned", "Systematic"]
            }
            
            for word, alternatives in synonyms.items():
                if word.lower() in text.lower():
                    return text.replace(word, random.choice(alternatives))
            return text
            
        return text

    def generate_semantic_variation(self, base_customer: Customer, intensity: str) -> Dict[str, Any]:
        """Generate incoming customer with semantic variations"""
        
        # Define variation probabilities based on intensity
        variation_probs = {
            "low": {
                "company_name": 0.8,  # High probability for company name variations
                "description": 0.3,
                "industry": 0.2
            },
            "medium": {
                "company_name": 0.9,
                "description": 0.6,
                "industry": 0.4
            },
            "high": {
                "company_name": 0.95,
                "description": 0.8,
                "industry": 0.6
            }
        }
        
        probs = variation_probs[intensity]
        
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
        
        # Apply semantic variations
        if random.random() < probs["company_name"] and incoming_data["company_name"]:
            variation_types = ["suffix", "industry_term", "abbreviation", "industry_specific", "synonym"]
            # Apply multiple variations for higher intensity
            num_variations = 1 if intensity == "low" else (2 if intensity == "medium" else 3)
            
            for _ in range(num_variations):
                variation_type = random.choice(variation_types)
                incoming_data["company_name"] = self.apply_semantic_variation(
                    incoming_data["company_name"], intensity, variation_type
                )
        
        if random.random() < probs["description"] and incoming_data["description"]:
            variation_types = ["industry_specific", "synonym", "abbreviation"]
            variation_type = random.choice(variation_types)
            incoming_data["description"] = self.apply_semantic_variation(
                incoming_data["description"], intensity, variation_type
            )
        
        if random.random() < probs["industry"] and incoming_data["industry"]:
            # Apply industry-specific variations
            if incoming_data["industry"] in self.industry_semantic_mappings:
                industry_variations = list(self.industry_semantic_mappings.keys())
                incoming_data["industry"] = random.choice(industry_variations)
        
        return incoming_data

    def create_semantic_test_data(self, count_per_intensity: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """Create semantic test data for all intensity levels"""
        logger.info(f"Generating semantic test data: {count_per_intensity} customers per intensity level")
        
        # Get base customers
        base_customers = self.get_existing_customers(limit=count_per_intensity * 3 * 2)  # Extra for variety
        
        if not base_customers:
            raise ValueError("No existing customers found in database")
        
        test_data = {}
        
        for intensity in ["low", "medium", "high"]:
            logger.info(f"Generating {count_per_intensity} customers with {intensity} intensity")
            intensity_customers = []
            
            for i in range(count_per_intensity):
                # Select random base customer
                base_customer = random.choice(base_customers)
                
                # Generate semantic variation
                incoming_data = self.generate_semantic_variation(base_customer, intensity)
                
                # Add metadata
                incoming_data["base_customer_id"] = base_customer.customer_id
                incoming_data["variation_intensity"] = intensity
                incoming_data["test_category"] = "semantic_similarity"
                incoming_data["generated_at"] = datetime.now().isoformat()
                
                intensity_customers.append(incoming_data)
                
                logger.info(f"Generated {intensity} customer {i+1}/{count_per_intensity}: {incoming_data['company_name']}")
            
            test_data[intensity] = intensity_customers
        
        return test_data

    def save_to_database(self, test_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[IncomingCustomer]]:
        """Save semantic test data to database with embeddings"""
        logger.info("Saving semantic test data to database")
        
        saved_data = {}
        
        try:
            with self.SessionLocal() as db:
                for intensity, customers in test_data.items():
                    logger.info(f"Saving {len(customers)} {intensity} intensity customers")
                    saved_customers = []
                    
                    for customer_data in customers:
                        # Remove metadata fields
                        base_customer_id = customer_data.pop("base_customer_id", None)
                        variation_intensity = customer_data.pop("variation_intensity", None)
                        test_category = customer_data.pop("test_category", None)
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
                    
                    saved_data[intensity] = saved_customers
                    logger.info(f"Successfully saved {len(saved_customers)} {intensity} intensity customers")
                
                return saved_data
                
        except Exception as e:
            logger.error(f"Error saving semantic test data to database: {e}")
            raise

    def save_to_json(self, test_data: Dict[str, List[Dict[str, Any]]], output_path: str) -> bool:
        """Save semantic test data to JSON file for review"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, default=str)
            
            logger.info(f"Saved semantic test data to JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False

    def print_summary(self, test_data: Dict[str, List[Dict[str, Any]]], saved_data: Dict[str, List[IncomingCustomer]]):
        """Print summary of generated test data"""
        print("\n" + "="*60)
        print("SEMANTIC SIMILARITY TEST DATA GENERATION SUMMARY")
        print("="*60)
        
        for intensity in ["low", "medium", "high"]:
            customers = test_data[intensity]
            saved_customers = saved_data[intensity]
            
            print(f"\n📊 {intensity.upper()} INTENSITY ({len(customers)} customers):")
            print(f"   💾 Saved to database: {len(saved_customers)} records")
            print(f"   🆔 Request IDs: {[c.request_id for c in saved_customers[:5]]}{'...' if len(saved_customers) > 5 else ''}")
            
            # Show sample variations
            print(f"   📝 Sample variations:")
            for i, customer in enumerate(customers[:3]):
                print(f"      {i+1}. {customer['company_name']}")
        
        print(f"\n🎯 Total test data generated: {sum(len(customers) for customers in test_data.values())} customers")
        print(f"✅ Ready for vector matching semantic similarity tests!")
        print("="*60)


def main():
    """Main function to generate semantic similarity test data"""
    parser = argparse.ArgumentParser(description="Generate semantic similarity test data for vector matching")
    parser.add_argument("--count-per-intensity", type=int, default=20, 
                       help="Number of customers to generate per intensity level (default: 20)")
    parser.add_argument("--output-json", type=str, 
                       help="Optional JSON output file for review")
    parser.add_argument("--db-url", type=str, 
                       help="Database URL (defaults to settings)")
    
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
        generator = SemanticTestDataGenerator(db_url)
        
        # Generate semantic test data
        test_data = generator.create_semantic_test_data(
            count_per_intensity=args.count_per_intensity
        )
        
        # Save to database
        saved_data = generator.save_to_database(test_data)
        
        # Optionally save to JSON for review
        if args.output_json:
            generator.save_to_json(test_data, args.output_json)
        
        # Print summary
        generator.print_summary(test_data, saved_data)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 