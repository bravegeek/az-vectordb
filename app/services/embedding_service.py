"""Azure OpenAI embedding service for Customer Matching POC"""
import logging
import time
from typing import List, Tuple, Optional
import openai
from openai import AzureOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Azure OpenAI"""
    
    def __init__(self):
        """Initialize the embedding service"""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        try:
            if settings.azure_openai_endpoint and settings.azure_openai_api_key:
                self.client = AzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version
                )
                logger.info("Azure OpenAI client initialized successfully")
            else:
                logger.warning("Azure OpenAI credentials not configured")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI client: {e}")
    
    def test_connection(self) -> bool:
        """Test connection to Azure OpenAI service"""
        try:
            if not self.client:
                return False
            
            # Test with a simple embedding request
            test_embedding = self.generate_text_embedding("test")
            return len(test_embedding) > 0
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            return False
    
    def generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string"""
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")
            
            response = self.client.embeddings.create(
                input=text,
                model=settings.azure_openai_deployment_name
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            raise
    
    def generate_customer_embeddings(self, customer_data: dict) -> Tuple[List[float], List[float]]:
        """Generate embeddings for customer company name and full profile"""
        try:
            # Generate company name embedding
            company_name = customer_data.get('company_name', '')
            company_embedding = self.generate_text_embedding(company_name)
            
            # Generate full profile embedding
            profile_text = self._build_customer_profile_text(customer_data)
            profile_embedding = self.generate_text_embedding(profile_text)
            
            return company_embedding, profile_embedding
            
        except Exception as e:
            logger.error(f"Error generating customer embeddings: {e}")
            raise
    
    def _build_customer_profile_text(self, customer_data: dict) -> str:
        """Build a comprehensive text representation of customer data for embedding"""
        profile_parts = []
        
        # Company information
        if customer_data.get('company_name'):
            profile_parts.append(f"Company: {customer_data['company_name']}")
        
        if customer_data.get('description'):
            profile_parts.append(f"Description: {customer_data['description']}")
        
        if customer_data.get('industry'):
            profile_parts.append(f"Industry: {customer_data['industry']}")
        
        # Contact information
        if customer_data.get('contact_name'):
            profile_parts.append(f"Contact: {customer_data['contact_name']}")
        
        if customer_data.get('email'):
            profile_parts.append(f"Email: {customer_data['email']}")
        
        if customer_data.get('phone'):
            profile_parts.append(f"Phone: {customer_data['phone']}")
        
        # Address information
        address_parts = []
        if customer_data.get('address_line1'):
            address_parts.append(customer_data['address_line1'])
        if customer_data.get('address_line2'):
            address_parts.append(customer_data['address_line2'])
        if customer_data.get('city'):
            address_parts.append(customer_data['city'])
        if customer_data.get('state_province'):
            address_parts.append(customer_data['state_province'])
        if customer_data.get('postal_code'):
            address_parts.append(customer_data['postal_code'])
        if customer_data.get('country'):
            address_parts.append(customer_data['country'])
        
        if address_parts:
            profile_parts.append(f"Address: {' '.join(address_parts)}")
        
        # Business information
        if customer_data.get('annual_revenue'):
            profile_parts.append(f"Annual Revenue: ${customer_data['annual_revenue']:,.2f}")
        
        if customer_data.get('employee_count'):
            profile_parts.append(f"Employees: {customer_data['employee_count']}")
        
        if customer_data.get('website'):
            profile_parts.append(f"Website: {customer_data['website']}")
        
        return " | ".join(profile_parts)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            if not self.client:
                raise ValueError("Azure OpenAI client not initialized")
            
            embeddings = []
            batch_size = settings.batch_size
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.client.embeddings.create(
                    input=batch,
                    model=settings.azure_openai_deployment_name
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
                # Add small delay to avoid rate limiting
                if i + batch_size < len(texts):
                    time.sleep(0.1)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


# Global service instance
embedding_service = EmbeddingService()

def get_embedding_service():
    """Get the global embedding service instance"""
    return embedding_service
