# File: app/evaluation/schemas.py
"""
(`Milestone 14 Evaluation & Observability Schemas`)
Defines strict Pydantic V2 data contracts for read-only telemetry observation,
layer-level evaluation metrics, monitoring event logs, structured reports,
and JSON-only dashboard payloads.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# 1. Layer-Specific Evaluation Metrics
# =============================================================================

class RAGMetrics(BaseModel):
    """Evaluation metrics for the Hybrid RAG layer."""
    model_config = ConfigDict(from_attributes=True)

    retrieval_precision: float = Field(default=0.0, description="Precision of retrieved chunks (relevant / retrieved)")
    retrieval_recall: float = Field(default=0.0, description="Recall of retrieved chunks (retrieved relevant / all relevant)")
    mrr: float = Field(default=0.0, description="Mean Reciprocal Rank across queries")
    hit_at_k: float = Field(default=0.0, description="Hit rate at top K retrieved chunks")
    context_precision: float = Field(default=0.0, description="Precision of context snippet text against user query")
    context_recall: float = Field(default=0.0, description="Recall of context snippet text against answer facts")
    context_relevance: float = Field(default=0.0, description="Semantic relevance score of context to query")
    context_utilization: float = Field(default=0.0, description="Fraction of retrieved context tokens actually referenced in answer")
    groundedness: float = Field(default=0.0, description="Extent to which answer claims are supported by context")
    faithfulness: float = Field(default=0.0, description="Absence of contradictions with retrieved chunks")
    citation_coverage: float = Field(default=0.0, description="Proportion of key claims paired with valid source citations")


class GraphMetrics(BaseModel):
    """Evaluation metrics for the Knowledge Graph (GraphRAG) layer."""
    model_config = ConfigDict(from_attributes=True)

    entity_accuracy: float = Field(default=0.0, description="Accuracy of canonical entities resolved in graph")
    relationship_accuracy: float = Field(default=0.0, description="Accuracy of extracted USES/DEPENDS_ON/etc relationships")
    confidence_distribution: Dict[str, float] = Field(default_factory=dict, description="Mean confidence score per relationship type")
    average_node_degree: float = Field(default=0.0, description="Average number of edges connected to queried nodes")
    graph_density: float = Field(default=0.0, description="Structural density ratio of the retrieved subgraph")
    connected_components: int = Field(default=0, description="Number of connected components in retrieved subgraph")
    traversal_latency_ms: float = Field(default=0.0, description="Latency of multi-hop graph traversal in milliseconds")
    shortest_path_latency_ms: float = Field(default=0.0, description="Latency of path finding in milliseconds")
    graph_context_quality: float = Field(default=0.0, description="Relevance and structural clarity of formatted graph context")


class MemoryMetrics(BaseModel):
    """Evaluation metrics for the Long-Term Memory System layer."""
    model_config = ConfigDict(from_attributes=True)

    memory_retrieval_accuracy: float = Field(default=0.0, description="Accuracy of retrieved user facts against query intent")
    memory_ranking_quality: float = Field(default=0.0, description="Quality of vector ranking for semantic memory facts")
    conflict_resolution_accuracy: float = Field(default=0.0, description="Accuracy in resolving contradictory historical facts")
    memory_compression_ratio: float = Field(default=1.0, description="Ratio of summarized episodic memory size to raw history")
    memory_freshness: float = Field(default=1.0, description="Time decay factor / freshness score of retrieved memories")
    memory_utilization: float = Field(default=0.0, description="Fraction of retrieved memory facts directly referenced in output")
    memory_token_usage: int = Field(default=0, description="Total tokens consumed by memory context")


class ToolMetrics(BaseModel):
    """Evaluation metrics for the Tool Execution System layer."""
    model_config = ConfigDict(from_attributes=True)

    correct_tool_selection: float = Field(default=0.0, description="Binary or probabilistic accuracy of tool selection decision")
    tool_success_rate: float = Field(default=0.0, description="Fraction of tool executions completing with success=True")
    retry_count: int = Field(default=0, description="Total number of retry attempts triggered during execution")
    timeout_count: int = Field(default=0, description="Total number of tool execution timeouts incurred")
    average_execution_time_ms: float = Field(default=0.0, description="Mean latency across executed tool handlers")
    cache_hit_ratio: float = Field(default=0.0, description="Proportion of tool calls served directly from TTL cache")
    parallel_execution_speedup: float = Field(default=1.0, description="Speedup ratio achieved via asyncio.gather batching vs sequential")


class LangGraphMetrics(BaseModel):
    """Evaluation metrics for LangGraph Orchestration layer."""
    model_config = ConfigDict(from_attributes=True)

    node_execution_time_ms: Dict[str, float] = Field(default_factory=dict, description="Latency breakdown by node name")
    node_success_rate: float = Field(default=1.0, description="Fraction of nodes completing without unhandled errors")
    conditional_routing_accuracy: float = Field(default=1.0, description="Accuracy of state machine conditional transitions")
    workflow_success_rate: float = Field(default=1.0, description="Overall workflow completion success rate")
    state_transition_count: int = Field(default=0, description="Total number of node transitions in the workflow trajectory")
    workflow_latency_ms: float = Field(default=0.0, description="End-to-end LangGraph graph traversal time")
    branch_distribution: Dict[str, int] = Field(default_factory=dict, description="Frequency count of routing branches taken across runs")


class SystemMetrics(BaseModel):
    """Overall holistic metrics for the entire AI system execution."""
    model_config = ConfigDict(from_attributes=True)

    total_latency_ms: float = Field(default=0.0, description="Total end-to-end request latency")
    prompt_tokens: int = Field(default=0, description="Estimated token count of input prompt")
    completion_tokens: int = Field(default=0, description="Estimated token count of LLM completion")
    context_tokens: int = Field(default=0, description="Total tokens across all intelligence contexts")
    memory_tokens: int = Field(default=0, description="Memory context tokens")
    graph_tokens: int = Field(default=0, description="GraphRAG context tokens")
    tool_tokens: int = Field(default=0, description="External tool context tokens")
    rag_tokens: int = Field(default=0, description="Hybrid RAG context tokens")
    llm_cost_estimate_usd: float = Field(default=0.0, description="Estimated USD cost based on token consumption")
    response_time_ms: float = Field(default=0.0, description="Time to generate final output response")
    hallucination_score: float = Field(default=0.0, description="Calculated hallucination probability where 0.0 = no hallucination (100% grounded/faithful) and 1.0 = severe hallucination")
    answer_confidence: float = Field(default=0.0, description="Overall confidence rating of the finalized answer (0.0 to 1.0)")


# =============================================================================
# 2. Monitoring Engine Telemetry Log Event
# =============================================================================

class WorkflowMonitoringEvent(BaseModel):
    """
    (`Monitoring Telemetry Record`)
    Immutable log record generated for each Workflow run.
    """
    model_config = ConfigDict(from_attributes=True)

    workflow_id: str = Field(default="unknown", description="Unique execution instance identifier")
    user_id: str = Field(default="default", description="User ID associated with request")
    conversation_id: str = Field(default="default", description="Conversation session identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Execution completion timestamp")
    executed_nodes: List[str] = Field(default_factory=list, description="Ordered sequence of executed LangGraph nodes")
    node_timing: Dict[str, float] = Field(default_factory=dict, description="Detailed latency per individual node (e.g. isolating cold-boot loading vs query time)")
    module_timing: Dict[str, float] = Field(default_factory=dict, description="Aggregated latency per intelligence module (Memory, RAG, Graph, Tools)")
    errors: List[str] = Field(default_factory=list, description="Any error messages caught during workflow run")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal fallback warnings")
    route: str = Field(default="UNKNOWN", description="Executed state machine routing path")
    total_latency_ms: float = Field(default=0.0, description="Complete workflow latency in milliseconds")
    llm_latency_ms: float = Field(default=0.0, description="Latency spent exclusively inside LLM generation")


# =============================================================================
# 3. Structured Evaluation Reports
# =============================================================================

class WorkflowReport(BaseModel):
    """Structured evaluation report for LangGraph orchestration."""
    model_config = ConfigDict(from_attributes=True)

    workflow_id: str
    route_taken: str
    executed_nodes: List[str]
    status: str
    latency_ms: float
    error_count: int


class RAGReport(BaseModel):
    """Structured evaluation report for Hybrid RAG performance."""
    model_config = ConfigDict(from_attributes=True)

    query: str
    retrieved_chunks_count: int
    precision: float
    recall: float
    mrr: float
    groundedness: float
    faithfulness: float


class MemoryReport(BaseModel):
    """Structured evaluation report for Long-Term Memory."""
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    retrieval_accuracy: float
    memory_tokens: int


class GraphReport(BaseModel):
    """Structured evaluation report for GraphRAG / Neo4j."""
    model_config = ConfigDict(from_attributes=True)

    query: str
    relationship_accuracy: float
    average_degree: float
    graph_tokens: int


class ToolReport(BaseModel):
    """Structured evaluation report for Tool System."""
    model_config = ConfigDict(from_attributes=True)

    tool_name: str
    success_rate: float
    execution_time_ms: float
    cached: bool


class LLMReport(BaseModel):
    """Structured evaluation report for LLM Generation & groundedness."""
    model_config = ConfigDict(from_attributes=True)

    response_time_ms: float
    prompt_tokens: int
    completion_tokens: int
    cost_estimate_usd: float
    hallucination_score: float
    confidence_score: float


class SystemHealthReport(BaseModel):
    """Overall system diagnostic health summary (HEALTHY, WARNING, DEGRADED, CRITICAL)."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Health tier: HEALTHY, WARNING, DEGRADED, or CRITICAL")
    active_modules: List[str]
    error_rate: float
    avg_latency_ms: float


