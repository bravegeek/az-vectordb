"""Main API router for Customer Matching POC v1"""

from fastapi import APIRouter

from .endpoints import customers, health, matching, test_results, display

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(test_results.router, prefix="/test-results", tags=["test-results"])
api_router.include_router(display.router, prefix="/display", tags=["display"]) 