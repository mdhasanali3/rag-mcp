"""
Unit tests for configuration module.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError

from src.config.settings import Settings


class TestSettings:
    """Test suite for Settings class."""

    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings(OPENAI_API_KEY="test-key")

        assert settings.APP_NAME == "rag-anything-mcp"
        assert settings.VERSION == "1.0.0"
        assert settings.ENVIRONMENT == "production"
        assert settings.LOG_LEVEL == "INFO"
        assert settings.OPENAI_API_KEY == "test-key"

    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environments
        for env in ["development", "staging", "production"]:
            settings = Settings(ENVIRONMENT=env, OPENAI_API_KEY="test")
            assert settings.ENVIRONMENT == env

        # Invalid environment
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="invalid", OPENAI_API_KEY="test")

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(LOG_LEVEL=level, OPENAI_API_KEY="test")
            assert settings.LOG_LEVEL == level

        # Invalid log level
        with pytest.raises(ValidationError):
            Settings(LOG_LEVEL="INVALID", OPENAI_API_KEY="test")

    def test_working_directory_creation(self):
        """Test that working directory is created."""
        import tempfile
        temp_dir = Path(tempfile.mkdtemp()) / "test_rag"

        settings = Settings(
            RAG_WORKING_DIR=temp_dir,
            OPENAI_API_KEY="test"
        )

        assert settings.RAG_WORKING_DIR.exists()
        assert settings.RAG_WORKING_DIR.is_dir()

    def test_get_openai_config(self):
        """Test OpenAI configuration retrieval."""
        settings = Settings(OPENAI_API_KEY="test-key")
        config = settings.get_openai_config()

        assert config["api_key"] == "test-key"
        assert config["base_url"] == "https://api.openai.com/v1"
        assert config["llm_model"] == "gpt-4o-mini"
        assert config["vision_model"] == "gpt-4o"

    def test_get_rag_config(self):
        """Test RAG configuration retrieval."""
        settings = Settings(OPENAI_API_KEY="test")
        config = settings.get_rag_config()

        assert "working_dir" in config
        assert config["chunk_size"] == 512
        assert config["chunk_overlap"] == 50
        assert config["max_workers"] == 4

    def test_is_production(self):
        """Test production environment detection."""
        prod_settings = Settings(ENVIRONMENT="production", OPENAI_API_KEY="test")
        dev_settings = Settings(ENVIRONMENT="development", OPENAI_API_KEY="test")

        assert prod_settings.is_production() is True
        assert dev_settings.is_production() is False

    def test_is_development(self):
        """Test development environment detection."""
        prod_settings = Settings(ENVIRONMENT="production", OPENAI_API_KEY="test")
        dev_settings = Settings(ENVIRONMENT="development", OPENAI_API_KEY="test")

        assert prod_settings.is_development() is False
        assert dev_settings.is_development() is True

    def test_positive_integer_validation(self):
        """Test positive integer field validation."""
        # Valid values
        settings = Settings(
            RAG_MAX_WORKERS=4,
            OPENAI_API_KEY="test"
        )
        assert settings.RAG_MAX_WORKERS == 4

        # Zero or negative should use default
        settings = Settings(OPENAI_API_KEY="test")
        assert settings.RAG_MAX_WORKERS > 0

    def test_file_extension_list(self):
        """Test file extension list handling."""
        extensions = [".pdf", ".docx", ".txt"]
        settings = Settings(
            SUPPORTED_FILE_EXTENSIONS=extensions,
            OPENAI_API_KEY="test"
        )

        assert settings.SUPPORTED_FILE_EXTENSIONS == extensions

    def test_custom_base_url(self):
        """Test custom OpenAI base URL."""
        custom_url = "https://custom-api.example.com/v1"
        settings = Settings(
            OPENAI_BASE_URL=custom_url,
            OPENAI_API_KEY="test"
        )

        assert settings.OPENAI_BASE_URL == custom_url
