"""
Milestone 13: Tool System & External Function Calling Package

Exports core Pydantic schemas, registry, non-LLM router, high-performance
executor, manager, pipeline orchestrator, and singleton instances.
"""

from app.tools.executor import ToolExecutor, tool_executor
from app.tools.manager import ToolManager, tool_manager
from app.tools.pipeline import ToolPipeline, tool_pipeline
from app.tools.registry import ToolRegistry, tool_registry
from app.tools.router import (
    ROUTE_CALCULATOR,
    ROUTE_CURRENCY,
    ROUTE_NO_TOOL,
    ROUTE_TIME,
    ROUTE_TRANSLATION,
    ROUTE_UNIT,
    ROUTE_WEATHER,
    ROUTE_WEB_SEARCH,
    ToolRouter,
    tool_router,
)
from app.tools.schemas import (
    ToolContext,
    ToolDefinition,
    ToolExecution,
    ToolMetadata,
    ToolRequest,
    ToolResponse,
    ToolResult,
)

__all__ = [
    # Schemas
    "ToolRequest",
    "ToolResponse",
    "ToolDefinition",
    "ToolExecution",
    "ToolMetadata",
    "ToolResult",
    "ToolContext",
    # Classes
    "ToolRegistry",
    "ToolRouter",
    "ToolExecutor",
    "ToolManager",
    "ToolPipeline",
    # Singletons
    "tool_registry",
    "tool_router",
    "tool_executor",
    "tool_manager",
    "tool_pipeline",
    # Route Constants
    "ROUTE_WEB_SEARCH",
    "ROUTE_WEATHER",
    "ROUTE_CALCULATOR",
    "ROUTE_CURRENCY",
    "ROUTE_TIME",
    "ROUTE_UNIT",
    "ROUTE_TRANSLATION",
    "ROUTE_NO_TOOL",
]
