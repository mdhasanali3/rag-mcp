"""
Unit tests for utility modules.
"""

import pytest
from pathlib import Path

from src.utils.file_utils import FileUtils
from src.utils.validation import Validator


class TestFileUtils:
    """Test suite for FileUtils class."""

    def test_validate_path(self, temp_directory):
        """Test path validation."""
        # Valid path
        validated = FileUtils.validate_path(str(temp_directory))
        assert isinstance(validated, Path)
        assert validated.exists()

    def test_validate_path_invalid(self):
        """Test invalid path handling."""
        # This should not raise an error, just return a Path object
        result = FileUtils.validate_path("/nonexistent/path")
        assert isinstance(result, Path)

    def test_ensure_directory(self, temp_directory):
        """Test directory creation."""
        new_dir = temp_directory / "new" / "nested" / "dir"
        FileUtils.ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_get_file_hash(self, sample_text_file):
        """Test file hash calculation."""
        hash1 = FileUtils.get_file_hash(sample_text_file)
        hash2 = FileUtils.get_file_hash(sample_text_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length

    def test_get_file_size_mb(self, sample_text_file):
        """Test file size calculation."""
        size_mb = FileUtils.get_file_size_mb(sample_text_file)

        assert isinstance(size_mb, float)
        assert size_mb > 0

    def test_is_supported_file(self, sample_text_file):
        """Test file extension checking."""
        extensions = [".txt", ".pdf", ".docx"]

        assert FileUtils.is_supported_file(sample_text_file, extensions) is True
        assert FileUtils.is_supported_file(
            Path("test.exe"),
            extensions
        ) is False

    def test_safe_filename(self):
        """Test safe filename generation."""
        # Invalid characters
        unsafe = 'file<name>with:invalid"chars|?.txt'
        safe = FileUtils.safe_filename(unsafe)

        assert "<" not in safe
        assert ">" not in safe
        assert ":" not in safe
        assert "|" not in safe
        assert "?" not in safe

        # Empty or whitespace
        assert FileUtils.safe_filename("") == "unnamed"
        assert FileUtils.safe_filename("   ") == "unnamed"


class TestValidator:
    """Test suite for Validator class."""

    def test_validate_api_key_valid(self):
        """Test valid API key."""
        # Should not raise
        Validator.validate_api_key("sk-1234567890abcdefghij")

    def test_validate_api_key_invalid(self):
        """Test invalid API key."""
        with pytest.raises(ValueError, match="API key must be"):
            Validator.validate_api_key("")

        with pytest.raises(ValueError, match="too short"):
            Validator.validate_api_key("short")

        with pytest.raises(ValueError, match="API key must be"):
            Validator.validate_api_key(None)

    def test_validate_directory_path_valid(self, temp_directory):
        """Test valid directory path."""
        # Should not raise
        Validator.validate_directory_path(str(temp_directory))

    def test_validate_directory_path_not_exists(self):
        """Test non-existent directory."""
        with pytest.raises(FileNotFoundError):
            Validator.validate_directory_path("/nonexistent/directory")

    def test_validate_directory_path_is_file(self, sample_text_file):
        """Test that file path is rejected."""
        with pytest.raises(ValueError, match="not a directory"):
            Validator.validate_directory_path(str(sample_text_file))

    def test_validate_file_path_valid(self, sample_text_file):
        """Test valid file path."""
        # Should not raise
        Validator.validate_file_path(str(sample_text_file))

    def test_validate_file_path_not_exists(self):
        """Test non-existent file."""
        with pytest.raises(FileNotFoundError):
            Validator.validate_file_path("/nonexistent/file.txt")

    def test_validate_file_path_is_directory(self, temp_directory):
        """Test that directory path is rejected."""
        with pytest.raises(ValueError, match="not a file"):
            Validator.validate_file_path(str(temp_directory))

    def test_validate_query_mode_valid(self):
        """Test valid query modes."""
        valid_modes = ["hybrid", "local", "global", "naive", "mix", "bypass"]

        for mode in valid_modes:
            # Should not raise
            Validator.validate_query_mode(mode)

    def test_validate_query_mode_invalid(self):
        """Test invalid query mode."""
        with pytest.raises(ValueError, match="Invalid query mode"):
            Validator.validate_query_mode("invalid_mode")

    def test_validate_positive_int(self):
        """Test positive integer validation."""
        # Valid
        Validator.validate_positive_int(5, "test_param")

        # Invalid - not positive
        with pytest.raises(ValueError, match="must be positive"):
            Validator.validate_positive_int(0, "test_param")

        with pytest.raises(ValueError, match="must be positive"):
            Validator.validate_positive_int(-5, "test_param")

        # Invalid - not integer
        with pytest.raises(ValueError, match="must be an integer"):
            Validator.validate_positive_int(5.5, "test_param")

    def test_validate_range(self):
        """Test range validation."""
        # Valid - within range
        Validator.validate_range(5, "test", min_val=0, max_val=10)

        # Invalid - below minimum
        with pytest.raises(ValueError, match="at least"):
            Validator.validate_range(-1, "test", min_val=0)

        # Invalid - above maximum
        with pytest.raises(ValueError, match="at most"):
            Validator.validate_range(11, "test", max_val=10)

        # Valid - no limits
        Validator.validate_range(100, "test")
