"""Configuration settings for Customer Matching POC"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    app_name: str = "Customer Matching POC"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # PostgreSQL Configuration
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_db: str = "customer_matching"
    postgres_user: str = "pgadmin"
    postgres_password: Optional[str] = None
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "text-embedding-ada-002"
    azure_openai_api_version: str = "2023-12-01-preview"
    
    # Azure Key Vault (Optional - for production)
    azure_key_vault_url: Optional[str] = None
    use_key_vault: bool = False
    
    # Similarity Thresholds
    default_similarity_threshold: float = 0.08  # Lowered from 0.8 to match vector similarity scores
    high_confidence_threshold: float = 0.12    # Lowered from 0.9 to match vector similarity scores
    potential_match_threshold: float = 0.06    # Lowered from 0.75 to match vector similarity scores
    
    # Exact matching weights
    exact_company_name_weight: float = 0.4
    exact_email_weight: float = 0.4
    exact_phone_weight: float = 0.2
    exact_match_min_score: float = 0.4
    
    # Fuzzy matching settings
    fuzzy_similarity_threshold: float = 0.8
    fuzzy_max_results: int = 10
    
    # Vector matching settings
    vector_similarity_threshold: float = 0.05  # Lowered from 0.7 to match actual embedding similarity scores
    vector_max_results: int = 5
    
    # Hybrid matching settings
    enable_exact_matching: bool = True
    enable_vector_matching: bool = True
    enable_fuzzy_matching: bool = True
    exact_matching_priority: int = 1
    vector_matching_priority: int = 2
    fuzzy_matching_priority: int = 3
    
    # Business rules
    enable_business_rules: bool = True
    industry_match_boost: float = 1.2
    location_match_boost: float = 1.1
    country_mismatch_penalty: float = 0.8
    revenue_size_boost: bool = True
    
    # Performance settings
    batch_size: int = 16
    max_concurrent_requests: int = 10
    cache_embeddings: bool = True
    
    model_config = SettingsConfigDict(
        env_file="app/.env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from environment
    )
    
    def _build_db_url(self, async_mode: bool = False) -> str:
        host = self.postgres_host
        port = self.postgres_port
        user = self.postgres_user
        password = self.postgres_password
        db_name = self.postgres_db
            
        if not host or not password:
            raise ValueError("Database host and password are required")
        driver = "postgresql+asyncpg" if async_mode else "postgresql"
        return f"{driver}://{user}:{password}@{host}:{port}/{db_name}"

    @property
    def database_url(self) -> str:
        return self._build_db_url(async_mode=False)

    @property
    def async_database_url(self) -> str:
        return self._build_db_url(async_mode=True)


# Global settings instance
settings = Settings()
