"""Matching endpoints for Customer Matching POC"""

import logging
import time
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.database import IncomingCustomer, MatchingResult, Customer
from app.models.schemas import CustomerMatchResponse, MatchResult
from app.services.matching.matching_service import matching_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{request_id}", response_model=CustomerMatchResponse)
async def process_customer_matching(request_id: int, db: Session = Depends(get_db)):
    """Process matching for an incoming customer using hybrid approach"""
    start_time = time.time()
    
    try:
        # Get incoming customer
        incoming_customer = db.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == request_id
        ).first()
        
        if not incoming_customer:
            raise HTTPException(
                status_code=404, 
                detail=f"Incoming customer with request_id {request_id} not found"
            )
        
        # Process matching using the matching service
        matches = matching_service.find_matches(incoming_customer, db)
        
        # Update processing status
        incoming_customer.processing_status = "completed"  # type: ignore
        incoming_customer.processed_date = datetime.fromtimestamp(time.time())  # type: ignore
        db.commit()
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return CustomerMatchResponse(
            incoming_customer=incoming_customer,
            matches=matches,
            total_matches=len(matches),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing matching for request_id {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hybrid/{request_id}", response_model=CustomerMatchResponse)
async def process_customer_matching_hybrid(request_id: int, db: Session = Depends(get_db)):
    """Process matching for an incoming customer using hybrid approach"""
    start_time = time.time()
    
    try:
        # Get incoming customer
        incoming_customer = db.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == request_id
        ).first()
        
        if not incoming_customer:
            raise HTTPException(
                status_code=404, 
                detail=f"Incoming customer with request_id {request_id} not found"
            )
        
        # Process hybrid matching
        matches = matching_service.find_matches_hybrid(incoming_customer, db)
        
        # Update processing status
        incoming_customer.processing_status = "completed"
        incoming_customer.processed_date = datetime.fromtimestamp(time.time())
        db.commit()
        
        processing_time = (time.time() - start_time) * 1000
        
        return CustomerMatchResponse(
            incoming_customer=incoming_customer,
            matches=matches,
            total_matches=len(matches),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing hybrid matching for request_id {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exact/{request_id}", response_model=CustomerMatchResponse)
async def process_customer_matching_exact(request_id: int, db: Session = Depends(get_db)):
    """Process matching for an incoming customer using exact matching only"""
    start_time = time.time()
    
    try:
        # Get incoming customer
        incoming_customer = db.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == request_id
        ).first()
        
        if not incoming_customer:
            raise HTTPException(
                status_code=404, 
                detail=f"Incoming customer with request_id {request_id} not found"
            )
        
        # Process exact matching
        matches = matching_service.find_exact_matches(incoming_customer, db)
        
        # Update processing status
        incoming_customer.processing_status = "completed"
        incoming_customer.processed_date = datetime.fromtimestamp(time.time())
        db.commit()
        
        processing_time = (time.time() - start_time) * 1000
        
        return CustomerMatchResponse(
            incoming_customer=incoming_customer,
            matches=matches,
            total_matches=len(matches),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing exact matching for request_id {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{request_id}", response_model=List[MatchResult])
async def get_matching_results(request_id: int, db: Session = Depends(get_db)):
    """Get matching results for an incoming customer"""
    try:
        # Get matching results
        results = db.query(MatchingResult).filter(
            MatchingResult.incoming_customer_id == request_id
        ).order_by(desc(MatchingResult.similarity_score)).all()
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No matching results found for request_id {request_id}"
            )
        
        # Convert to response format
        match_results = []
        for result in results:
            matched_customer = db.query(Customer).filter(
                Customer.customer_id == result.matched_customer_id
            ).first()
            
            if matched_customer:
                match_results.append(MatchResult(
                    match_id=result.match_id,
                    matched_customer_id=result.matched_customer_id,
                    matched_company_name=matched_customer.company_name,
                    matched_contact_name=matched_customer.contact_name,
                    matched_email=matched_customer.email,
                    similarity_score=float(result.similarity_score or 0.0),
                    match_type=result.match_type,
                    confidence_level=float(result.confidence_level or 0.0),
                    match_criteria=result.match_criteria or {},
                    created_date=result.created_date
                ))
        
        return match_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matching results for request_id {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 