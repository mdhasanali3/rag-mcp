"""
RAG Manager Service

Manages RAG instances, caching, and lifecycle for processed directories.

Standard Practices:
- Singleton pattern per directory
- Resource pooling and management
- Graceful cleanup and shutdown
- Thread-safe operations
- Caching with TTL
"""

import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any
from threading import Lock
from datetime import datetime, timedelta

from src.config.settings import Settings
from src.monitoring.logger import get_logger
from src.monitoring.metrics import MetricsCollector
from src.services.document_processor import DocumentProcessor
from src.services.query_service import QueryService


logger = get_logger(__name__)
metrics = MetricsCollector()


class RAGInstance:
    """
    Represents a RAG instance for a specific directory.

    Maintains state and resources for a processed directory.
    """

    def __init__(
        self,
        directory_path: Path,
        api_key: str,
        settings: Settings,
        working_dir: Optional[Path] = None
    ):
        """Initialize RAG instance."""
        self.directory_path = directory_path
        self.api_key = api_key
        self.settings = settings
        self.working_dir = working_dir or settings.RAG_WORKING_DIR / directory_path.name
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.is_processing = False
        self.is_initialized = False

        # Create working directory
        self.working_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.document_processor = DocumentProcessor(settings, api_key)
        self.query_service = QueryService(settings, api_key, self.working_dir)

        logger.info(f"RAG instance created for: {directory_path}")

    def touch(self):
        """Update last accessed time."""
        self.last_accessed = datetime.utcnow()

    def get_info(self) -> Dict[str, Any]:
        """Get information about this RAG instance."""
        return {
            "directory_path": str(self.directory_path),
            "working_dir": str(self.working_dir),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "is_processing": self.is_processing,
            "is_initialized": self.is_initialized,
        }


