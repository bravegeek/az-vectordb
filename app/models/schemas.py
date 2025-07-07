"""Pydantic schemas for Customer Matching POC API"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level categories"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MatchType(str, Enum):
    """Match types for classification"""
    EXACT = "exact"
    HIGH_CONFIDENCE = "high_confidence"
    POTENTIAL = "potential"
    LOW_CONFIDENCE = "low_confidence"


class ProcessingStatus(str, Enum):
    """Processing status for incoming customers"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CustomerBase(BaseModel):
    """Base customer model for API"""
    company_name: str = Field(..., min_length=1, description="Company name (cannot be empty)")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address_line1: Optional[str] = Field(None, description="Address line 1")
    address_line2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state_province: Optional[str] = Field(None, description="State or province")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(None, description="Country")
    industry: Optional[str] = Field(None, description="Industry")
    annual_revenue: Optional[float] = Field(None, ge=0, description="Annual revenue (must be non-negative)")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees (must be non-negative)")
    website: Optional[str] = Field(None, description="Website URL")
    description: Optional[str] = Field(None, description="Company description")

    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        return v.strip()

    @field_validator('annual_revenue')
    @classmethod
    def validate_annual_revenue(cls, v):
        if v is not None and v < 0:
            raise ValueError('Annual revenue cannot be negative')
        return v

    @field_validator('employee_count')
    @classmethod
    def validate_employee_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('Employee count cannot be negative')
        return v


class CustomerCreate(CustomerBase):
    """Customer creation model"""
    pass


class CustomerResponse(CustomerBase):
    """Customer response model"""
    customer_id: int
    created_date: datetime
    updated_date: datetime
    
    model_config = ConfigDict(from_attributes=True)


class IncomingCustomerCreate(CustomerBase):
    """Incoming customer creation model"""
    pass


class IncomingCustomerResponse(CustomerBase):
    """Incoming customer response model"""
    request_id: int
    request_date: datetime
    processing_status: str
    processed_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class MatchResult(BaseModel):
    """Match result model"""
    match_id: int
    matched_customer_id: int
    matched_company_name: str
    matched_contact_name: Optional[str]
    matched_email: Optional[str]
    similarity_score: float
    match_type: str
    confidence_level: float
    match_criteria: dict
    created_date: datetime
    reviewed: Optional[bool] = False
    reviewer_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class CustomerMatchResponse(BaseModel):
    """Customer matching response model"""
    incoming_customer: IncomingCustomerResponse
    matches: List[MatchResult]
    total_matches: int
    processing_time_ms: float


class SimilaritySearchRequest(BaseModel):
    """Similarity search request model"""
    query_text: str = Field(..., min_length=1, description="Text to search for similar customers")
    similarity_threshold: Optional[float] = Field(0.8, ge=0, le=1, description="Minimum similarity threshold (0-1)")
    max_results: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results (1-100)")


class SimilaritySearchResult(BaseModel):
    """Similarity search result model"""
    customer_id: int
    company_name: str
    contact_name: Optional[str]
    email: Optional[str]
    city: Optional[str]
    country: Optional[str]
    similarity_score: float
    
    model_config = ConfigDict(from_attributes=True)


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    database_connected: bool
    openai_connected: bool


class TestResultBase(BaseModel):
    """Base test result model"""
    test_name: str
    test_type: str
    test_configuration: Optional[dict] = None
    test_data_summary: Optional[dict] = None
    execution_metrics: Optional[dict] = None
    results_summary: Optional[dict] = None
    analysis_results: Optional[dict] = None
    recommendations: Optional[dict] = None
    status: str = "completed"
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    notes: Optional[str] = None


class TestResultCreate(TestResultBase):
    """Test result creation model"""
    pass


class TestResultResponse(TestResultBase):
    """Test result response model"""
    test_id: int
    created_date: datetime
    completed_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class TestResultList(BaseModel):
    """Test result list response model"""
    test_results: List[TestResultResponse]
    total_count: int
    page: int
    page_size: int


