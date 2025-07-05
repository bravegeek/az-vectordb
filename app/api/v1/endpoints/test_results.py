"""Test results API endpoints"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import TestResultResponse, TestResultList
from app.services.test_result_processor import TestResultProcessor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=TestResultList)
async def get_test_results(
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get test results with optional filtering"""
    try:
        processor = TestResultProcessor()
        test_results = processor.get_test_results(
            test_type=test_type,
            status=status,
            limit=limit,
            offset=offset,
            db=db
        )
        
        # Get total count for pagination
        total_count = len(test_results)  # This is simplified - in production you'd want a separate count query
        
        return TestResultList(
            test_results=test_results,
            total_count=total_count,
            page=(offset // limit) + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}", response_model=TestResultResponse)
async def get_test_result(test_id: int, db: Session = Depends(get_db)):
    """Get a specific test result by ID"""
    try:
        processor = TestResultProcessor()
        test_result = processor.get_test_result(test_id, db)
        
        if not test_result:
            raise HTTPException(
                status_code=404,
                detail=f"Test result with ID {test_id} not found"
            )
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test result {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/summary")
async def get_test_statistics(db: Session = Depends(get_db)):
    """Get aggregate statistics about test results"""
    try:
        processor = TestResultProcessor()
        statistics = processor.get_test_statistics(db)
        
        return {
            "statistics": statistics,
            "message": "Test statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving test statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types/semantic-similarity", response_model=List[TestResultResponse])
async def get_semantic_similarity_tests(
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Get semantic similarity test results specifically"""
    try:
        processor = TestResultProcessor()
        test_results = processor.get_test_results(
            test_type="semantic_similarity",
            limit=limit,
            db=db
        )
        
        return test_results
        
    except Exception as e:
        logger.error(f"Error retrieving semantic similarity test results: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 