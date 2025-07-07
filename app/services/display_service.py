"""Display service for matching results presentation"""
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, and_, or_

from app.models.database import Customer, IncomingCustomer, MatchingResult
from app.models.schemas import (
    DetailedMatchDisplay, MatchedCustomerDetail, MatchSummary, ProcessingMetadata,
    MatchFilters, PaginationParams, BulkMatchDisplay, MatchSummaryDisplay,
    ComparisonHighlight, ConfidenceBreakdown, ConfidenceLevel, MatchType,
    CustomerResponse, IncomingCustomerResponse, MatchResult, ProcessingStatus
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class MatchDisplayService:
    """Service for displaying matching results in various formats"""
    
    def __init__(self):
        """Initialize the display service"""
        self.high_confidence_threshold = 0.9
        self.medium_confidence_threshold = 0.7
        self.low_confidence_threshold = 0.5
    
    def _safe_decimal_to_float(self, value: Any) -> float:
        """Safely convert SQLAlchemy Decimal to float"""
        if value is None:
            return 0.0
        return float(value)
    
    def _safe_dict_from_json(self, value: Any) -> Dict[str, Any]:
        """Safely convert SQLAlchemy JSON to dict"""
        if value is None:
            return {}
        return dict(value) if isinstance(value, dict) else {}
        
    def get_detailed_match_view(self, request_id: int, db: Session) -> DetailedMatchDisplay:
        """Get comprehensive match display for a specific incoming customer"""
        try:
            logger.info(f"Getting detailed match view for request_id: {request_id}")
            
            # Get incoming customer
            incoming_customer = db.query(IncomingCustomer).filter(
                IncomingCustomer.request_id == request_id
            ).first()
            
            if not incoming_customer:
                logger.warning(f"Incoming customer not found for request_id: {request_id}")
                raise ValueError(f"Incoming customer with request_id {request_id} not found")
            
            # Get matches with eager loading of relationships
            matches = db.query(MatchingResult).options(
                joinedload(MatchingResult.matched_customer)
            ).filter(
                MatchingResult.incoming_customer_id == request_id
            ).order_by(desc(MatchingResult.confidence_level)).all()
            
            logger.info(f"Found {len(matches)} matches for request_id: {request_id}")
            
            # Build detailed response
            match_details = []
            for match in matches:
                matched_customer = match.matched_customer
                
                if matched_customer:
                    comparison_highlights = self.get_comparison_highlights(
                        incoming_customer, matched_customer
                    )
                    
                    confidence_breakdown = calculate_confidence_breakdown(match)
                    confidence_level = self._safe_decimal_to_float(match.confidence_level)
                    confidence_category = self._get_confidence_category(confidence_level)
                    
                    match_details.append(MatchedCustomerDetail(
                        customer_info=CustomerResponse.model_validate(matched_customer),
                        match_details=MatchResult(
                            match_id=match.match_id,
                            matched_customer_id=match.matched_customer_id,
                            matched_company_name=matched_customer.company_name,
                            matched_contact_name=matched_customer.contact_name,
                            matched_email=matched_customer.email,
                            similarity_score=self._safe_decimal_to_float(match.similarity_score),
                            match_type=match.match_type,
                            confidence_level=confidence_level,
                            match_criteria=self._safe_dict_from_json(match.match_criteria),
                            created_date=match.created_date,
                            reviewed=match.reviewed,
                            reviewer_notes=match.reviewer_notes
                        ),
                        comparison_highlights=comparison_highlights,
                        confidence_breakdown=confidence_breakdown,
                        confidence_category=confidence_category
                    ))
            
            # Generate summary and metadata
            match_summary = generate_match_summary(matches)
            processing_metadata = generate_processing_metadata(incoming_customer)
            
            return DetailedMatchDisplay(
                incoming_customer=IncomingCustomerResponse.model_validate(incoming_customer),
                matched_customers=match_details,
                match_summary=match_summary,
                processing_metadata=processing_metadata
            )
            
        except Exception as e:
            logger.error(f"Error getting detailed match display for request_id {request_id}: {str(e)}")
            raise
    
    def get_bulk_matches(self, filters: MatchFilters, pagination: PaginationParams, db: Session) -> BulkMatchDisplay:
        """Get filtered and paginated matches"""
        try:
            logger.info(f"Getting bulk matches with filters: {filters.model_dump() if filters else None}")
            
            # Build base query with eager loading
            query = db.query(MatchingResult).options(
                joinedload(MatchingResult.incoming_customer),
                joinedload(MatchingResult.matched_customer)
            )
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination and ordering
            offset = (pagination.page - 1) * pagination.page_size
            matches = query.order_by(desc(MatchingResult.confidence_level)).offset(offset).limit(pagination.page_size).all()
            
            # Build detailed match list
            match_details = []
            for match in matches:
                incoming_customer = match.incoming_customer
                matched_customer = match.matched_customer
                
                comparison_highlights = self.get_comparison_highlights(incoming_customer, matched_customer)
                confidence_breakdown = calculate_confidence_breakdown(match)
                confidence_level = self._safe_decimal_to_float(match.confidence_level)
                confidence_category = self._get_confidence_category(confidence_level)
                
                match_details.append(MatchedCustomerDetail(
                    customer_info=CustomerResponse.model_validate(matched_customer),
                    match_details=MatchResult(
                        match_id=match.match_id,
                        matched_customer_id=match.matched_customer_id,
                        matched_company_name=matched_customer.company_name,
                        matched_contact_name=matched_customer.contact_name,
                        matched_email=matched_customer.email,
                        similarity_score=self._safe_decimal_to_float(match.similarity_score),
                        match_type=match.match_type,
                        confidence_level=confidence_level,
                        match_criteria=self._safe_dict_from_json(match.match_criteria),
                        created_date=match.created_date,
                        reviewed=match.reviewed,
                        reviewer_notes=match.reviewer_notes
                    ),
                    comparison_highlights=comparison_highlights,
                    confidence_breakdown=confidence_breakdown,
                    confidence_category=confidence_category
                ))
            
            # Generate summary stats
            summary_stats = self._generate_bulk_summary_stats(query, db)
            
            return BulkMatchDisplay(
                matches=match_details,
                pagination=pagination,
                total_count=total_count,
                filters_applied=filters,
                summary_stats=summary_stats
            )
            
        except Exception as e:
            logger.error(f"Error getting bulk matches: {str(e)}")
            raise
    
    def get_match_summary(self, db: Session) -> MatchSummaryDisplay:
        """Get overall matching statistics"""
        try:
            logger.info("Getting match summary statistics")
            
            # Get basic counts
            total_incoming = db.query(IncomingCustomer).count()
            total_matches = db.query(MatchingResult).count()
            processed_customers = db.query(IncomingCustomer).filter(
                IncomingCustomer.processing_status == "completed"
            ).count()
            pending_customers = db.query(IncomingCustomer).filter(
                IncomingCustomer.processing_status == "pending"
            ).count()
            
            # Get review status counts
            approved_matches = db.query(MatchingResult).filter(
                MatchingResult.reviewed == True,
                MatchingResult.reviewer_notes.like('%approved%')
            ).count()
            rejected_matches = db.query(MatchingResult).filter(
                MatchingResult.reviewed == True,
                MatchingResult.reviewer_notes.like('%rejected%')
            ).count()
            
            # Get average processing time (placeholder - would need actual timing data)
            average_processing_time = None
            
            # Get match type distribution
            match_distribution = {}
            match_types = db.query(
                MatchingResult.match_type, 
                func.count(MatchingResult.match_id).label('count')
            ).group_by(MatchingResult.match_type).all()
            
            for match_type, count in match_types:
                match_distribution[match_type or 'unknown'] = count
            
            # Get confidence distribution
            confidence_distribution = {}
            confidence_counts = db.query(
                func.case(
                    (MatchingResult.confidence_level >= self.high_confidence_threshold, 'high'),
                    (MatchingResult.confidence_level >= self.medium_confidence_threshold, 'medium'),
                    else_='low'
                ).label('confidence_category'),
                func.count(MatchingResult.match_id).label('count')
            ).group_by('confidence_category').all()
            
            for category, count in confidence_counts:
                confidence_distribution[category] = count
            
            return MatchSummaryDisplay(
                total_incoming_customers=total_incoming,
                total_matches=total_matches,
                processed_customers=processed_customers,
                pending_customers=pending_customers,
                approved_matches=approved_matches,
                rejected_matches=rejected_matches,
                average_processing_time_ms=average_processing_time,
                match_distribution=match_distribution,
                confidence_distribution=confidence_distribution
            )
            
        except Exception as e:
            logger.error(f"Error getting match summary: {str(e)}")
            raise
    
    def get_comparison_highlights(self, incoming_customer: IncomingCustomer, matched_customer: Customer) -> List[ComparisonHighlight]:
        """Generate side-by-side comparison highlights"""
        try:
            highlights = []
            
            # Define fields to compare
            field_mappings = [
                ('company_name', 'Company Name'),
                ('contact_name', 'Contact Name'),
                ('email', 'Email'),
                ('phone', 'Phone'),
                ('industry', 'Industry'),
                ('annual_revenue', 'Annual Revenue'),
                ('city', 'City'),
                ('state_province', 'State/Province'),
                ('country', 'Country'),
                ('website', 'Website')
            ]
            
            for field_name, display_name in field_mappings:
                incoming_value = getattr(incoming_customer, field_name)
                matched_value = getattr(matched_customer, field_name)
                
                # Convert to string for comparison
                incoming_str = str(incoming_value) if incoming_value is not None else None
                matched_str = str(matched_value) if matched_value is not None else None
                
                # Determine match status and similarity
                match_status, similarity_score = generate_field_comparison(incoming_str, matched_str)
                
                highlights.append(ComparisonHighlight(
                    field_name=display_name,
                    incoming_value=incoming_str,
                    matched_value=matched_str,
                    match_status=match_status,
                    similarity_score=similarity_score
                ))
            
            return highlights
            
        except Exception as e:
            logger.error(f"Error generating comparison highlights: {str(e)}")
            raise
    
    def _apply_filters(self, query, filters: MatchFilters):
        """Apply filters to the query using proper SQLAlchemy patterns"""
        if filters.confidence_min is not None:
            query = query.filter(MatchingResult.confidence_level >= filters.confidence_min)
        
        if filters.confidence_max is not None:
            query = query.filter(MatchingResult.confidence_level <= filters.confidence_max)
        
        if filters.match_types:
            query = query.filter(MatchingResult.match_type.in_([mt.value for mt in filters.match_types]))
        
        # For filters that require joins, add them conditionally
        needs_incoming_join = filters.processing_status or filters.industries or filters.companies
        needs_customer_join = filters.industries or filters.companies
        
        if needs_incoming_join:
            query = query.join(MatchingResult.incoming_customer)
        
        if needs_customer_join:
            query = query.join(MatchingResult.matched_customer)
        
        if filters.processing_status:
            query = query.filter(IncomingCustomer.processing_status.in_([ps.value for ps in filters.processing_status]))
        
        if filters.date_from:
            query = query.filter(MatchingResult.created_date >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(MatchingResult.created_date <= filters.date_to)
        
        if filters.industries:
            query = query.filter(or_(
                IncomingCustomer.industry.in_(filters.industries),
                Customer.industry.in_(filters.industries)
            ))
        
        if filters.companies:
            company_conditions = []
            for company in filters.companies:
                company_conditions.extend([
                    IncomingCustomer.company_name.ilike(f'%{company}%'),
                    Customer.company_name.ilike(f'%{company}%')
                ])
            query = query.filter(or_(*company_conditions))
        
        if filters.reviewed is not None:
            query = query.filter(MatchingResult.reviewed == filters.reviewed)
        
        return query
    
    def _get_confidence_category(self, confidence_level: float) -> ConfidenceLevel:
        """Get confidence category based on threshold"""
        if confidence_level >= self.high_confidence_threshold:
            return ConfidenceLevel.HIGH
        elif confidence_level >= self.medium_confidence_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_bulk_summary_stats(self, query, db: Session) -> Dict[str, Any]:
        """Generate summary statistics for bulk display"""
        try:
            # Get confidence distribution for filtered results
            confidence_stats = query.with_entities(
                func.avg(MatchingResult.confidence_level).label('avg_confidence'),
                func.max(MatchingResult.confidence_level).label('max_confidence'),
                func.min(MatchingResult.confidence_level).label('min_confidence')
            ).first()
            
            # Get match type distribution
            match_type_counts = query.with_entities(
                MatchingResult.match_type,
                func.count(MatchingResult.match_id).label('count')
            ).group_by(MatchingResult.match_type).all()
            
            match_types = {match_type: count for match_type, count in match_type_counts}
            
            return {
                'average_confidence': self._safe_decimal_to_float(confidence_stats.avg_confidence),
                'max_confidence': self._safe_decimal_to_float(confidence_stats.max_confidence),
                'min_confidence': self._safe_decimal_to_float(confidence_stats.min_confidence),
                'match_type_distribution': match_types
            }
            
        except Exception as e:
            logger.error(f"Error generating bulk summary stats: {str(e)}")
            return {}


# Helper Functions
def generate_comparison_highlights(incoming_customer: IncomingCustomer, matched_customer: Customer) -> List[ComparisonHighlight]:
    """Generate side-by-side comparison highlights"""
    service = MatchDisplayService()
    return service.get_comparison_highlights(incoming_customer, matched_customer)


def calculate_confidence_breakdown(match: MatchingResult) -> ConfidenceBreakdown:
    """Calculate detailed confidence factors for a match"""
    try:
        # Extract match criteria if available
        criteria = match.match_criteria or {}
        
        # Default breakdown based on match type and overall confidence
        overall_confidence = float(match.confidence_level) if match.confidence_level else 0.0
        
        # For exact matches, assign high scores to matched fields
        if match.match_type == 'exact':
            return ConfidenceBreakdown(
                company_name_score=1.0,
                contact_name_score=criteria.get('contact_name_match', 0.8),
                email_score=criteria.get('email_match', 0.9),
                phone_score=criteria.get('phone_match', 0.8),
                address_score=criteria.get('address_match', 0.7),
                industry_score=criteria.get('industry_match', 0.9),
                revenue_score=criteria.get('revenue_match', 0.6),
                overall_score=overall_confidence
            )
        
        # For other matches, distribute confidence across fields
        base_score = overall_confidence * 0.7  # Base score for each field
        variation = overall_confidence * 0.3   # Variation based on field importance
        
        return ConfidenceBreakdown(
            company_name_score=min(1.0, base_score + variation * 0.9),  # Company name most important
            contact_name_score=min(1.0, base_score + variation * 0.7),
            email_score=min(1.0, base_score + variation * 0.8),
            phone_score=min(1.0, base_score + variation * 0.6),
            address_score=min(1.0, base_score + variation * 0.5),
            industry_score=min(1.0, base_score + variation * 0.8),
            revenue_score=min(1.0, base_score + variation * 0.4),
            overall_score=overall_confidence
        )
        
    except Exception as e:
        logger.error(f"Error calculating confidence breakdown: {str(e)}")
        # Return default breakdown
        return ConfidenceBreakdown(
            company_name_score=0.5,
            contact_name_score=0.5,
            email_score=0.5,
            phone_score=0.5,
            address_score=0.5,
            industry_score=0.5,
            revenue_score=0.5,
            overall_score=0.5
        )


def generate_match_summary(matches: List[MatchingResult]) -> MatchSummary:
    """Generate aggregated match statistics"""
    try:
        total_matches = len(matches)
        
        if total_matches == 0:
            return MatchSummary(
                total_matches=0,
                high_confidence_matches=0,
                medium_confidence_matches=0,
                low_confidence_matches=0,
                exact_matches=0,
                potential_matches=0,
                average_confidence=0.0,
                processing_time_ms=0.0,
                recommendation="No matches found"
            )
        
        # Categorize matches by confidence
        high_confidence = sum(1 for m in matches if m.confidence_level and m.confidence_level >= 0.9)
        medium_confidence = sum(1 for m in matches if m.confidence_level and 0.7 <= m.confidence_level < 0.9)
        low_confidence = sum(1 for m in matches if m.confidence_level and m.confidence_level < 0.7)
        
        # Categorize by match type
        exact_matches = sum(1 for m in matches if m.match_type == 'exact')
        potential_matches = sum(1 for m in matches if m.match_type in ['potential', 'high_confidence'])
        
        # Calculate average confidence
        confidence_scores = [float(m.confidence_level) for m in matches if m.confidence_level]
        average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Generate recommendation
        if exact_matches > 0:
            recommendation = "Exact matches found - Review recommended"
        elif high_confidence > 0:
            recommendation = "High confidence matches found - Consider auto-approval"
        elif medium_confidence > 0:
            recommendation = "Medium confidence matches - Manual review required"
        else:
            recommendation = "Low confidence matches - Thorough review needed"
        
        return MatchSummary(
            total_matches=total_matches,
            high_confidence_matches=high_confidence,
            medium_confidence_matches=medium_confidence,
            low_confidence_matches=low_confidence,
            exact_matches=exact_matches,
            potential_matches=potential_matches,
            average_confidence=average_confidence,
            processing_time_ms=None,  # Would need actual timing data
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"Error generating match summary: {str(e)}")
        return MatchSummary(
            total_matches=0,
            high_confidence_matches=0,
            medium_confidence_matches=0,
            low_confidence_matches=0,
            exact_matches=0,
            potential_matches=0,
            average_confidence=0.0,
            processing_time_ms=0.0,
            recommendation="Error generating summary"
        )


def generate_processing_metadata(incoming_customer: IncomingCustomer) -> ProcessingMetadata:
    """Generate processing metadata for request tracking"""
    try:
        return ProcessingMetadata(
            request_date=incoming_customer.request_date,  # type: ignore
            processed_date=incoming_customer.processed_date,  # type: ignore
            processing_status=ProcessingStatus(incoming_customer.processing_status),  # type: ignore
            match_strategies_used=["hybrid"],  # Could be extracted from match criteria
            total_processing_time_ms=None,  # Would need actual timing data
            error_message=None,
            retry_count=0
        )
        
    except Exception as e:
        logger.error(f"Error generating processing metadata: {str(e)}")
        return ProcessingMetadata(
            request_date=datetime.now(),
            processed_date=None,
            processing_status=ProcessingStatus.FAILED,
            match_strategies_used=[],
            total_processing_time_ms=None,
            error_message=str(e),
            retry_count=0
        )


def generate_field_comparison(incoming_value: Optional[str], matched_value: Optional[str]) -> tuple[str, Optional[float]]:
    """Generate field comparison status and similarity score"""
    try:
        # Handle None values
        if incoming_value is None and matched_value is None:
            return "missing", None
        elif incoming_value is None or matched_value is None:
            return "missing", None
        
        # Exact match
        if incoming_value.lower().strip() == matched_value.lower().strip():
            return "exact", 1.0
        
        # Calculate similarity (simple approach)
        # In a real implementation, you might use more sophisticated similarity algorithms
        incoming_clean = incoming_value.lower().strip()
        matched_clean = matched_value.lower().strip()
        
        # Check if one contains the other
        if incoming_clean in matched_clean or matched_clean in incoming_clean:
            return "similar", 0.8
        
        # Simple character-based similarity
        common_chars = set(incoming_clean) & set(matched_clean)
        all_chars = set(incoming_clean) | set(matched_clean)
        
        if len(all_chars) == 0:
            similarity = 0.0
        else:
            similarity = len(common_chars) / len(all_chars)
        
        if similarity > 0.6:
            return "similar", similarity
        else:
            return "different", similarity
            
    except Exception as e:
        logger.error(f"Error in field comparison: {str(e)}")
        return "different", 0.0


# Global service instance
display_service = MatchDisplayService() 