# ==============================================================================
# NEW MODELS FOR ENHANCED MATCHING RESULTS DISPLAY
# ==============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = Field(1, ge=1, description="Page number (starting from 1)")
    page_size: int = Field(25, ge=1, le=100, description="Number of items per page (1-100)")
    
    @field_validator('page')
    @classmethod
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page number must be greater than 0')
        return v
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Page size must be between 1 and 100')
        return v


class MatchFilters(BaseModel):
    """Filtering parameters for match queries"""
    confidence_min: Optional[float] = Field(None, ge=0, le=1, description="Minimum confidence level (0-1)")
    confidence_max: Optional[float] = Field(None, ge=0, le=1, description="Maximum confidence level (0-1)")
    match_types: Optional[List[MatchType]] = Field(None, description="Filter by match types")
    processing_status: Optional[List[ProcessingStatus]] = Field(None, description="Filter by processing status")
    date_from: Optional[datetime] = Field(None, description="Filter matches from this date")
    date_to: Optional[datetime] = Field(None, description="Filter matches to this date")
    industries: Optional[List[str]] = Field(None, description="Filter by industry")
    companies: Optional[List[str]] = Field(None, description="Filter by company names (partial match)")
    reviewed: Optional[bool] = Field(None, description="Filter by review status")
    
    @field_validator('confidence_min', 'confidence_max')
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Confidence level must be between 0 and 1')
        return v
    
    @field_validator('date_from', 'date_to')
    @classmethod
    def validate_dates(cls, v):
        if v is not None and v > datetime.now():
            raise ValueError('Date cannot be in the future')
        return v


