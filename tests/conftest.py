"""
Pytest Configuration and Fixtures

This module contains shared fixtures and configuration for all tests.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.config.settings import Settings
from src.services.rag_manager import RAGManager
from src.monitoring.metrics import MetricsCollector


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        OPENAI_API_KEY="test-api-key",
        RAG_WORKING_DIR=Path(tempfile.mkdtemp()),
        ENABLE_CACHE=False,
        ENABLE_METRICS=False,
    )


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_file(temp_directory):
    """Create a sample text file for testing."""
    file_path = temp_directory / "sample.txt"
    file_path.write_text("This is a sample document for testing.")
    return file_path


@pytest.fixture
def sample_documents_directory(temp_directory):
    """Create a directory with sample documents."""
    docs_dir = temp_directory / "documents"
    docs_dir.mkdir()

    # Create sample files
    (docs_dir / "doc1.txt").write_text("Sample document 1 content")
    (docs_dir / "doc2.txt").write_text("Sample document 2 content")
    (docs_dir / "doc3.md").write_text("# Sample Markdown\n\nContent here")

    return docs_dir


@pytest.fixture
def rag_manager(test_settings):
    """Provide a RAG manager instance."""
    return RAGManager(test_settings)


@pytest.fixture
def mock_openai_client():
    """Provide a mocked OpenAI client."""
    mock_client = Mock()
    mock_client.embeddings.create = AsyncMock(return_value={
        "data": [{"embedding": [0.1] * 3072}]
    })
    mock_client.chat.completions.create = AsyncMock(return_value={
        "choices": [{"message": {"content": "Test response"}}]
    })
    return mock_client


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    metrics = MetricsCollector()
    metrics.reset()
    yield
    metrics.reset()


@pytest.fixture
def mock_rag_instance():
    """Provide a mocked RAG instance."""
    mock_instance = Mock()
    mock_instance.is_processing = False
    mock_instance.is_initialized = True
    mock_instance.directory_path = Path("/test/path")
    mock_instance.working_dir = Path("/test/working")
    return mock_instance
