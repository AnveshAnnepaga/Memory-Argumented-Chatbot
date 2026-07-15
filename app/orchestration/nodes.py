# File: app/orchestration/nodes.py
"""
(`Milestone 11 LangGraph Orchestration Nodes`)
Contains every standalone node inside the LangGraph orchestration engine.
Each node adheres strictly to the Single Responsibility Principle, does not directly communicate
with other nodes, and interacts solely through the shared `WorkflowState`.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from app.ai.llm.llm_manager import llm_manager
from app.graph.pipeline import graph_pipeline
from app.memory.pipeline import memory_pipeline
from app.orchestration.router import intelligent_router
from app.orchestration.schemas import (
    IntentResult,
    PromptContext,
    RouterDecision,
    RouteType,
)
from app.orchestration.state import WorkflowState
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger("app.orchestration.nodes")


async def start_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Start Node`)
    Initializes timing markers and records entry into the LangGraph workflow.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("start_node")
    timing = dict(state.get("timing") or {})
    if "start_time" not in timing:
        timing["start_time"] = time.perf_counter()

    logger.debug(f"Workflow execution started for query: '{state.get('user_query', '')[:50]}...'")
    return {
        "node_path": node_path,
        "timing": timing
    }


async def intent_analysis_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Intent Analysis Node`)
    Analyzes user query semantics and identifies high-level intent (`IntentResult`).
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("intent_analysis_node")
    user_query = state.get("user_query", "")

    intent_res = intelligent_router.analyze_intent(user_query)
    logger.info(f"Analyzed intent: {intent_res.intent.value} (conf={intent_res.confidence:.2f}, keywords={intent_res.keywords})")

    return {
        "node_path": node_path,
        "intent": intent_res.model_dump()
    }


async def router_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Router Node`)
    Invokes the Intelligent Router to determine the execution path (`RouterDecision`).
    Does not call the LLM; decides execution branches based on classification.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("router_node")
    user_query = state.get("user_query", "")
    intent_data = state.get("intent")
    
    intent_res = IntentResult(**intent_data) if intent_data else None
    decision = intelligent_router.route_query(user_query, intent_result=intent_res)

    metadata = dict(state.get("metadata") or {})
    metadata["route_taken"] = decision.route.value

    logger.info(f"Router decision: {decision.route.value} (rag={decision.requires_rag}, graph={decision.requires_graph})")
    return {
        "node_path": node_path,
        "router_decision": decision.model_dump(),
        "metadata": metadata
    }


async def rag_retrieval_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`RAG Retrieval Node`)
    Queries the Hybrid RAG engine (Dense + Sparse + RRF + Cross-Encoder Reranker)
    and stores retrieved documentation chunks into state.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("rag_retrieval_node")
    user_query = state.get("user_query", "")
    metadata = dict(state.get("metadata") or {})
    errors = list(state.get("errors") or [])

    t0 = time.perf_counter()
    rag_context_str = ""
    rag_tokens = 0

    try:
        # Execute production Hybrid RAG query (`retrieve_context`)
        rag_ctx = await rag_pipeline.retrieve_context(user_query, top_k=3)
        rag_context_str = getattr(rag_ctx, "formatted_context", str(rag_ctx))
        rag_tokens = getattr(rag_ctx, "total_tokens", len(rag_context_str.split()))

        logger.info(f"Retrieved {rag_tokens} words/tokens from Hybrid RAG engine in {(time.perf_counter()-t0)*1000:.1f}ms.")
    except Exception as exc:
        logger.warning(f"RAG retrieval node fallback triggered: {exc}")
        errors.append(f"RAG Retrieval Error: {exc}")
        rag_context_str = "[RAG Engine Offline: No chunks retrieved]"

    metadata["rag_tokens"] = rag_tokens
    return {
        "node_path": node_path,
        "retrieved_rag_context": rag_context_str,
        "metadata": metadata,
        "errors": errors
    }


async def graph_retrieval_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Graph Retrieval Node`)
    Queries the Knowledge Graph engine (GraphRAG / Neo4j) to extract structural multi-hop
    relationships, dependencies, and explainability provenance into state.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("graph_retrieval_node")
    user_query = state.get("user_query", "")
    metadata = dict(state.get("metadata") or {})
    errors = list(state.get("errors") or [])

    t0 = time.perf_counter()
    graph_context_str = ""
    graph_tokens = 0

    try:
        # Execute GraphRAG query
        graph_ctx = await graph_pipeline.query_graph(user_query)
        graph_context_str = graph_ctx.formatted_context
        graph_tokens = graph_ctx.total_tokens
        logger.info(f"Retrieved {graph_tokens} words/tokens from GraphRAG engine in {(time.perf_counter()-t0)*1000:.1f}ms.")
    except Exception as exc:
        logger.warning(f"Graph retrieval node fallback triggered: {exc}")
        errors.append(f"Graph Retrieval Error: {exc}")
        graph_context_str = "[GraphRAG Engine Offline: No structural relationships found]"

    metadata["graph_tokens"] = graph_tokens
    return {
        "node_path": node_path,
        "retrieved_graph_context": graph_context_str,
        "metadata": metadata,
        "errors": errors
    }


async def memory_retrieval_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Memory Retrieval Node for Milestone 12 Long-Term Memory`)
    Retrieves User Profile, Enduring Semantic Facts, Episodes, and Conversation Window from `MemoryPipeline`.
    Injected into `retrieved_memory_context` for LangGraph orchestration.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("memory_retrieval_node")
    user_query = state.get("user_query", "")
    user_id = state.get("user_id", "default-user")
    conversation_id = state.get("conversation_id", "default-session")
    metadata = dict(state.get("metadata") or {})
    errors = list(state.get("errors") or [])

    t0 = time.perf_counter()
    memory_context_str = ""
    memory_tokens = 0

    try:
        # First process any incoming turn facts/profile updates via extractor/manager
        await memory_pipeline.process_turn(user_query=user_query, ai_response=None, user_id=user_id, conversation_id=conversation_id)

        # Retrieve full ranking memory context
        mem_ctx = await memory_pipeline.retrieve_context(user_id=user_id, query=user_query, conversation_id=conversation_id)
        memory_context_str = mem_ctx.formatted_context
        memory_tokens = mem_ctx.total_tokens
        logger.info(f"Retrieved {memory_tokens} words/tokens from Long-Term Memory engine in {(time.perf_counter()-t0)*1000:.1f}ms.")
    except Exception as exc:
        logger.warning(f"Memory retrieval node fallback triggered: {exc}")
        errors.append(f"Memory Retrieval Error: {exc}")
        memory_context_str = "[Long-Term Memory Engine Offline: Using default context]"

    metadata["memory_tokens"] = memory_tokens
    return {
        "node_path": node_path,
        "retrieved_memory_context": memory_context_str,
        "metadata": metadata,
        "errors": errors
    }

# Backward compatibility alias for workflow imports
memory_placeholder_node = memory_retrieval_node


async def tools_placeholder_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Placeholder for Milestone 13 External Tools`)
    Invokes external tool APIs or function calling blocks when requested.
    Currently acts as a pass-through node.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("tools_placeholder_node")
    logger.debug("Executing tools placeholder node (Milestone 13 pass-through).")
    return {"node_path": node_path}


async def context_merge_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Context Merge Node`)
    Consolidates retrieved RAG chunks, Knowledge Graph relationships, and Long-Term
    Memory contexts into a single unified `final_context` block.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("context_merge_node")

    rag_ctx = state.get("retrieved_rag_context", "").strip()
    graph_ctx = state.get("retrieved_graph_context", "").strip()
    mem_ctx = state.get("retrieved_memory_context", "").strip()

    merged_sections = []
    if mem_ctx and mem_ctx not in ("[Long-Term Memory Engine Offline: Using default context]", ""):
        merged_sections.append(f"=== LONG-TERM USER & SESSION MEMORY ===\n{mem_ctx}")

    if rag_ctx and rag_ctx not in ("[RAG Engine Offline: No chunks retrieved]", ""):
        merged_sections.append(f"=== RETRIEVED DOCUMENTATION (HYBRID RAG) ===\n{rag_ctx}")
    
    if graph_ctx and graph_ctx not in ("[GraphRAG Engine Offline: No structural relationships found]", ""):
        merged_sections.append(f"=== STRUCTURAL KNOWLEDGE GRAPH (GRAPHRAG) ===\n{graph_ctx}")

    final_ctx = "\n\n".join(merged_sections).strip() if merged_sections else ""
    logger.debug(f"Merged {len(merged_sections)} context sections into final_context ({len(final_ctx.split())} words).")

    return {
        "node_path": node_path,
        "final_context": final_ctx
    }


async def prompt_builder_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Prompt Builder Node`)
    Constructs the exact consolidated prompt (`final_prompt`) and `PromptContext` payload.
    No other node in the workflow is permitted to construct or modify prompts.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("prompt_builder_node")

    user_query = state.get("user_query", "")
    final_context = state.get("final_context", "")
    metadata = dict(state.get("metadata") or {})

    system_prompt = (
        "You are Antigravity, an advanced Agentic AI system powered by LangGraph Orchestration, "
        "Long-Term Memory System, Hybrid RAG, and Neo4j GraphRAG. Provide accurate, clear, and structured answers based "
        "on the retrieved context provided below. If no context is needed or provided, answer directly."
    )

    if final_context:
        final_prompt = (
            f"{system_prompt}\n\n"
            f"--- CONTEXT ---\n{final_context}\n\n"
            f"--- USER QUESTION ---\n{user_query}\n\n"
            f"Answer:"
        )
    else:
        final_prompt = (
            f"{system_prompt}\n\n"
            f"--- USER QUESTION ---\n{user_query}\n\n"
            f"Answer:"
        )

    prompt_tokens = len(final_prompt.split())
    metadata["total_prompt_tokens"] = prompt_tokens

    prompt_ctx = PromptContext(
        user_query=user_query,
        system_prompt=system_prompt,
        rag_context=state.get("retrieved_rag_context", ""),
        graph_context=state.get("retrieved_graph_context", ""),
        final_prompt=final_prompt
    )

    logger.debug(f"Assembled final_prompt ({prompt_tokens} words/tokens).")
    return {
        "node_path": node_path,
        "final_prompt": final_prompt,
        "prompt_context": prompt_ctx.model_dump(),
        "metadata": metadata
    }


async def llm_generation_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`LLM Generation Node`)
    Submits the assembled `final_prompt` to Groq LLM (`llm_manager.generate`) and stores `llm_response`.
    Includes robust fallback so orchestration tests never hang or crash during offline testing.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("llm_generation_node")
    final_prompt = state.get("final_prompt", "")
    errors = list(state.get("errors") or [])

    t0 = time.perf_counter()
    llm_output = ""

    try:
        res = await llm_manager.generate(
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0.3,
            max_tokens=800
        )
        llm_output = res.get("content", "").strip()
        if not llm_output:
            raise ValueError("LLM returned empty output string.")
        logger.info(f"Groq LLM generated response ({len(llm_output.split())} words) in {(time.perf_counter()-t0)*1000:.1f}ms.")
    except Exception as exc:
        logger.warning(f"LLM generation node fallback triggered ({exc}). Using deterministic response synthesis.")
        errors.append(f"LLM Generation Fallback: {exc}")
        # Build intelligent fallback response from final_context if LLM API is offline
        user_query = state.get("user_query", "")
        final_context = state.get("final_context", "")
        if final_context:
            llm_output = f"Synthesized Answer for '{user_query}':\nBased on retrieved knowledge:\n{final_context[:1000]}..."
        else:
            llm_output = f"Hello! I am ready to process your query: '{user_query}'."

    return {
        "node_path": node_path,
        "llm_response": llm_output,
        "errors": errors
    }


async def response_formatter_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Response Formatter Node`)
    Finalizes execution diagnostics, calculates total latency (`execution_time_ms`),
    and formats the state payload for API presentation.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("response_formatter_node")
    timing = dict(state.get("timing") or {})
    metadata = dict(state.get("metadata") or {})
    errors = list(state.get("errors") or [])

    start_time = timing.get("start_time", time.perf_counter())
    total_ms = (time.perf_counter() - start_time) * 1000.0

    metadata["execution_time_ms"] = round(total_ms, 2)
    metadata["node_path"] = node_path
    metadata["errors"] = errors

    logger.info(f"Response formatter completed workflow in {total_ms:.1f}ms across {len(node_path)} nodes: {' -> '.join(node_path)}")
    return {
        "node_path": node_path,
        "metadata": metadata
    }


async def end_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`End Node`)
    Marks completion of the StateGraph execution.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("end_node")
    logger.debug("LangGraph workflow reached end_node successfully.")
    return {"node_path": node_path}
