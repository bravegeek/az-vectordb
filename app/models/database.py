"""SQLAlchemy models for Customer Matching POC"""
from datetime import datetime
from typing import Optional, List, Any
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Customer(Base):
    """Customer table model"""
    __tablename__ = "customers"
    __table_args__ = {"schema": "customer_data"}
    
    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state_province: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_date: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Vector embeddings
    company_name_embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536))
    full_profile_embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536))
    
    # Relationships
    matches: Mapped[List["MatchingResult"]] = relationship(
        "MatchingResult", 
        foreign_keys="MatchingResult.matched_customer_id", 
        back_populates="matched_customer"
    )


class IncomingCustomer(Base):
    """Incoming customer requests table model"""
    __tablename__ = "incoming_customers"
    __table_args__ = {"schema": "customer_data"}
    
    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
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
    request_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Vector embeddings
    company_name_embedding = Column(Vector(1536))
    full_profile_embedding = Column(Vector(1536))
    
    # Processing status
    processing_status: Mapped[str] = mapped_column(String(20), default="pending")
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    matches = relationship("MatchingResult", foreign_keys="MatchingResult.incoming_customer_id", back_populates="incoming_customer")


class MatchingResult(Base):
    """Customer matching results table model"""
    __tablename__ = "matching_results"
    __table_args__ = {"schema": "customer_data"}
    
    match_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incoming_customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer_data.incoming_customers.request_id"))
    matched_customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer_data.customers.customer_id"))
    similarity_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 4))
    match_type: Mapped[str] = mapped_column(String(50))  # 'exact', 'high_confidence', 'potential', 'low_confidence'
    match_criteria: Mapped[Optional[dict]] = mapped_column(JSON)
    confidence_level: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 4))
    created_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    incoming_customer = relationship("IncomingCustomer", foreign_keys=[incoming_customer_id], back_populates="matches")
    matched_customer = relationship("Customer", foreign_keys=[matched_customer_id], back_populates="matches")


class TestResult(Base):
    """Test execution results table model"""
    __tablename__ = "test_results"
    __table_args__ = {"schema": "customer_data"}
    
    test_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    test_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 'semantic_similarity', 'performance', 'integration', etc.
    test_configuration: Mapped[Optional[dict]] = mapped_column(JSON)  # Store test parameters and settings
    test_data_summary: Mapped[Optional[dict]] = mapped_column(JSON)  # Summary of test data used
    execution_metrics: Mapped[Optional[dict]] = mapped_column(JSON)  # Performance metrics, timing, etc.
    results_summary: Mapped[Optional[dict]] = mapped_column(JSON)  # Aggregate test results
    analysis_results: Mapped[Optional[dict]] = mapped_column(JSON)  # Detailed analysis and insights
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON)  # Recommendations from analysis
    status: Mapped[str] = mapped_column(String(50), default="completed")  # 'running', 'completed', 'failed'
    error_message: Mapped[Optional[str]] = mapped_column(Text)  # Error details if test failed
    created_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))  # User or system that ran the test
    notes: Mapped[Optional[str]] = mapped_column(Text)  # Additional notes about the test run
