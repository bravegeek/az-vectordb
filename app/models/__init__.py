"""Models package for Customer Matching POC"""

from .database import (
    Base, Customer, IncomingCustomer, MatchingResult
)

from .schemas import (
    CustomerBase, CustomerCreate, CustomerResponse,
    IncomingCustomerCreate, IncomingCustomerResponse,
    MatchResult, CustomerMatchResponse,
    SimilaritySearchRequest, SimilaritySearchResult,
    HealthCheck
)

__all__ = [
    # Database models
    "Base", "Customer", "IncomingCustomer", "MatchingResult",
    # Pydantic schemas
    "CustomerBase", "CustomerCreate", "CustomerResponse",
    "IncomingCustomerCreate", "IncomingCustomerResponse", 
    "MatchResult", "CustomerMatchResponse",
    "SimilaritySearchRequest", "SimilaritySearchResult", "HealthCheck"
] 