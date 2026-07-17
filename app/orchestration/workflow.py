# File: app/orchestration/workflow.py
"""
(`Milestone 11 LangGraph Orchestration StateGraph`)
Constructs and compiles the complete StateGraph (`OrchestrationWorkflow`), wiring all
single-responsibility nodes and implementing conditional routing branches.
"""
import logging
from typing import Dict

from langgraph.graph import END, START, StateGraph

from app.orchestration.nodes import (
    context_merge_node,
    end_node,
    graph_retrieval_node,
    intent_analysis_node,
    llm_generation_node,
    memory_placeholder_node,
    prompt_builder_node,
    rag_retrieval_node,
    response_formatter_node,
    router_node,
    start_node,
    tools_placeholder_node,
)
from app.orchestration.schemas import RouteType
from app.orchestration.state import WorkflowState

logger = logging.getLogger("app.orchestration.workflow")


def route_decision(state: WorkflowState) -> str:
    """
    (`Conditional Routing Function from Router Node / Tool Execution Node`)
    Inspects `router_decision` along with memory/tool results in state and directs execution.
    - MEMORY_ENHANCED / DIRECT_LLM / TOOLS_ENHANCED -> prompt_builder if no RAG/Graph required,
      else context_merge first (to honor all retrievals).
    - GRAPH_RAG -> graph_retrieval
    - HYBRID_RAG / HYBRID_SYNTHESIS -> rag_retrieval
    """
    decision = state.get("router_decision")
    route_str = decision.get("route", RouteType.DIRECT_LLM.value) if decision else RouteType.DIRECT_LLM.value

    if route_str in (RouteType.DIRECT_LLM.value, RouteType.MEMORY_ENHANCED.value,
                     RouteType.TOOLS_ENHANCED.value):
        mem_ctx = state.get("retrieved_memory_context", "").strip()
        tool_ctx = state.get("retrieved_tool_context", "").strip()
        rag_ctx = state.get("retrieved_rag_context", "").strip()
        graph_ctx = state.get("retrieved_graph_context", "").strip()

        has_mem = mem_ctx and mem_ctx not in ("[Long-Term Memory Engine Offline: Using default context]", "")
        has_tool = tool_ctx and tool_ctx not in ("[Tool System Offline: Execution failed]", "")
        # ALSO pull richer context if mixed reasoning upgraded routes
        decision_outer = state.get("router_decision", {}) or {}
        if decision_outer.get("requires_rag") or decision_outer.get("requires_graph"):
            return "rag_retrieval"

        if has_mem or has_tool:
            return "context_merge"
        return "prompt_builder"
    elif route_str == RouteType.GRAPH_RAG.value:
        return "graph_retrieval"
    elif route_str in (RouteType.HYBRID_RAG.value, RouteType.HYBRID_SYNTHESIS.value):
        return "rag_retrieval"

    return "prompt_builder"


def rag_post_route(state: WorkflowState) -> str:
    """
    (`Conditional Routing Function after RAG Retrieval`)
    Determines whether to proceed to Knowledge Graph retrieval (for HYBRID_SYNTHESIS)
    or directly to context merge (for standard HYBRID_RAG).
    """
    decision = state.get("router_decision")
    route_str = decision.get("route", RouteType.HYBRID_RAG.value) if decision else RouteType.HYBRID_RAG.value

    if route_str == RouteType.HYBRID_SYNTHESIS.value:
        return "graph_retrieval"
    return "context_merge"


class OrchestrationWorkflow:
    """
    (`4️⃣ workflow.py`)
    Encapsulates the compiled LangGraph StateGraph engine for all AI reasoning.
    """
    def __init__(self):
        self.workflow = StateGraph(WorkflowState)
        self._build_graph()
        self.app = self.workflow.compile()
        logger.info("Compiled LangGraph Orchestration StateGraph successfully.")

    def _build_graph(self) -> None:
        """Adds all nodes and defines unconditional/conditional routing transitions."""
        # 1. Add every standalone node
        self.workflow.add_node("start", start_node)
        self.workflow.add_node("intent_analysis", intent_analysis_node)
        self.workflow.add_node("router", router_node)
        self.workflow.add_node("rag_retrieval", rag_retrieval_node)
        self.workflow.add_node("graph_retrieval", graph_retrieval_node)
        self.workflow.add_node("memory_placeholder", memory_placeholder_node)
        self.workflow.add_node("tools_placeholder", tools_placeholder_node)
        self.workflow.add_node("context_merge", context_merge_node)
        self.workflow.add_node("prompt_builder", prompt_builder_node)
        self.workflow.add_node("llm_generation", llm_generation_node)
        self.workflow.add_node("response_formatter", response_formatter_node)
        self.workflow.add_node("end", end_node)

        # 2. Connect initial execution flow: start -> intent -> router -> memory -> tools
        self.workflow.add_edge(START, "start")
        self.workflow.add_edge("start", "intent_analysis")
        self.workflow.add_edge("intent_analysis", "router")
        self.workflow.add_edge("router", "memory_placeholder")
        self.workflow.add_edge("memory_placeholder", "tools_placeholder")

        # 3. Add conditional routing after tool execution node
        self.workflow.add_conditional_edges(
            "tools_placeholder",
            route_decision,
            {
                "prompt_builder": "prompt_builder",
                "context_merge": "context_merge",
                "rag_retrieval": "rag_retrieval",
                "graph_retrieval": "graph_retrieval"
            }
        )

        # 4. Add conditional routing from rag_retrieval (to support Hybrid Synthesis)
        self.workflow.add_conditional_edges(
            "rag_retrieval",
            rag_post_route,
            {
                "graph_retrieval": "graph_retrieval",
                "context_merge": "context_merge"
            }
        )

        # 5. Connect downstream context merge, prompt building, LLM generation, and formatting
        self.workflow.add_edge("graph_retrieval", "context_merge")
        self.workflow.add_edge("context_merge", "prompt_builder")
        self.workflow.add_edge("prompt_builder", "llm_generation")
        self.workflow.add_edge("llm_generation", "response_formatter")
        self.workflow.add_edge("response_formatter", "end")
        self.workflow.add_edge("end", END)


# Singleton instance of the compiled workflow graph
orchestration_workflow = OrchestrationWorkflow()
