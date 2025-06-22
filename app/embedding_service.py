"""Azure OpenAI embedding service for vector generation"""
import logging
import asyncio
from typing import List, Optional
import openai
from openai import AzureOpenAI
import numpy as np
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Azure OpenAI"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.deployment_name = settings.azure_openai_deployment_name
        self.max_tokens = 8191  # Maximum tokens for text-embedding-ada-002
        
    def _prepare_text(self, text: str) -> str:
        """Prepare text for embedding generation"""
        if not text:
            return ""
        
        # Clean and normalize text
        cleaned_text = text.strip().replace('\n', ' ').replace('\r', ' ')
        
        # Truncate if too long (rough estimation: 1 token ≈ 4 characters)
        max_chars = self.max_tokens * 3  # Conservative estimate
        if len(cleaned_text) > max_chars:
            cleaned_text = cleaned_text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")
        
        return cleaned_text
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        try:
            prepared_text = self._prepare_text(text)
            if not prepared_text:
                logger.warning("Empty text provided for embedding")
                return None
            
            response = self.client.embeddings.create(
                model=self.deployment_name,
                input=prepared_text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 16) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            try:
                # Prepare texts
                prepared_texts = [self._prepare_text(text) for text in batch]
                
                # Filter out empty texts but keep track of positions
                valid_texts = []
                valid_indices = []
                for idx, text in enumerate(prepared_texts):
                    if text:
                        valid_texts.append(text)
                        valid_indices.append(idx)
                
                if valid_texts:
                    response = self.client.embeddings.create(
                        model=self.deployment_name,
                        input=valid_texts
                    )
                    
                    # Map embeddings back to original positions
                    batch_results = [None] * len(batch)
                    for valid_idx, embedding_data in zip(valid_indices, response.data):
                        batch_results[valid_idx] = embedding_data.embedding
                    
                    batch_embeddings = batch_results
                else:
                    batch_embeddings = [None] * len(batch)
                
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}")
                batch_embeddings = [None] * len(batch)
            
            embeddings.extend(batch_embeddings)
            
            # Add small delay to avoid rate limiting
            if i + batch_size < len(texts):
                asyncio.sleep(0.1)
        
        return embeddings
    
    def create_customer_profile_text(self, customer_data: dict) -> str:
        """Create a comprehensive text profile for a customer"""
        profile_parts = []
        
        # Company information
        if customer_data.get('company_name'):
            profile_parts.append(f"Company: {customer_data['company_name']}")
        
        if customer_data.get('industry'):
            profile_parts.append(f"Industry: {customer_data['industry']}")
        
        # Contact information
        if customer_data.get('contact_name'):
            profile_parts.append(f"Contact: {customer_data['contact_name']}")
        
        if customer_data.get('email'):
            profile_parts.append(f"Email: {customer_data['email']}")
        
        # Location information
        location_parts = []
        for field in ['city', 'state_province', 'country']:
            if customer_data.get(field):
                location_parts.append(customer_data[field])
        
        if location_parts:
            profile_parts.append(f"Location: {', '.join(location_parts)}")
        
        # Business information
        if customer_data.get('annual_revenue'):
            profile_parts.append(f"Revenue: ${customer_data['annual_revenue']:,.0f}")
        
        if customer_data.get('employee_count'):
            profile_parts.append(f"Employees: {customer_data['employee_count']}")
        
        if customer_data.get('website'):
            profile_parts.append(f"Website: {customer_data['website']}")
        
        # Description
        if customer_data.get('description'):
            profile_parts.append(f"Description: {customer_data['description']}")
        
        return ". ".join(profile_parts)
    
    def generate_customer_embeddings(self, customer_data: dict) -> tuple[Optional[List[float]], Optional[List[float]]]:
        """Generate both company name and full profile embeddings for a customer"""
        
        # Company name embedding
        company_name = customer_data.get('company_name', '')
        company_embedding = self.generate_embedding(company_name) if company_name else None
        
        # Full profile embedding
        profile_text = self.create_customer_profile_text(customer_data)
        profile_embedding = self.generate_embedding(profile_text) if profile_text else None
        
        return company_embedding, profile_embedding
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def test_connection(self) -> bool:
        """Test connection to Azure OpenAI service"""
        try:
            test_embedding = self.generate_embedding("test connection")
            return test_embedding is not None
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            return False


# Global embedding service instance
embedding_service = EmbeddingService()

def get_embedding_service():
    """Get the global embedding service instance"""
    return embedding_service
