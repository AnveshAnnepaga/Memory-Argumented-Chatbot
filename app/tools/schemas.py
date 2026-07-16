"""
Tool Execution Framework Schemas (Milestone 13)

Defines rigorous, decoupled Pydantic models for tool requests, definitions,
responses, execution metadata, and pipeline context.
"""

import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ToolRequest(BaseModel):
    """
    Standardized request sent to the Tool Manager or Executor.
    """
    query: str = Field(..., description="The original or targeted user query requesting tool action.")
    tool_name: Optional[str] = Field(default=None, description="Explicit name of tool to invoke, if routed.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters for the tool invocation.")
    user_id: str = Field(default="default", description="Identifier for the user initiating the request.")
    session_id: str = Field(default="default", description="Session ID for context tracing.")


class ToolMetadata(BaseModel):
    """
    Metadata describing the provenance and execution metrics of a tool call.
    """
    source_api: str = Field(default="internal", description="Name of external API or internal engine.")
    rate_limit_remaining: Optional[int] = Field(default=None, description="Remaining API calls in current window if applicable.")
    timestamp: datetime = Field(default_factory=_utcnow, description="UTC timestamp when execution finished.")


class ToolResponse(BaseModel):
    """
    Standardized, normalized response returned by any tool execution.
    Never exposes raw unhandled exceptions to downstream orchestrators.
    """
    success: bool = Field(..., description="Whether the tool executed successfully.")
    tool_name: str = Field(..., description="Name of the executed tool.")
    data: Any = Field(default=None, description="Payload data if successful.")
    error: Optional[str] = Field(default=None, description="Error message if execution failed.")
    execution_time_ms: float = Field(default=0.0, description="Duration of execution in milliseconds.")
    cached: bool = Field(default=False, description="Whether the response was retrieved from the TTL cache.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance or execution metadata.")


class ToolDefinition(BaseModel):
    """
    Definition of an independent tool registered in the ToolRegistry.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Unique identifier of the tool (e.g. 'weather', 'calculator').")
    description: str = Field(..., description="Clear description of what the tool does and when to use it.")
    category: str = Field(..., description="Logical category (e.g. 'search', 'math', 'utility').")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema defining required and optional input parameters.")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema defining expected output payload.")
    priority: int = Field(default=10, description="Execution priority (lower numbers execute first in sequential batches).")
    timeout: float = Field(default=5.0, description="Maximum allowed execution duration in seconds.")
    allow_parallel: bool = Field(default=True, description="Whether this tool safely executes in parallel with other tools.")
    cache_ttl_seconds: int = Field(default=0, description="Cache time-to-live in seconds (0 means caching disabled).")
    handler: Optional[Callable[..., Any]] = Field(default=None, description="Async or sync callable function implementing tool execution.")


class ToolExecution(BaseModel):
    """
    Internal tracking object representing an active tool execution.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: ToolRequest
    definition: ToolDefinition
    start_time: float = Field(default_factory=time.perf_counter)


class ToolResult(BaseModel):
    """
    Raw execution result captured right after handler completion before normalization.
    """
    success: bool
    raw_output: Any = None
    error_message: Optional[str] = None


class ToolContext(BaseModel):
    """
    Context passed alongside tool requests containing session parameters and global constraints.
    """
    user_id: str = Field(default="default")
    session_id: str = Field(default="default")
    global_timeout: float = Field(default=15.0)
    extra_config: Dict[str, Any] = Field(default_factory=dict)
