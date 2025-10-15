"""
Logging Module

Provides structured logging capabilities with support for:
- JSON and text formatting
- Multiple log levels
- File and console output
- Contextual logging
- Performance logging

Standard Practices:
- Structured logging for better searchability
- Log levels following Python logging standards
- Rotation for file-based logging
- Contextual information (request_id, user_id, etc.)
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation systems
    like ELK, Splunk, or CloudWatch.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ContextualLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log records.

    Useful for adding request IDs, user IDs, or other contextual data
    to all log messages within a specific context.
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """Initialize the contextual logger."""
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log messages."""
        if "extra_fields" not in kwargs:
            kwargs["extra_fields"] = {}

        kwargs["extra_fields"].update(self.extra)
        return msg, kwargs


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[Path] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup application logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        log_file: Path to log file (None for stdout only)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep

    Example:
        >>> setup_logging(log_level="DEBUG", log_format="json")
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Choose formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger instance with optional contextual information.

    Args:
        name: Logger name (usually __name__)
        extra: Extra contextual fields to add to all log messages

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__, {"request_id": "123"})
        >>> logger.info("Processing request")
    """
    logger = logging.getLogger(name)

    if extra:
        return ContextualLogger(logger, extra)

    return logger


class PerformanceLogger:
    """
    Context manager for logging performance metrics.

    Usage:
        >>> with PerformanceLogger("process_document"):
        ...     # Your code here
        ...     pass
    """

    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """Initialize performance logger."""
        self.operation_name = operation_name
        self.logger = logger or get_logger(__name__)
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log duration."""
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                extra={"extra_fields": {"duration_seconds": duration}}
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                extra={"extra_fields": {"duration_seconds": duration, "error": str(exc_val)}}
            )
