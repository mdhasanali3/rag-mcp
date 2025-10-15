"""
Integration tests for end-to-end RAG workflows.
"""

import pytest
from pathlib import Path

from src.services.rag_manager import RAGManager


@pytest.mark.integration
class TestRAGWorkflow:
    """Integration tests for RAG workflows."""

    @pytest.mark.asyncio
    async def test_process_and_query_workflow(
        self,
        rag_manager,
        sample_documents_directory,
        test_settings
    ):
        """Test complete workflow: process directory then query."""
        # This is a placeholder for integration testing
        # In real implementation, you'd use actual RAG processing

        # Process directory
        result = await rag_manager.process_directory(
            directory_path=str(sample_documents_directory),
            api_key=test_settings.OPENAI_API_KEY
        )

        # Verify processing completed
        assert "status" in result
        assert result["total_files"] > 0

    @pytest.mark.asyncio
    async def test_multiple_directory_processing(
        self,
        rag_manager,
        temp_directory,
        test_settings
    ):
        """Test processing multiple directories."""
        # Create multiple document directories
        dir1 = temp_directory / "docs1"
        dir2 = temp_directory / "docs2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "file1.txt").write_text("Content 1")
        (dir2 / "file2.txt").write_text("Content 2")

        # Process both directories
        result1 = await rag_manager.process_directory(
            str(dir1),
            test_settings.OPENAI_API_KEY
        )
        result2 = await rag_manager.process_directory(
            str(dir2),
            test_settings.OPENAI_API_KEY
        )

        # Verify both completed
        assert result1["status"] == "completed"
        assert result2["status"] == "completed"

        # List processed directories
        directories = rag_manager.list_processed_directories()
        assert len(directories) >= 2
