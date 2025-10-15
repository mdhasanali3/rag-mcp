"""
RAG Anything MCP Server - Main Entry Point

This module serves as the main entry point for the MCP (Model Context Protocol) server
that provides comprehensive RAG (Retrieval-Augmented Generation) capabilities.

Production-ready implementation with proper error handling, logging, and monitoring.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.stdio import stdio_server
from src.config.settings import Settings
from src.monitoring.logger import setup_logging, get_logger
from src.monitoring.metrics import MetricsCollector
from src.tools.registry import ToolRegistry
from src.services.rag_manager import RAGManager


logger = get_logger(__name__)
metrics = MetricsCollector()


class MCPServer:
    """
    Main MCP Server class that orchestrates all RAG operations.

    This class follows the Singleton pattern to ensure only one instance
    of the server exists throughout the application lifecycle.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPServer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the MCP server with all required components."""
        if self._initialized:
            return

        self.settings = Settings()
        self.rag_manager = RAGManager(self.settings)
        self.tool_registry = ToolRegistry(self.rag_manager, self.settings)
        self._initialized = True

        logger.info("MCP Server initialized successfully")
        metrics.increment("server.initialization.success")

    async def run(self):
        """
        Run the MCP server using stdio transport.

        This method sets up the server with all registered tools and
        starts listening for incoming requests via standard input/output.
        """
        try:
            logger.info("Starting RAG Anything MCP Server...")
            logger.info(f"Environment: {self.settings.ENVIRONMENT}")
            logger.info(f"Log Level: {self.settings.LOG_LEVEL}")

            # Get all registered tools from the registry
            tools = self.tool_registry.get_all_tools()

            logger.info(f"Registered {len(tools)} tools")
            for tool_name in tools.keys():
                logger.debug(f"  - {tool_name}")

            # Start the MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                from mcp.server import Server

                server = Server("rag-anything-mcp")

                # Register all tools with the server
                for tool_name, tool_handler in tools.items():
                    server.add_tool(tool_name, tool_handler)

                logger.info("MCP Server running and ready to accept connections")
                metrics.increment("server.start.success")

                # Run the server
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options()
                )

        except KeyboardInterrupt:
            logger.info("Server shutdown requested by user")
            metrics.increment("server.shutdown.graceful")
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            metrics.increment("server.error.critical")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Perform cleanup operations before server shutdown."""
        try:
            logger.info("Performing cleanup operations...")

            # Close all RAG instances
            if hasattr(self, 'rag_manager'):
                await self.rag_manager.cleanup()

            # Flush metrics
            if metrics:
                metrics.flush()

            logger.info("Cleanup completed successfully")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)


def main():
    """
    Application entry point.

    Sets up logging and starts the MCP server.
    """
    try:
        # Setup logging configuration
        setup_logging()

        # Create and run server
        server = MCPServer()
        asyncio.run(server.run())

    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
