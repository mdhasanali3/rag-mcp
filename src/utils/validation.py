"""
Validation Utilities

Input validation and sanitization functions.

Standard Practices:
- Comprehensive input validation
- Type checking
- Range validation
- Format validation
"""

from typing import Any, List, Dict, Optional
from pathlib import Path


class Validator:
    """Utility class for input validation."""

    @staticmethod
    def validate_api_key(api_key: str) -> None:
        """
        Validate OpenAI API key format.

        Args:
            api_key: API key string

        Raises:
            ValueError: If API key is invalid
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        if len(api_key) < 20:
            raise ValueError("API key appears to be too short")

    @staticmethod
    def validate_directory_path(path: str) -> None:
        """
        Validate directory path.

        Args:
            path: Directory path string

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If directory doesn't exist
        """
        if not path:
            raise ValueError("Directory path cannot be empty")

        dir_path = Path(path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

    @staticmethod
    def validate_file_path(path: str) -> None:
        """
        Validate file path.

        Args:
            path: File path string

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If file doesn't exist
        """
        if not path:
            raise ValueError("File path cannot be empty")

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

    @staticmethod
    def validate_query_mode(mode: str) -> None:
        """
        Validate query mode.

        Args:
            mode: Query mode string

        Raises:
            ValueError: If mode is invalid
        """
        valid_modes = ["hybrid", "local", "global", "naive", "mix", "bypass"]

        if mode not in valid_modes:
            raise ValueError(
                f"Invalid query mode: {mode}. Valid modes: {', '.join(valid_modes)}"
            )

    @staticmethod
    def validate_positive_int(value: int, name: str) -> None:
        """
        Validate positive integer.

        Args:
            value: Integer value
            name: Parameter name

        Raises:
            ValueError: If value is not a positive integer
        """
        if not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")

        if value <= 0:
            raise ValueError(f"{name} must be positive")

    @staticmethod
    def validate_range(
        value: float,
        name: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> None:
        """
        Validate value is within range.

        Args:
            value: Value to validate
            name: Parameter name
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Raises:
            ValueError: If value is out of range
        """
        if min_val is not None and value < min_val:
            raise ValueError(f"{name} must be at least {min_val}")

        if max_val is not None and value > max_val:
            raise ValueError(f"{name} must be at most {max_val}")
