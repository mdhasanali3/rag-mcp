"""
MCP Tool Handlers

Individual handler implementations for each MCP tool.

Standard Practices:
- One handler class per tool
- Input validation
- Detailed logging
- Metrics collection
"""

from typing import Dict, Any, List, Optional

from src.config.settings import Settings
from src.services.rag_manager import RAGManager
from src.monitoring.logger import get_logger
from src.monitoring.metrics import MetricsCollector, timer


logger = get_logger(__name__)
metrics = MetricsCollector()


class BaseHandler:
    """Base class for tool handlers."""

    def __init__(self, rag_manager: RAGManager):
        """Initialize handler."""
        self.rag_manager = rag_manager

    def validate_required_params(self, params: Dict[str, Any], required: List[str]):
        """Validate required parameters."""
        missing = [p for p in required if p not in params or params[p] is None]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")


class ProcessDirectoryHandler(BaseHandler):
    """Handler for process_directory tool."""

    def __init__(self, rag_manager: RAGManager, settings: Settings):
        """Initialize handler."""
        super().__init__(rag_manager)
        self.settings = settings

    @timer("tools.process_directory")
    async def handle(self, **params) -> Dict[str, Any]:
        """
        Handle directory processing request.

        Required params:
            - directory_path: str
            - api_key: str

        Optional params:
            - working_dir: str
            - base_url: str
            - file_extensions: List[str]
            - recursive: bool
            - enable_image_processing: bool
            - enable_table_processing: bool
            - enable_equation_processing: bool
            - max_workers: int
        """
        # Validate required parameters
        self.validate_required_params(params, ["directory_path", "api_key"])

        directory_path = params["directory_path"]
        api_key = params["api_key"]

        logger.info(f"Processing directory: {directory_path}")
        metrics.increment("tools.process_directory.invocations")

        # Process directory
        result = await self.rag_manager.process_directory(
            directory_path=directory_path,
            api_key=api_key,
            working_dir=params.get("working_dir"),
            file_extensions=params.get("file_extensions", self.settings.SUPPORTED_FILE_EXTENSIONS),
            recursive=params.get("recursive", True),
            enable_image_processing=params.get("enable_image_processing", True),
            enable_table_processing=params.get("enable_table_processing", True),
            enable_equation_processing=params.get("enable_equation_processing", True),
            max_workers=params.get("max_workers", self.settings.RAG_MAX_WORKERS)
        )

        result["success"] = True
        return result


class ProcessSingleDocumentHandler(BaseHandler):
    """Handler for process_single_document tool."""

    def __init__(self, rag_manager: RAGManager, settings: Settings):
        """Initialize handler."""
        super().__init__(rag_manager)
        self.settings = settings

    @timer("tools.process_single_document")
    async def handle(self, **params) -> Dict[str, Any]:
        """
        Handle single document processing request.

        Required params:
            - file_path: str
            - api_key: str

        Optional params:
            - working_dir: str
            - base_url: str
            - output_dir: str
            - parse_method: str
            - enable_image_processing: bool
            - enable_table_processing: bool
            - enable_equation_processing: bool
        """
        # Validate required parameters
        self.validate_required_params(params, ["file_path", "api_key"])

        file_path = params["file_path"]
        api_key = params["api_key"]

        logger.info(f"Processing document: {file_path}")
        metrics.increment("tools.process_single_document.invocations")

        # Process document
        result = await self.rag_manager.process_single_document(
            file_path=file_path,
            api_key=api_key,
            working_dir=params.get("working_dir"),
            output_dir=params.get("output_dir"),
            parse_method=params.get("parse_method", "auto"),
            enable_image_processing=params.get("enable_image_processing", True),
            enable_table_processing=params.get("enable_table_processing", True),
            enable_equation_processing=params.get("enable_equation_processing", True)
        )

        result["success"] = True
        return result


class QueryDirectoryHandler(BaseHandler):
    """Handler for query_directory tool."""

    @timer("tools.query_directory")
    async def handle(self, **params) -> Dict[str, Any]:
        """
        Handle directory query request.

        Required params:
            - directory_path: str
            - query: str

        Optional params:
            - mode: str (default: "hybrid")
        """
        # Validate required parameters
        self.validate_required_params(params, ["directory_path", "query"])

        directory_path = params["directory_path"]
        query = params["query"]
        mode = params.get("mode", "hybrid")

        logger.info(f"Querying directory: {directory_path}")
        metrics.increment("tools.query_directory.invocations")

        # Execute query
        result = await self.rag_manager.query_directory(
            directory_path=directory_path,
            query=query,
            mode=mode
        )

        result["success"] = True
        return result


class QueryWithMultimodalHandler(BaseHandler):
    """Handler for query_with_multimodal_content tool."""

    @timer("tools.query_with_multimodal_content")
    async def handle(self, **params) -> Dict[str, Any]:
        """
        Handle multimodal query request.

        Required params:
            - directory_path: str
            - query: str
            - multimodal_content: List[Dict]

        Optional params:
            - mode: str (default: "hybrid")
        """
        # Validate required parameters
        self.validate_required_params(params, ["directory_path", "query", "multimodal_content"])

        directory_path = params["directory_path"]
        query = params["query"]
        multimodal_content = params["multimodal_content"]
        mode = params.get("mode", "hybrid")

        logger.info(f"Multimodal query on directory: {directory_path}")
        metrics.increment("tools.query_with_multimodal_content.invocations")

        # Execute query
        result = await self.rag_manager.query_with_multimodal(
            directory_path=directory_path,
            query=query,
            multimodal_content=multimodal_content,
            mode=mode
        )

        result["success"] = True
        return result


class ListProcessedDirectoriesHandler(BaseHandler):
    """Handler for list_processed_directories tool."""

    @timer("tools.list_processed_directories")
    async def handle(self, **params) -> Dict[str, Any]:
        """
        Handle list directories request.

        No parameters required.
        """
        logger.info("Listing processed directories")
        metrics.increment("tools.list_processed_directories.invocations")

        directories = self.rag_manager.list_processed_directories()

        return {
            "success": True,
            "directories": directories,
            "total_count": len(directories)
        }


class GetRAGInfoHandler(BaseHandler):
    """Handler for get_rag_info tool."""

    @timer("tools.get_rag_info")
    async def handle(self, **params) -> Dict[str, Any]:
        """
        Handle get RAG info request.

        Required params:
            - directory_path: str
        """
        # Validate required parameters
        self.validate_required_params(params, ["directory_path"])

        directory_path = params["directory_path"]

        logger.info(f"Getting RAG info for: {directory_path}")
        metrics.increment("tools.get_rag_info.invocations")

        info = self.rag_manager.get_rag_info(directory_path)

        if info is None:
            return {
                "success": False,
                "error": f"No RAG instance found for directory: {directory_path}",
                "error_type": "NotFoundError"
            }

        return {
            "success": True,
            "info": info
        }
