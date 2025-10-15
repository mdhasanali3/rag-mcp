"""
Configuration Settings Module

This module manages all configuration settings for the RAG Anything MCP Server.
Uses environment variables with sensible defaults following the 12-factor app methodology.

Standard Practices Used:
- Environment-based configuration
- Type validation with Pydantic
- Singleton pattern for settings
- Secrets management best practices
- Configuration inheritance for different environments
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    This class uses Pydantic's BaseSettings to automatically load
    configuration from environment variables with type validation.
    """

    # Application Settings
    APP_NAME: str = Field(default="rag-anything-mcp", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="production", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json, text"
    )
    LOG_FILE_PATH: Optional[Path] = Field(
        default=None,
        description="Path to log file (None for stdout only)"
    )

    # OpenAI API Settings
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    OPENAI_LLM_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Default LLM model"
    )
    OPENAI_VISION_MODEL: str = Field(
        default="gpt-4o",
        description="Vision model for image processing"
    )
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-large",
        description="Embedding model"
    )
    OPENAI_EMBEDDING_DIM: int = Field(
        default=3072,
        description="Embedding dimension"
    )

    # RAG Processing Settings
    RAG_WORKING_DIR: Path = Field(
        default=Path("./rag_storage"),
        description="Working directory for RAG storage"
    )
    RAG_DEFAULT_CHUNK_SIZE: int = Field(
        default=512,
        description="Default chunk size for text splitting"
    )
    RAG_CHUNK_OVERLAP: int = Field(
        default=50,
        description="Overlap between chunks"
    )
    RAG_MAX_WORKERS: int = Field(
        default=4,
        description="Maximum concurrent workers for processing"
    )

    # File Processing Settings
    SUPPORTED_FILE_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".docx", ".pptx", ".txt", ".md"],
        description="Supported file extensions"
    )
    MAX_FILE_SIZE_MB: int = Field(
        default=100,
        description="Maximum file size in MB"
    )
    ENABLE_RECURSIVE_PROCESSING: bool = Field(
        default=True,
        description="Enable recursive directory processing"
    )

    # Multimodal Processing Settings
    ENABLE_IMAGE_PROCESSING: bool = Field(
        default=True,
        description="Enable image analysis"
    )
    ENABLE_TABLE_PROCESSING: bool = Field(
        default=True,
        description="Enable table extraction"
    )
    ENABLE_EQUATION_PROCESSING: bool = Field(
        default=True,
        description="Enable equation processing"
    )
    IMAGE_MAX_DIMENSION: int = Field(
        default=2048,
        description="Maximum image dimension"
    )

    # Performance Settings
    REQUEST_TIMEOUT: int = Field(
        default=300,
        description="Request timeout in seconds"
    )
    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    RETRY_BACKOFF_FACTOR: float = Field(
        default=2.0,
        description="Backoff factor for retries"
    )

    # Cache Settings
    ENABLE_CACHE: bool = Field(
        default=True,
        description="Enable caching"
    )
    CACHE_TTL: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    CACHE_MAX_SIZE: int = Field(
        default=1000,
        description="Maximum cache size"
    )

    # Monitoring Settings
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    METRICS_PORT: int = Field(
        default=9090,
        description="Metrics server port"
    )
    ENABLE_TRACING: bool = Field(
        default=False,
        description="Enable distributed tracing"
    )

    # Security Settings
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        description="Allowed hosts for CORS"
    )
    API_RATE_LIMIT: int = Field(
        default=100,
        description="API rate limit per minute"
    )
    ENABLE_API_KEY_AUTH: bool = Field(
        default=False,
        description="Enable API key authentication"
    )

    @validator("RAG_WORKING_DIR", pre=True)
    def create_working_dir(cls, v):
        """Ensure working directory exists."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v.lower()

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Allow environment variables to override defaults
        env_prefix = ""

    def get_openai_config(self) -> dict:
        """Get OpenAI configuration as a dictionary."""
        return {
            "api_key": self.OPENAI_API_KEY,
            "base_url": self.OPENAI_BASE_URL,
            "llm_model": self.OPENAI_LLM_MODEL,
            "vision_model": self.OPENAI_VISION_MODEL,
            "embedding_model": self.OPENAI_EMBEDDING_MODEL,
            "embedding_dim": self.OPENAI_EMBEDDING_DIM,
        }

    def get_rag_config(self) -> dict:
        """Get RAG configuration as a dictionary."""
        return {
            "working_dir": str(self.RAG_WORKING_DIR),
            "chunk_size": self.RAG_DEFAULT_CHUNK_SIZE,
            "chunk_overlap": self.RAG_CHUNK_OVERLAP,
            "max_workers": self.RAG_MAX_WORKERS,
            "enable_image": self.ENABLE_IMAGE_PROCESSING,
            "enable_table": self.ENABLE_TABLE_PROCESSING,
            "enable_equation": self.ENABLE_EQUATION_PROCESSING,
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
