"""
File Utilities

Helper functions for file operations.

Standard Practices:
- Path validation and normalization
- Safe file operations
- Cross-platform compatibility
- Error handling
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional


class FileUtils:
    """Utility class for file operations."""

    @staticmethod
    def validate_path(path: str) -> Path:
        """
        Validate and normalize a file path.

        Args:
            path: Path string

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is invalid
        """
        try:
            p = Path(path).resolve()
            return p
        except Exception as e:
            raise ValueError(f"Invalid path: {path}") from e

    @staticmethod
    def ensure_directory(directory: Path) -> None:
        """
        Ensure a directory exists, create if it doesn't.

        Args:
            directory: Directory path
        """
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """
        Calculate file hash.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm

        Returns:
            Hex digest of file hash
        """
        hasher = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """
        Get file size in megabytes.

        Args:
            file_path: Path to file

        Returns:
            File size in MB
        """
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)

    @staticmethod
    def is_supported_file(
        file_path: Path,
        extensions: List[str]
    ) -> bool:
        """
        Check if file extension is supported.

        Args:
            file_path: Path to file
            extensions: List of supported extensions

        Returns:
            True if supported, False otherwise
        """
        return file_path.suffix.lower() in [ext.lower() for ext in extensions]

    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        Create a safe filename by removing/replacing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = "".join(c if c not in invalid_chars else "_" for c in filename)

        # Remove leading/trailing spaces and dots
        safe_name = safe_name.strip(". ")

        return safe_name if safe_name else "unnamed"
