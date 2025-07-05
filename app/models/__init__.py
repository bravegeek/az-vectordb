"""Models package for Customer Matching POC"""

from .database import (
    Base, Customer, IncomingCustomer, MatchingResult, TestResult
)

from .schemas import (
    CustomerBase, CustomerCreate, CustomerResponse,
    IncomingCustomerCreate, IncomingCustomerResponse,
    MatchResult, CustomerMatchResponse,
    SimilaritySearchRequest, SimilaritySearchResult,
    HealthCheck, TestResultBase, TestResultCreate, TestResultResponse, TestResultList
)

__all__ = [
    # Database models
    "Base", "Customer", "IncomingCustomer", "MatchingResult", "TestResult",
    # Pydantic schemas
    "CustomerBase", "CustomerCreate", "CustomerResponse",
    "IncomingCustomerCreate", "IncomingCustomerResponse", 
    "MatchResult", "CustomerMatchResponse",
    "SimilaritySearchRequest", "SimilaritySearchResult", "HealthCheck",
    "TestResultBase", "TestResultCreate", "TestResultResponse", "TestResultList"
] 