class ProcessingMetadata(BaseModel):
    """Processing metadata for request tracking"""
    request_date: datetime
    processed_date: Optional[datetime] = None
    processing_status: ProcessingStatus
    match_strategies_used: List[str] = Field(default_factory=list, description="List of matching strategies used")
    total_processing_time_ms: Optional[float] = Field(None, ge=0, description="Total processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    retry_count: Optional[int] = Field(0, ge=0, description="Number of retry attempts")
    
    @field_validator('total_processing_time_ms')
    @classmethod
    def validate_processing_time(cls, v):
        if v is not None and v < 0:
            raise ValueError('Processing time cannot be negative')
        return v


class MatchSummary(BaseModel):
    """Aggregated match statistics"""
    total_matches: int = Field(ge=0, description="Total number of matches found")
    high_confidence_matches: int = Field(ge=0, description="Number of high confidence matches")
    medium_confidence_matches: int = Field(ge=0, description="Number of medium confidence matches")
    low_confidence_matches: int = Field(ge=0, description="Number of low confidence matches")
    exact_matches: int = Field(ge=0, description="Number of exact matches")
    potential_matches: int = Field(ge=0, description="Number of potential matches")
    average_confidence: Optional[float] = Field(None, ge=0, le=1, description="Average confidence score")
    processing_time_ms: Optional[float] = Field(None, ge=0, description="Processing time in milliseconds")
    recommendation: Optional[str] = Field(None, description="System recommendation (e.g., 'Review', 'Auto-approve')")
    
    @field_validator('high_confidence_matches', 'medium_confidence_matches', 'low_confidence_matches', 'exact_matches', 'potential_matches')
    @classmethod
    def validate_counts(cls, v):
        if v < 0:
            raise ValueError('Match counts cannot be negative')
        return v


class ComparisonHighlight(BaseModel):
    """Individual field comparison result"""
    field_name: str
    incoming_value: Optional[str] = None
    matched_value: Optional[str] = None
    match_status: str = Field(..., description="'exact', 'similar', 'different', or 'missing'")
    similarity_score: Optional[float] = Field(None, ge=0, le=1, description="Similarity score for this field")
    
    @field_validator('match_status')
    @classmethod
    def validate_match_status(cls, v):
        valid_statuses = ['exact', 'similar', 'different', 'missing']
        if v not in valid_statuses:
            raise ValueError(f'Match status must be one of: {valid_statuses}')
        return v


class ConfidenceBreakdown(BaseModel):
    """Detailed confidence factors for a match"""
    company_name_score: Optional[float] = Field(None, ge=0, le=1, description="Company name matching score")
    contact_name_score: Optional[float] = Field(None, ge=0, le=1, description="Contact name matching score")
    email_score: Optional[float] = Field(None, ge=0, le=1, description="Email matching score")
    phone_score: Optional[float] = Field(None, ge=0, le=1, description="Phone matching score")
    address_score: Optional[float] = Field(None, ge=0, le=1, description="Address matching score")
    industry_score: Optional[float] = Field(None, ge=0, le=1, description="Industry matching score")
    revenue_score: Optional[float] = Field(None, ge=0, le=1, description="Revenue similarity score")
    overall_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    
    @field_validator('company_name_score', 'contact_name_score', 'email_score', 'phone_score', 'address_score', 'industry_score', 'revenue_score', 'overall_score')
    @classmethod
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Confidence scores must be between 0 and 1')
        return v


class MatchedCustomerDetail(BaseModel):
    """Detailed information about a matched customer"""
    customer_info: CustomerResponse
    match_details: MatchResult
    comparison_highlights: List[ComparisonHighlight] = Field(default_factory=list, description="Field-by-field comparison")
    confidence_breakdown: ConfidenceBreakdown
    confidence_category: ConfidenceLevel
    
    model_config = ConfigDict(from_attributes=True)


class DetailedMatchDisplay(BaseModel):
    """Comprehensive match display for a specific incoming customer"""
    incoming_customer: IncomingCustomerResponse
    matched_customers: List[MatchedCustomerDetail] = Field(default_factory=list, description="List of matched customers with details")
    match_summary: MatchSummary
    processing_metadata: ProcessingMetadata
    
    model_config = ConfigDict(from_attributes=True)


class BulkMatchDisplay(BaseModel):
    """Bulk match display with pagination and metadata"""
    matches: List[MatchedCustomerDetail] = Field(default_factory=list, description="List of matches")
    pagination: PaginationParams
    total_count: int = Field(ge=0, description="Total number of matches available")
    filters_applied: Optional[MatchFilters] = None
    summary_stats: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class MatchSummaryDisplay(BaseModel):
    """Summary view of all matches with key metrics"""
    total_incoming_customers: int = Field(ge=0, description="Total incoming customers")
    total_matches: int = Field(ge=0, description="Total matches found")
    processed_customers: int = Field(ge=0, description="Number of processed customers")
    pending_customers: int = Field(ge=0, description="Number of pending customers")
    approved_matches: int = Field(ge=0, description="Number of approved matches")
    rejected_matches: int = Field(ge=0, description="Number of rejected matches")
    average_processing_time_ms: Optional[float] = Field(None, ge=0, description="Average processing time")
    match_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of match types")
    confidence_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of confidence levels")
    
    model_config = ConfigDict(from_attributes=True)


class ExportRequest(BaseModel):
    """Export request parameters"""
    format: str = Field(..., description="Export format (csv, json, excel)")
    filters: Optional[MatchFilters] = None
    include_fields: Optional[List[str]] = Field(None, description="Specific fields to include in export")
    filename: Optional[str] = Field(None, description="Custom filename for export")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        valid_formats = ['csv', 'json', 'excel', 'pdf']
        if v.lower() not in valid_formats:
            raise ValueError(f'Export format must be one of: {valid_formats}')
        return v.lower()


class ExportResult(BaseModel):
    """Export operation result"""
    success: bool
    filename: str
    file_size: Optional[int] = Field(None, description="File size in bytes")
    record_count: int = Field(ge=0, description="Number of records exported")
    export_time_ms: Optional[float] = Field(None, ge=0, description="Export processing time")
    download_url: Optional[str] = Field(None, description="URL for downloading the exported file")
    error_message: Optional[str] = Field(None, description="Error message if export failed")
    
    model_config = ConfigDict(from_attributes=True) 