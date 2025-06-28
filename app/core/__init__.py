"""Core package for Customer Matching POC"""

from .config import settings
from .database import get_db, get_async_db, initialize_database, check_database_connection

__all__ = [
    "settings",
    "get_db", 
    "get_async_db", 
    "initialize_database", 
    "check_database_connection"
] 