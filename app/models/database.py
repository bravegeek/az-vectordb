"""SQLAlchemy models for Customer Matching POC"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

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


class TestResult(Base):
    """Test execution results table model"""
    __tablename__ = "test_results"
    __table_args__ = {"schema": "customer_data"}
    
    test_id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String(255), nullable=False, index=True)
    test_type = Column(String(100), nullable=False)  # 'semantic_similarity', 'performance', 'integration', etc.
    test_configuration = Column(JSON)  # Store test parameters and settings
    test_data_summary = Column(JSON)  # Summary of test data used
    execution_metrics = Column(JSON)  # Performance metrics, timing, etc.
    results_summary = Column(JSON)  # Aggregate test results
    analysis_results = Column(JSON)  # Detailed analysis and insights
    recommendations = Column(JSON)  # Recommendations from analysis
    status = Column(String(50), default="completed")  # 'running', 'completed', 'failed'
    error_message = Column(Text)  # Error details if test failed
    created_date = Column(DateTime, default=func.now())
    completed_date = Column(DateTime)
    created_by = Column(String(100))  # User or system that ran the test
    notes = Column(Text)  # Additional notes about the test run
