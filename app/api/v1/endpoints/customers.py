"""Customer endpoints for Customer Matching POC"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import Customer, IncomingCustomer
from app.models.schemas import (
    CustomerCreate, CustomerResponse, IncomingCustomerCreate, 
    IncomingCustomerResponse, SimilaritySearchRequest, SimilaritySearchResult
)
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer with embeddings"""
    try:
        # Generate embeddings
        company_embedding, profile_embedding = embedding_service.generate_customer_embeddings(
            customer.dict()
        )
        
        # Create customer record
        db_customer = Customer(
            **customer.dict(),
            company_name_embedding=company_embedding,
            full_profile_embedding=profile_embedding
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        logger.info(f"Created customer: {customer.company_name}")
        return db_customer
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all customers"""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers


@router.post("/incoming", response_model=IncomingCustomerResponse)
async def create_incoming_customer(customer: IncomingCustomerCreate, db: Session = Depends(get_db)):
    """Create an incoming customer request with embeddings"""
    try:
        # Generate embeddings
        company_embedding, profile_embedding = embedding_service.generate_customer_embeddings(
            customer.dict()
        )
        
        # Create incoming customer record
        db_incoming = IncomingCustomer(
            **customer.dict(),
            company_name_embedding=company_embedding,
            full_profile_embedding=profile_embedding
        )
        
        db.add(db_incoming)
        db.commit()
        db.refresh(db_incoming)
        
        logger.info(f"Created incoming customer request: {customer.company_name}")
        return db_incoming
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating incoming customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incoming", response_model=List[IncomingCustomerResponse])
async def list_incoming_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all incoming customers"""
    incoming_customers = db.query(IncomingCustomer).offset(skip).limit(limit).all()
    return incoming_customers


@router.post("/search", response_model=List[SimilaritySearchResult])
async def search_similar_customers(
    search_request: SimilaritySearchRequest,
    db: Session = Depends(get_db)
):
    """Search for similar customers using text query"""
    try:
        # Generate embedding for search query
        query_embedding = embedding_service.generate_text_embedding(search_request.query_text)
        
        # Search for similar customers using vector similarity
        from sqlalchemy import text
        query = text("""
            SELECT 
                customer_id, company_name, contact_name, email, city, country,
                1 - (full_profile_embedding <=> CAST(:query_embedding AS vector(1536))) as similarity_score
            FROM customer_data.customers 
            WHERE 1 - (full_profile_embedding <=> CAST(:query_embedding AS vector(1536))) > :threshold
            ORDER BY full_profile_embedding <=> CAST(:query_embedding AS vector(1536))
            LIMIT :max_results
        """)
        
        results = db.execute(
            query,
            {
                "query_embedding": query_embedding,
                "threshold": search_request.similarity_threshold,
                "max_results": search_request.max_results
            }
        ).fetchall()
        
        return [
            SimilaritySearchResult(
                customer_id=row.customer_id,
                company_name=row.company_name,
                contact_name=row.contact_name,
                email=row.email,
                city=row.city,
                country=row.country,
                similarity_score=float(row.similarity_score)
            )
            for row in results
        ]
        
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 