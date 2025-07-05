"""Pydantic schemas for Customer Matching POC API"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator


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