"""
Tool Registry

Manages all MCP tools and their handlers.

Standard Practices:
- Registry pattern for tool management
- Lazy loading of handlers
- Input validation
- Error handling wrappers
"""

from typing import Dict, Callable, Any
from functools import wraps

from src.config.settings import Settings
from src.services.rag_manager import RAGManager
from src.monitoring.logger import get_logger
from src.monitoring.metrics import MetricsCollector, timer
from src.tools.handlers import (
    ProcessDirectoryHandler,
    ProcessSingleDocumentHandler,
    QueryDirectoryHandler,
    QueryWithMultimodalHandler,
    ListProcessedDirectoriesHandler,
    GetRAGInfoHandler
)


logger = get_logger(__name__)
metrics = MetricsCollector()


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors in tool execution."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            metrics.increment(f"tools.{func.__name__}.validation_error")
            return {
                "success": False,
                "error": str(e),
                "error_type": "ValidationError"
            }
        except FileNotFoundError as e:
            logger.error(f"File not found in {func.__name__}: {e}")
            metrics.increment(f"tools.{func.__name__}.file_not_found")
            return {
                "success": False,
                "error": str(e),
                "error_type": "FileNotFoundError"
            }
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            metrics.increment(f"tools.{func.__name__}.error")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    return wrapper


class ToolRegistry:
    """
    Registry for all MCP tools.

    Manages tool registration, validation, and execution.
    """

    def __init__(self, rag_manager: RAGManager, settings: Settings):
        """Initialize tool registry."""
        self.rag_manager = rag_manager
        self.settings = settings
        self._tools: Dict[str, Callable] = {}

        # Initialize handlers
        self._initialize_handlers()

        logger.info(f"Tool Registry initialized with {len(self._tools)} tools")

    def _initialize_handlers(self):
        """Initialize all tool handlers."""
        # Create handler instances
        process_dir_handler = ProcessDirectoryHandler(self.rag_manager, self.settings)
        process_doc_handler = ProcessSingleDocumentHandler(self.rag_manager, self.settings)
        query_handler = QueryDirectoryHandler(self.rag_manager)
        multimodal_handler = QueryWithMultimodalHandler(self.rag_manager)
        list_handler = ListProcessedDirectoriesHandler(self.rag_manager)
        info_handler = GetRAGInfoHandler(self.rag_manager)

        # Register tools
        self.register_tool("process_directory", process_dir_handler.handle)
        self.register_tool("process_single_document", process_doc_handler.handle)
        self.register_tool("query_directory", query_handler.handle)
        self.register_tool("query_with_multimodal_content", multimodal_handler.handle)
        self.register_tool("list_processed_directories", list_handler.handle)
        self.register_tool("get_rag_info", info_handler.handle)

    def register_tool(self, name: str, handler: Callable):
        """
        Register a tool with its handler.

        Args:
            name: Tool name
            handler: Tool handler function
        """
        # Wrap handler with error handling
        wrapped_handler = handle_errors(handler)

        self._tools[name] = wrapped_handler
        logger.debug(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Callable:
        """
        Get a tool handler by name.

        Args:
            name: Tool name

        Returns:
            Tool handler function

        Raises:
            ValueError: If tool not found
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        return self._tools[name]

    def get_all_tools(self) -> Dict[str, Callable]:
        """
        Get all registered tools.

        Returns:
            Dictionary of tool name to handler
        """
        return self._tools.copy()

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
