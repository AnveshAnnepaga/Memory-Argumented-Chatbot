# File: app/orchestration/state.py
"""
(`Milestone 11 LangGraph Orchestration State`)
Contains the complete LangGraph State (`WorkflowState`) shared across all nodes.
Nodes never communicate directly with each other; they only read from and update this serializable state dictionary.
"""
import time
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from app.orchestration.schemas import (
    IntentResult,
    PromptContext,
    RouterDecision,
    RouteType,
    WorkflowMetadata,
)


class WorkflowState(TypedDict, total=False):
    """
    The central, serializable LangGraph state dictionary.
    Every node receives this dictionary, performs its single responsibility, and returns fields to update.
    """
    # Core User & Session Identifiers
    user_query: str
    conversation_id: str
    user_id: str

    # Classification & Decision Tracking
    intent: Optional[Dict[str, Any]]
    router_decision: Optional[Dict[str, Any]]

    # Retrieval Context Payloads
    file_context: str
    retrieved_rag_context: str
    retrieved_graph_context: str
    retrieved_memory_context: str
    retrieved_tool_context: str
    final_context: str

    # Prompt & LLM Generation Payloads
    final_prompt: str
    prompt_context: Optional[Dict[str, Any]]
    llm_response: str

    # Diagnostics & Timing
    metadata: Dict[str, Any]
    timing: Dict[str, float]
    errors: List[str]
    node_path: List[str]


def create_initial_state(
    user_query: str,
    conversation_id: str = "default",
    user_id: str = "default",
    file_context: str = ""
) -> WorkflowState:
    """
    Factory helper to initialize a clean, serializable LangGraph workflow state dictionary.
    """
    start_time = time.perf_counter()
    return {
        "user_query": user_query.strip(),
        "conversation_id": conversation_id,
        "user_id": user_id,
        "intent": None,
        "router_decision": None,
        "file_context": file_context,
        "retrieved_rag_context": "",
        "retrieved_graph_context": "",
        "retrieved_memory_context": "",
        "retrieved_tool_context": "",
        "final_context": "",
        "final_prompt": "",
        "prompt_context": None,
        "llm_response": "",
        "metadata": {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "route_taken": RouteType.UNKNOWN.value,
            "rag_tokens": 0,
            "graph_tokens": 0,
            "memory_tokens": 0,
            "tool_tokens": 0,
            "total_prompt_tokens": 0,
            "execution_time_ms": 0.0,
            "node_path": [],
            "errors": []
        },
        "timing": {"start_time": start_time},
        "errors": [],
        "node_path": []
    }
