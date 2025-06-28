"""Health check endpoints for Customer Matching POC"""

from datetime import datetime
from fastapi import APIRouter

from app.core.config import settings
from app.core.database import check_database_connection
from app.services.embedding_service import embedding_service
from app.models.schemas import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    db_connected = check_database_connection()
    openai_connected = embedding_service.test_connection()
    
    return HealthCheck(
        status="healthy" if db_connected and openai_connected else "unhealthy",
        timestamp=datetime.now(),
        version=settings.app_version,
        database_connected=db_connected,
        openai_connected=openai_connected
    ) 