class EvaluationReport(BaseModel):
    """
    (`Complete Multi-Layer Evaluation Report`)
    Consolidates layer metrics and structured summaries into a single immutable document.
    """
    model_config = ConfigDict(from_attributes=True)

    workflow_id: str = Field(..., description="Workflow run ID")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Raw numeric metrics
    rag_metrics: RAGMetrics = Field(default_factory=RAGMetrics)
    graph_metrics: GraphMetrics = Field(default_factory=GraphMetrics)
    memory_metrics: MemoryMetrics = Field(default_factory=MemoryMetrics)
    tool_metrics: ToolMetrics = Field(default_factory=ToolMetrics)
    langgraph_metrics: LangGraphMetrics = Field(default_factory=LangGraphMetrics)
    system_metrics: SystemMetrics = Field(default_factory=SystemMetrics)

    # Structured summaries
    workflow_report: WorkflowReport
    rag_report: RAGReport
    memory_report: MemoryReport
    graph_report: GraphReport
    tool_report: ToolReport
    llm_report: LLMReport
    system_health_report: SystemHealthReport


# =============================================================================
# 4. JSON Dashboard Payload Schema
# =============================================================================

class DashboardResponse(BaseModel):
    """
    (`Dashboard Layer API Response`)
    Returns JSON-only structured summaries ready for frontend visualization.
    """
    model_config = ConfigDict(from_attributes=True)

    system_health: str = Field(..., description="Overall status indicator e.g. 'OPTIMAL' or 'DEGRADED'")
    workflow_latency: str = Field(..., description="Average latency string e.g. '142.5ms'")
    rag_accuracy: str = Field(..., description="Hybrid RAG groundedness/precision e.g. '96.4%'")
    graph_quality: str = Field(..., description="Graph relationship fidelity e.g. '98.2%'")
    memory_usage: str = Field(..., description="Memory retrieval success rate e.g. '94.0%'")
    tool_success_rate: str = Field(..., description="External tool success percentage e.g. '100.0%'")
    hallucination_score: str = Field(..., description="Calculated hallucination probability e.g. '0.02'")
    average_response_time: str = Field(..., description="End-to-end completion time e.g. '185.0ms'")
    total_requests: int = Field(default=0, description="Total workflow runs observed")
    cost_estimate_total: str = Field(default="$0.0000", description="Cumulative USD cost of observed LLM tokens")
