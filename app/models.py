"""SQLAlchemy models for Customer Matching POC"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field

Base = declarative_base()


class Customer(Base):
    """Customer table model"""
    __tablename__ = "customers"
    __table_args__ = {"schema": "customer_data"}
    
    customer_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(255))
    email = Column(String(255), index=True)
    phone = Column(String(50), index=True)
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    industry = Column(String(100))
    annual_revenue = Column(DECIMAL(15, 2))
    employee_count = Column(Integer)
    website = Column(String(255))
    description = Column(Text)
    created_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Vector embeddings
    company_name_embedding = Column(Vector(1536))
    full_profile_embedding = Column(Vector(1536))
    
    # Relationships
    matches = relationship("MatchingResult", foreign_keys="MatchingResult.matched_customer_id", back_populates="matched_customer")


class IncomingCustomer(Base):
    """Incoming customer requests table model"""
    __tablename__ = "incoming_customers"
    __table_args__ = {"schema": "customer_data"}
    
    request_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    industry = Column(String(100))
    annual_revenue = Column(DECIMAL(15, 2))
    employee_count = Column(Integer)
    website = Column(String(255))
    description = Column(Text)
    request_date = Column(DateTime, default=func.now())
    
    # Vector embeddings
    company_name_embedding = Column(Vector(1536))
    full_profile_embedding = Column(Vector(1536))
    
    # Processing status
    processing_status = Column(String(20), default="pending")
    processed_date = Column(DateTime)
    
    # Relationships
    matches = relationship("MatchingResult", foreign_keys="MatchingResult.incoming_customer_id", back_populates="incoming_customer")


class MatchingResult(Base):
    """Customer matching results table model"""
    __tablename__ = "matching_results"
    __table_args__ = {"schema": "customer_data"}
    
    match_id = Column(Integer, primary_key=True, index=True)
    incoming_customer_id = Column(Integer, ForeignKey("customer_data.incoming_customers.request_id"))
    matched_customer_id = Column(Integer, ForeignKey("customer_data.customers.customer_id"))
    similarity_score = Column(DECIMAL(5, 4))
    match_type = Column(String(50))  # 'exact', 'high_confidence', 'potential', 'low_confidence'
    match_criteria = Column(JSON)
    confidence_level = Column(DECIMAL(5, 4))
    created_date = Column(DateTime, default=func.now())
    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text)
    
    # Relationships
    incoming_customer = relationship("IncomingCustomer", foreign_keys=[incoming_customer_id], back_populates="matches")
    matched_customer = relationship("Customer", foreign_keys=[matched_customer_id], back_populates="matches")


# Pydantic models for API
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
