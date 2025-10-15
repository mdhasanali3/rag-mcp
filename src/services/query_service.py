"""
Query Service

Handles querying processed documents using RAG.

Standard Practices:
- Async query execution
- Multiple query modes
- Result caching
- Error handling and fallbacks
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config.settings import Settings
from src.monitoring.logger import get_logger
from src.monitoring.metrics import MetricsCollector, timer


logger = get_logger(__name__)
metrics = MetricsCollector()


class QueryService:
    """
    Service for querying processed documents.

    Supports:
    - Multiple query modes (hybrid, local, global, etc.)
    - Multimodal content integration
    - Result caching
    - Fallback strategies
    """

    VALID_MODES = ["hybrid", "local", "global", "naive", "mix", "bypass"]

    def __init__(self, settings: Settings, api_key: str, working_dir: Path):
        """Initialize query service."""
        self.settings = settings
        self.api_key = api_key
        self.working_dir = working_dir
        self._cache = {} if settings.ENABLE_CACHE else None

        logger.info(f"Query Service initialized for: {working_dir}")

    async def query(
        self,
        query: str,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Execute a text query.

        Args:
            query: Query string
            mode: Query mode

        Returns:
            Query results
        """
        self._validate_mode(mode)

        logger.info(f"Executing query with mode '{mode}': {query[:100]}")
        metrics.increment("query_service.queries.started", labels={"mode": mode})

        # Check cache
        cache_key = f"{mode}:{query}"
        if self._cache is not None and cache_key in self._cache:
            logger.debug(f"Cache hit for query: {query[:50]}")
            metrics.increment("query_service.cache.hit")
            return self._cache[cache_key]

        with timer(f"query_service.query.{mode}"):
            try:
                # This is where you would integrate with raganything/LightRAG
                # For now, placeholder implementation
                result = {
                    "query": query,
                    "mode": mode,
                    "response": f"Placeholder response for query: {query}",
                    "sources": [
                        {
                            "document": "example_doc.pdf",
                            "page": 1,
                            "relevance_score": 0.95,
                            "excerpt": "Relevant text excerpt..."
                        }
                    ],
                    "metadata": {
                        "working_dir": str(self.working_dir),
                        "total_sources": 1,
                        "processing_time_ms": 150
                    }
                }

                # Cache result
                if self._cache is not None:
                    self._cache[cache_key] = result

                metrics.increment("query_service.queries.success", labels={"mode": mode})
                logger.info(f"Query completed successfully")
                return result

            except Exception as e:
                metrics.increment("query_service.queries.error", labels={"mode": mode})
                logger.error(f"Error executing query: {e}", exc_info=True)
                raise

    async def query_with_multimodal(
        self,
        query: str,
        multimodal_content: List[Dict[str, Any]],
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Execute a query with multimodal content.

        Args:
            query: Query string
            multimodal_content: List of multimodal content items
            mode: Query mode

        Returns:
            Query results
        """
        self._validate_mode(mode)

        logger.info(f"Executing multimodal query with {len(multimodal_content)} items")
        metrics.increment("query_service.multimodal_queries.started", labels={"mode": mode})

        with timer(f"query_service.multimodal_query.{mode}"):
            try:
                # Validate multimodal content
                validated_content = self._validate_multimodal_content(multimodal_content)

                # Execute query with multimodal context
                # Placeholder implementation
                result = {
                    "query": query,
                    "mode": mode,
                    "multimodal_items": len(validated_content),
                    "response": f"Placeholder multimodal response for: {query}",
                    "sources": [
                        {
                            "document": "example_doc.pdf",
                            "page": 1,
                            "relevance_score": 0.95,
                            "excerpt": "Relevant text excerpt..."
                        }
                    ],
                    "multimodal_analysis": {
                        "tables_processed": sum(1 for c in validated_content if c["type"] == "table"),
                        "equations_processed": sum(1 for c in validated_content if c["type"] == "equation"),
                        "images_processed": sum(1 for c in validated_content if c["type"] == "image"),
                    },
                    "metadata": {
                        "working_dir": str(self.working_dir),
                        "total_sources": 1,
                        "processing_time_ms": 250
                    }
                }

                metrics.increment("query_service.multimodal_queries.success", labels={"mode": mode})
                logger.info("Multimodal query completed successfully")
                return result

            except Exception as e:
                metrics.increment("query_service.multimodal_queries.error", labels={"mode": mode})
                logger.error(f"Error executing multimodal query: {e}", exc_info=True)
                raise

    def _validate_mode(self, mode: str):
        """Validate query mode."""
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Invalid query mode: {mode}. Valid modes: {', '.join(self.VALID_MODES)}"
            )

    def _validate_multimodal_content(
        self,
        content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate multimodal content structure.

        Args:
            content: List of multimodal content items

        Returns:
            Validated content

        Raises:
            ValueError: If content is invalid
        """
        if not isinstance(content, list):
            raise ValueError("multimodal_content must be a list")

        validated = []
        for item in content:
            if not isinstance(item, dict):
                raise ValueError("Each multimodal item must be a dictionary")

            if "type" not in item:
                raise ValueError("Each multimodal item must have a 'type' field")

            item_type = item["type"]

            if item_type == "table":
                if "table_data" not in item:
                    raise ValueError("Table items must have 'table_data' field")
            elif item_type == "equation":
                if "latex" not in item:
                    raise ValueError("Equation items must have 'latex' field")
            elif item_type == "image":
                if "image_url" not in item and "image_path" not in item:
                    raise ValueError("Image items must have 'image_url' or 'image_path' field")
            else:
                logger.warning(f"Unknown multimodal content type: {item_type}")

            validated.append(item)

        return validated
