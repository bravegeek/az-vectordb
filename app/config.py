"""Configuration management for Customer Matching POC"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


class Settings(BaseSettings):
    """Application settings with Azure Key Vault integration"""
    
    # Application
    app_name: str = Field(default="Customer Matching POC", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # PostgreSQL
    postgres_host: str = Field(env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="customer_matching", env="POSTGRES_DB")
    postgres_user: str = Field(env="POSTGRES_USER")
    postgres_password: str = Field(env="POSTGRES_PASSWORD")
    
    # Azure OpenAI
    azure_openai_endpoint: str = Field(env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(env="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str = Field(default="text-embedding-ada-002", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION")
    
    # Azure Key Vault (Optional)
    azure_key_vault_url: Optional[str] = Field(default=None, env="AZURE_KEY_VAULT_URL")
    use_key_vault: bool = Field(default=False, env="USE_KEY_VAULT")
    
    # Similarity Thresholds
    default_similarity_threshold: float = Field(default=0.8, env="DEFAULT_SIMILARITY_THRESHOLD")
    high_confidence_threshold: float = Field(default=0.9, env="HIGH_CONFIDENCE_THRESHOLD")
    potential_match_threshold: float = Field(default=0.75, env="POTENTIAL_MATCH_THRESHOLD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.use_key_vault and self.azure_key_vault_url:
            self._load_from_key_vault()
    
    def _load_from_key_vault(self):
        """Load secrets from Azure Key Vault"""
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.azure_key_vault_url, credential=credential)
            
            # Override with Key Vault values if available
            secrets_mapping = {
                "postgresql-connection-string": "postgres_password",
                "openai-api-key": "azure_openai_api_key",
                "openai-endpoint": "azure_openai_endpoint"
            }
            
            for secret_name, attr_name in secrets_mapping.items():
                try:
                    secret = client.get_secret(secret_name)
                    if secret_name == "postgresql-connection-string":
                        # Parse connection string for password
                        conn_parts = secret.value.split(';')
                        for part in conn_parts:
                            if part.startswith('Password='):
                                setattr(self, attr_name, part.split('=', 1)[1])
                    else:
                        setattr(self, attr_name, secret.value)
                except Exception as e:
                    print(f"Warning: Could not retrieve secret {secret_name}: {e}")
                    
        except Exception as e:
            print(f"Warning: Could not connect to Key Vault: {e}")
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}?sslmode=require"
    
    @property
    def async_database_url(self) -> str:
        """Get async PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}?ssl=require"


# Global settings instance
settings = Settings()
