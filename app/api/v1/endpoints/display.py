"""Display endpoints for Customer Matching POC - Enhanced Results Display"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import (
    MatchSummaryDisplay, PaginationParams, MatchFilters, 
    DetailedMatchDisplay, BulkMatchDisplay, MatchType, ProcessingStatus
)
from app.services.display_service import MatchDisplayService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize display service
display_service = MatchDisplayService()


@router.get("/matches/summary", response_model=MatchSummaryDisplay)
async def get_matches_summary(
    db: Session = Depends(get_db)
):
    """Get summary view of all matching results with key metrics
    
    Returns:
        MatchSummaryDisplay: Summary statistics including:
        - Total incoming customers and matches
        - Processing status distribution
        - Match type and confidence distributions
        - Average processing times
    """
    try:
        logger.info("Getting matches summary")
        
        summary = display_service.get_match_summary(db)
        
        logger.info(f"Retrieved summary with {summary.total_matches} total matches")
        return summary
        
    except Exception as e:
        logger.error(f"Error getting matches summary: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving matches summary: {str(e)}"
        )


@router.get("/matches/detailed/{request_id}", response_model=DetailedMatchDisplay)
async def get_detailed_match_display(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed match display for a specific incoming customer
    
    Args:
        request_id: ID of the incoming customer to display matches for
        
    Returns:
        DetailedMatchDisplay: Comprehensive match details including:
        - Incoming customer information
        - All matched customers with detailed comparison
        - Side-by-side field comparisons
        - Confidence breakdowns
        - Processing metadata
    """
    try:
        logger.info(f"Getting detailed match display for request_id: {request_id}")
        
        detailed_display = display_service.get_detailed_match_view(request_id, db)
        
        logger.info(f"Retrieved detailed display with {len(detailed_display.matched_customers)} matches")
        return detailed_display
        
    except ValueError as e:
        logger.warning(f"Invalid request_id {request_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting detailed match display for request_id {request_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving detailed match display: {str(e)}"
        )


@router.get("/matches/bulk", response_model=BulkMatchDisplay)
async def get_bulk_matches(
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(25, ge=1, le=100, description="Number of items per page (1-100)"),
    
    # Sorting parameters
    sort_by: str = Query("confidence_level", description="Field to sort by (confidence_level, created_date, company_name)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    
    # Filter parameters
    confidence_min: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence level (0-1)"),
    confidence_max: Optional[float] = Query(None, ge=0, le=1, description="Maximum confidence level (0-1)"),
    match_types: Optional[str] = Query(None, description="Comma-separated match types to filter by"),
    processing_status: Optional[str] = Query(None, description="Comma-separated processing statuses to filter by"),
    reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    
    db: Session = Depends(get_db)
):
    """Get bulk display of matches with filtering and pagination
    
    Args:
        page: Page number (starting from 1)
        page_size: Number of items per page (1-100)
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        confidence_min: Minimum confidence level filter
        confidence_max: Maximum confidence level filter
        match_types: Comma-separated match types filter
        processing_status: Comma-separated processing statuses filter
        reviewed: Filter by review status
        
    Returns:
        BulkMatchDisplay: Paginated list of matches with:
        - Match details with comparison highlights
        - Pagination metadata
        - Applied filters
        - Summary statistics
    """
    try:
        logger.info(f"Getting bulk matches - page: {page}, size: {page_size}, sort: {sort_by} {sort_order}")
        
        # Build pagination params
        pagination = PaginationParams(page=page, page_size=page_size)
        
        # Parse match types
        match_type_list = None
        if match_types:
            try:
                match_type_list = [MatchType(mt.strip()) for mt in match_types.split(',')]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid match type: {str(e)}")
                
        # Parse processing status
        status_list = None
        if processing_status:
            try:
                status_list = [ProcessingStatus(ps.strip()) for ps in processing_status.split(',')]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid processing status: {str(e)}")
        
        # Build filters with all parameters
        filters = MatchFilters(
            confidence_min=confidence_min,
            confidence_max=confidence_max,
            match_types=match_type_list,
            processing_status=status_list,
            date_from=None,
            date_to=None,
            industries=None,
            companies=None,
            reviewed=reviewed
        )
        
        # Get bulk matches
        bulk_display = display_service.get_bulk_matches(filters, pagination, db)
        
        logger.info(f"Retrieved {len(bulk_display.matches)} matches out of {bulk_display.total_count} total")
        return bulk_display
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bulk matches: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving bulk matches: {str(e)}"
        ) 