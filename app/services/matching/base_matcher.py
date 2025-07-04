"""Base matcher interface for customer matching strategies"""
from abc import ABC, abstractmethod
from typing import List
from sqlalchemy.orm import Session

from app.models.database import IncomingCustomer
from app.models.schemas import MatchResult as MatchResultSchema


class BaseMatcher(ABC):
    """Abstract base class for all matching strategies"""
    
    @abstractmethod
    def find_matches(self, incoming_customer: IncomingCustomer, db: Session) -> List[MatchResultSchema]:
        """Find matches using this strategy"""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if this matcher is enabled"""
        pass 