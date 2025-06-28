"""Pydantic schemas for Customer Matching POC API"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """Base customer model for API"""
    company_name: str = Field(..., description="Company name")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address_line1: Optional[str] = Field(None, description="Address line 1")
    address_line2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state_province: Optional[str] = Field(None, description="State or province")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(None, description="Country")
    industry: Optional[str] = Field(None, description="Industry")
    annual_revenue: Optional[float] = Field(None, description="Annual revenue")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    website: Optional[str] = Field(None, description="Website URL")
    description: Optional[str] = Field(None, description="Company description")


class CustomerCreate(CustomerBase):
    """Customer creation model"""
    pass


class CustomerResponse(CustomerBase):
    """Customer response model"""
    customer_id: int
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class IncomingCustomerCreate(CustomerBase):
    """Incoming customer creation model"""
    pass


class IncomingCustomerResponse(CustomerBase):
    """Incoming customer response model"""
    request_id: int
    request_date: datetime
    processing_status: str
    processed_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


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
    
    class Config:
        from_attributes = True


class CustomerMatchResponse(BaseModel):
    """Customer matching response model"""
    incoming_customer: IncomingCustomerResponse
    matches: List[MatchResult]
    total_matches: int
    processing_time_ms: float


class SimilaritySearchRequest(BaseModel):
    """Similarity search request model"""
    query_text: str = Field(..., description="Text to search for similar customers")
    similarity_threshold: Optional[float] = Field(0.8, description="Minimum similarity threshold")
    max_results: Optional[int] = Field(10, description="Maximum number of results")


class SimilaritySearchResult(BaseModel):
    """Similarity search result model"""
    customer_id: int
    company_name: str
    contact_name: Optional[str]
    email: Optional[str]
    city: Optional[str]
    country: Optional[str]
    similarity_score: float
    
    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    database_connected: bool
    openai_connected: bool 