class RAGManager:
    """
    Manages multiple RAG instances with caching and lifecycle management.

    Implements:
    - Instance caching with TTL
    - Resource pooling
    - Concurrent access control
    - Automatic cleanup
    """

    def __init__(self, settings: Settings):
        """Initialize RAG manager."""
        self.settings = settings
        self._instances: Dict[str, RAGInstance] = {}
        self._lock = Lock()
        self._cleanup_task = None

        logger.info("RAG Manager initialized")
        metrics.set_gauge("rag_manager.instances", 0)

    def get_or_create_instance(
        self,
        directory_path: str,
        api_key: str,
        working_dir: Optional[str] = None
    ) -> RAGInstance:
        """
        Get existing RAG instance or create a new one.

        Args:
            directory_path: Path to the directory
            api_key: OpenAI API key
            working_dir: Optional custom working directory

        Returns:
            RAG instance
        """
        dir_path = Path(directory_path).resolve()
        cache_key = str(dir_path)

        with self._lock:
            # Check if instance exists
            if cache_key in self._instances:
                instance = self._instances[cache_key]
                instance.touch()
                logger.debug(f"Reusing cached RAG instance: {cache_key}")
                metrics.increment("rag_manager.cache.hit")
                return instance

            # Create new instance
            work_dir = Path(working_dir) if working_dir else None
            instance = RAGInstance(dir_path, api_key, self.settings, work_dir)
            self._instances[cache_key] = instance

            # Update metrics
            metrics.increment("rag_manager.cache.miss")
            metrics.set_gauge("rag_manager.instances", len(self._instances))

            logger.info(f"Created new RAG instance: {cache_key}")
            return instance

    async def process_directory(
        self,
        directory_path: str,
        api_key: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a directory for RAG indexing.

        Args:
            directory_path: Path to directory
            api_key: OpenAI API key
            **kwargs: Additional processing options

        Returns:
            Processing results
        """
        instance = self.get_or_create_instance(directory_path, api_key, kwargs.get("working_dir"))

        if instance.is_processing:
            raise ValueError(f"Directory is already being processed: {directory_path}")

        try:
            instance.is_processing = True
            metrics.increment("rag_manager.processing.started")

            # Process documents
            result = await instance.document_processor.process_directory(
                directory_path=directory_path,
                working_dir=str(instance.working_dir),
                **kwargs
            )

            instance.is_initialized = True
            metrics.increment("rag_manager.processing.completed")

            logger.info(f"Directory processing completed: {directory_path}")
            return result

        except Exception as e:
            logger.error(f"Error processing directory {directory_path}: {e}", exc_info=True)
            metrics.increment("rag_manager.processing.error")
            raise
        finally:
            instance.is_processing = False

    async def process_single_document(
        self,
        file_path: str,
        api_key: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a single document.

        Args:
            file_path: Path to file
            api_key: OpenAI API key
            **kwargs: Additional processing options

        Returns:
            Processing results
        """
        # Get parent directory instance
        file = Path(file_path)
        directory_path = str(file.parent)

        instance = self.get_or_create_instance(directory_path, api_key, kwargs.get("working_dir"))

        try:
            metrics.increment("rag_manager.document.started")

            result = await instance.document_processor.process_single_document(
                file_path=file_path,
                **kwargs
            )

            metrics.increment("rag_manager.document.completed")
            logger.info(f"Document processing completed: {file_path}")
            return result

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}", exc_info=True)
            metrics.increment("rag_manager.document.error")
            raise

    async def query_directory(
        self,
        directory_path: str,
        query: str,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Query a processed directory.

        Args:
            directory_path: Path to directory
            query: Query string
            mode: Query mode

        Returns:
            Query results
        """
        dir_path = Path(directory_path).resolve()
        cache_key = str(dir_path)

        with self._lock:
            if cache_key not in self._instances:
                raise ValueError(f"Directory not processed: {directory_path}")

            instance = self._instances[cache_key]
            instance.touch()

        if not instance.is_initialized:
            raise ValueError(f"Directory not fully initialized: {directory_path}")

        try:
            metrics.increment("rag_manager.query.started")

            result = await instance.query_service.query(
                query=query,
                mode=mode
            )

            metrics.increment("rag_manager.query.completed")
            return result

        except Exception as e:
            logger.error(f"Error querying directory {directory_path}: {e}", exc_info=True)
            metrics.increment("rag_manager.query.error")
            raise

    async def query_with_multimodal(
        self,
        directory_path: str,
        query: str,
        multimodal_content: List[Dict[str, Any]],
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Query with multimodal content.

        Args:
            directory_path: Path to directory
            query: Query string
            multimodal_content: List of multimodal content items
            mode: Query mode

        Returns:
            Query results
        """
        dir_path = Path(directory_path).resolve()
        cache_key = str(dir_path)

        with self._lock:
            if cache_key not in self._instances:
                raise ValueError(f"Directory not processed: {directory_path}")

            instance = self._instances[cache_key]
            instance.touch()

        try:
            metrics.increment("rag_manager.multimodal_query.started")

            result = await instance.query_service.query_with_multimodal(
                query=query,
                multimodal_content=multimodal_content,
                mode=mode
            )

            metrics.increment("rag_manager.multimodal_query.completed")
            return result

        except Exception as e:
            logger.error(f"Error in multimodal query: {e}", exc_info=True)
            metrics.increment("rag_manager.multimodal_query.error")
            raise

    def list_processed_directories(self) -> List[Dict[str, Any]]:
        """
        List all processed directories.

        Returns:
            List of directory information
        """
        with self._lock:
            return [
                instance.get_info()
                for instance in self._instances.values()
            ]

    def get_rag_info(self, directory_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific RAG instance.

        Args:
            directory_path: Path to directory

        Returns:
            RAG instance information or None
        """
        dir_path = Path(directory_path).resolve()
        cache_key = str(dir_path)

        with self._lock:
            instance = self._instances.get(cache_key)
            return instance.get_info() if instance else None

    def cleanup_stale_instances(self, ttl_seconds: int = 3600):
        """
        Clean up instances that haven't been accessed recently.

        Args:
            ttl_seconds: Time-to-live in seconds
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=ttl_seconds)

        with self._lock:
            stale_keys = [
                key for key, instance in self._instances.items()
                if instance.last_accessed < cutoff_time and not instance.is_processing
            ]

            for key in stale_keys:
                logger.info(f"Removing stale RAG instance: {key}")
                del self._instances[key]
                metrics.increment("rag_manager.cleanup.removed")

            metrics.set_gauge("rag_manager.instances", len(self._instances))

    async def cleanup(self):
        """Cleanup all instances and resources."""
        logger.info("Cleaning up RAG Manager...")

        with self._lock:
            for key, instance in self._instances.items():
                logger.debug(f"Cleaning up instance: {key}")
                # Add any necessary cleanup for instance
                pass

            self._instances.clear()
            metrics.set_gauge("rag_manager.instances", 0)

        logger.info("RAG Manager cleanup completed")
