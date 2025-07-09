"""Vector similarity matching strategy for customer matching"""
import logging
import numpy as np
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.database import IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema
from .base_matcher import BaseMatcher
from .business_rules import BusinessRulesEngine
from .utils import MatchingUtils

logger = logging.getLogger(__name__)


class VectorMatcher(BaseMatcher):
    """Handles vector similarity matching using embeddings"""
    
    def __init__(self):
        """Initialize vector matcher with business rules engine"""
        self.business_rules = BusinessRulesEngine()
    
    def is_enabled(self) -> bool:
        """Check if vector matching is enabled"""
        return settings.enable_vector_matching
    
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using vector similarity"""
        if not self.is_enabled():
            return []
        
        if incoming_customer.full_profile_embedding is None:
            return []
        
        matches = []
        query_embedding = self._prepare_embedding(incoming_customer.full_profile_embedding)
        
        # Query for vector similarity matches
        results = self._execute_vector_query(query_embedding, db)
        
        for row in results:
            similarity_score = float(row.similarity_score)
            match_type = self._determine_match_type(similarity_score)
            
            # Apply business rules for confidence calculation
            confidence = self.business_rules.apply_rules(similarity_score, incoming_customer, row)
            
            matches.append(MatchResultSchema(
                match_id=0,
                matched_customer_id=row.customer_id,
                matched_company_name=row.company_name,
                matched_contact_name=row.contact_name,
                matched_email=row.email,
                similarity_score=similarity_score,
                match_type=match_type,
                confidence_level=confidence,
                match_criteria={"vector_similarity": True, "embedding_score": similarity_score},
                created_date=datetime.now()
            ))
        
        return matches
    
    def _prepare_embedding(self, embedding) -> List[float]:
        """Convert numpy array to list if needed and validate normalization"""
        if isinstance(embedding, np.ndarray):
            embedding_list = embedding.tolist()
        else:
            embedding_list = embedding
        
        # Validate embedding is normalized for accurate cosine similarity
        # For production, embeddings should have magnitude ~1.0
        magnitude = sum(x * x for x in embedding_list) ** 0.5
        if not (0.99 <= magnitude <= 1.01):
            logger.warning(f"Embedding not normalized: magnitude={magnitude:.4f}")
        
        return embedding_list
    
    def _execute_vector_query(self, query_embedding: List[float], db: Session):
        """Execute vector similarity query with optimized distance calculation"""
        query = text("""
            WITH distance_calc AS (
                SELECT 
                    customer_id, 
                    company_name, 
                    contact_name, 
                    email,
                    full_profile_embedding <=> CAST(:query_embedding AS vector(1536)) as distance
                FROM customer_data.customers 
                WHERE full_profile_embedding IS NOT NULL
            )
            SELECT 
                customer_id, 
                company_name, 
                contact_name, 
                email,
                (1 - distance) as similarity_score
            FROM distance_calc
            WHERE (1 - distance) > :threshold
            ORDER BY distance  -- Sort by distance (ascending = most similar first)
            LIMIT :max_results
        """)
        
        return db.execute(
            query,
            {
                "query_embedding": query_embedding,
                "threshold": settings.vector_similarity_threshold,
                "max_results": settings.vector_max_results
            }
        ).fetchall()
    
    def _determine_match_type(self, score: float) -> str:
        """Determine match type based on similarity score"""
        return MatchingUtils.determine_match_type(
            score, 
            settings.high_confidence_threshold,
            settings.default_similarity_threshold,
            settings.potential_match_threshold
        )
    
    def _log_query_performance(self, query_time: float, result_count: int):
        """Log performance metrics for monitoring"""
        logger.info(f"Vector query: {query_time:.3f}s, {result_count} results")
        
        if query_time > 1.0:  # Threshold for slow queries
            logger.warning(f"Slow vector query detected: {query_time:.3f}s") 