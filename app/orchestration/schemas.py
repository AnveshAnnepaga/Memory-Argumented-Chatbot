# File: app/orchestration/schemas.py
"""
(`Milestone 11 LangGraph Orchestration Schemas`)
Pydantic schemas representing query intents, router routing decisions, prompt contexts,
metadata tracking, and end-to-end orchestration responses.
Strictly Single Responsibility Principle with zero duplicated logic.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RouteType(str, Enum):
    """Possible routing destinations decided by the Intelligent Router."""
    DIRECT_LLM = "DIRECT_LLM"
    HYBRID_RAG = "HYBRID_RAG"
    GRAPH_RAG = "GRAPH_RAG"
    HYBRID_SYNTHESIS = "HYBRID_SYNTHESIS"
    UNKNOWN = "UNKNOWN"


class IntentType(str, Enum):
    """High-level semantic intent of the incoming user query."""
    GREETING = "GREETING"
    TECHNICAL_DOCS = "TECHNICAL_DOCS"
    RELATIONSHIP_QUERY = "RELATIONSHIP_QUERY"
    MIXED_REASONING = "MIXED_REASONING"
    GENERAL_CHAT = "GENERAL_CHAT"


class IntentResult(BaseModel):
    """Results of query intent classification."""
    model_config = ConfigDict(from_attributes=True)

    intent: IntentType = Field(default=IntentType.GENERAL_CHAT, description="Classified intent type")
    confidence: float = Field(default=0.95, description="Confidence rating between 0.0 and 1.0")
    keywords: List[str] = Field(default_factory=list, description="Extracted key concepts or technical terms")
    reasoning: str = Field(default="", description="Explanation of why this intent was selected")


class RouterDecision(BaseModel):
    """
    Intelligent Router routing decision specifying exact execution dependencies and branches.
    Does not call the LLM directly; operates on high-speed semantic classification.
    """
    model_config = ConfigDict(from_attributes=True)

    route: RouteType = Field(default=RouteType.DIRECT_LLM, description="Selected primary execution route")
    confidence: float = Field(default=0.95, description="Router decision confidence rating")
    requires_rag: bool = Field(default=False, description="Whether Hybrid RAG retrieval should be executed")
    requires_graph: bool = Field(default=False, description="Whether Knowledge Graph retrieval should be executed")
    requires_memory: bool = Field(default=False, description="Placeholder for Milestone 12 Long-Term Memory")
    requires_tools: bool = Field(default=False, description="Placeholder for Milestone 13 External Tools")
    reasoning: str = Field(default="", description="Detailed rationale for the chosen route")


class PromptContext(BaseModel):
    """
    Assembled prompt block combining system instructions, retrieved RAG chunks,
    and structured GraphRAG relationships before LLM generation.
    No node except Prompt Builder constructs or modifies this structure.
    """
    model_config = ConfigDict(from_attributes=True)

    user_query: str = Field(..., description="Original user prompt")
    system_prompt: str = Field(default="", description="Core agent system prompt instructions")
    rag_context: str = Field(default="", description="Retrieved chunks from Hybrid RAG engine")
    graph_context: str = Field(default="", description="Retrieved relationships from Knowledge Graph engine")
    memory_context: str = Field(default="", description="Placeholder for Milestone 12 memory summaries")
    tool_context: str = Field(default="", description="Placeholder for Milestone 13 external tool outputs")
    final_prompt: str = Field(default="", description="The exact consolidated prompt text submitted to Groq LLM")


class WorkflowMetadata(BaseModel):
    """End-to-end execution diagnostics, token budgets, and StateGraph transition path."""
    model_config = ConfigDict(from_attributes=True)

    conversation_id: str = Field(default="default", description="Unique conversation session identifier")
    user_id: str = Field(default="default", description="Unique user identifier")
    route_taken: RouteType = Field(default=RouteType.UNKNOWN, description="The actual route executed by the state machine")
    rag_tokens: int = Field(default=0, description="Estimated token count of retrieved RAG context")
    graph_tokens: int = Field(default=0, description="Estimated token count of retrieved Graph context")
    memory_tokens: int = Field(default=0, description="Estimated token count of retrieved Memory context")
    tool_tokens: int = Field(default=0, description="Estimated token count of retrieved Tool context")
    total_prompt_tokens: int = Field(default=0, description="Estimated token count of the final LLM prompt")
    execution_time_ms: float = Field(default=0.0, description="Total workflow execution latency in milliseconds")
    node_path: List[str] = Field(default_factory=list, description="Chronological sequence of LangGraph nodes executed")
    errors: List[str] = Field(default_factory=list, description="Any non-fatal warnings or fallback errors encountered")
    retrieved_chunks: List[Any] = Field(default_factory=list, description="Retrieved document chunks from RAG retrieval node")


class WorkflowResponse(BaseModel):
    """
    Final public payload returned by the LangGraph Orchestrator (`pipeline.process_query`).
    Single clean API response for FastAPI routes.
    """
    model_config = ConfigDict(from_attributes=True)

    response: str = Field(..., description="Final text generated by Groq LLM or system fallbacks")
    intent: IntentResult = Field(..., description="Intent classification details")
    router_decision: RouterDecision = Field(..., description="Router execution path details")
    metadata: WorkflowMetadata = Field(..., description="Execution diagnostics and node transition path")
    prompt_context: Optional[PromptContext] = Field(default=None, description="Detailed prompt composition breakdown")
    evaluation: Optional[Dict[str, Any]] = Field(default=None, description="Read-only evaluation telemetry report from EvaluationPipeline")
