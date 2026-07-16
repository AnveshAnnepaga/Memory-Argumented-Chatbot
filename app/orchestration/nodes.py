# File: app/orchestration/nodes.py
"""
(`Milestone 11 LangGraph Orchestration Nodes`)
Contains every standalone node inside the LangGraph orchestration engine.
Each node adheres strictly to the Single Responsibility Principle, does not directly communicate
with other nodes, and interacts solely through the shared `WorkflowState`.
"""
import json
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
from app.tools.pipeline import tool_pipeline

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


async def tool_execution_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Tool Execution Node for Milestone 13 External Tools`)
    Executes external tool actions (`ToolPipeline`) based on deterministic routing
    and injects structured real-time results into `retrieved_tool_context`.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("tool_execution_node")
    user_query = state.get("user_query", "")
    user_id = state.get("user_id", "default")
    conversation_id = state.get("conversation_id", "default")
    metadata = dict(state.get("metadata") or {})
    errors = list(state.get("errors") or [])

    t0 = time.perf_counter()
    tool_context_str = ""
    tool_tokens = 0

    try:
        _, tool_context_str = await tool_pipeline.process_query(
            user_query=user_query,
            user_id=user_id,
            session_id=conversation_id
        )
        tool_tokens = len(tool_context_str.split()) if tool_context_str else 0
        if tool_tokens > 0:
            logger.info(f"Retrieved {tool_tokens} words/tokens from Tool System in {(time.perf_counter()-t0)*1000:.1f}ms.")
    except Exception as exc:
        logger.warning(f"Tool execution node fallback triggered: {exc}")
        errors.append(f"Tool Execution Error: {exc}")
        tool_context_str = "[Tool System Offline: Execution failed]"

    metadata["tool_tokens"] = tool_tokens
    return {
        "node_path": node_path,
        "retrieved_tool_context": tool_context_str,
        "metadata": metadata,
        "errors": errors
    }

# Backward compatibility alias
tools_placeholder_node = tool_execution_node


async def context_merge_node(state: WorkflowState) -> Dict[str, Any]:
    """
    (`Context Merge Node`)
    Consolidates retrieved RAG chunks, Knowledge Graph relationships, Long-Term
    Memory contexts, and Real-Time External Tool intelligence into `final_context`.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("context_merge_node")

    rag_ctx = state.get("retrieved_rag_context", "").strip()
    graph_ctx = state.get("retrieved_graph_context", "").strip()
    mem_ctx = state.get("retrieved_memory_context", "").strip()
    tool_ctx = state.get("retrieved_tool_context", "").strip()

    merged_sections = []
    if mem_ctx and mem_ctx not in ("[Long-Term Memory Engine Offline: Using default context]", ""):
        merged_sections.append(f"=== LONG-TERM USER & SESSION MEMORY ===\n{mem_ctx}")

    if tool_ctx and tool_ctx not in ("[Tool System Offline: Execution failed]", ""):
        # tool_ctx already contains `=== REAL-TIME EXTERNAL TOOL INTELLIGENCE ===` prefix from ToolPipeline
        merged_sections.append(tool_ctx)

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
        "You are Antigravity, a highly intelligent, empathetic, and capable AI assistant created by Anvesh Mishra. "
        "You provide thoughtful, precise, and helpful answers across coding, architecture, general knowledge, and reasoning tasks. "
        "Talk naturally like ChatGPT or Claude—be concise, direct, and conversational without repeatedly announcing your backend modules or system architecture unless specifically asked. "
        "IMPORTANT: Always output rich, beautifully formatted Markdown (headings, bullet points, code blocks) just like ChatGPT, Claude, and Gemini. NEVER output raw JSON dictionaries or wrap your answers in JSON format unless the user specifically asks for JSON string output."
    )

    if final_context:
        final_prompt = (
            f"Here is relevant context that may help answer the question:\n{final_context}\n\n"
            f"Question: {user_query}"
        )
    else:
        final_prompt = user_query

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
    Submits the assembled messages (`system` + `user`) to Groq LLM (`llm_manager.generate`) and stores `llm_response`.
    Includes robust fallback so orchestration tests never hang or crash during offline testing.
    """
    node_path = list(state.get("node_path") or [])
    node_path.append("llm_generation_node")
    final_prompt = state.get("final_prompt", "")
    prompt_ctx = state.get("prompt_context", {}) if isinstance(state.get("prompt_context"), dict) else {}
    sys_prompt = prompt_ctx.get("system_prompt") or (
        "You are Antigravity, a highly intelligent, empathetic, and capable AI assistant created by Anvesh Mishra. "
        "Talk naturally like ChatGPT or Claude—be direct, engaging, and conversational without announcing internal architecture unless asked. "
        "Always output rich Markdown. NEVER output raw JSON objects unless specifically asked."
    )
    errors = list(state.get("errors") or [])

    t0 = time.perf_counter()
    llm_output = ""

    try:
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": final_prompt}
        ]
        res = await llm_manager.generate(
            messages=messages,
            temperature=0.5,
            max_tokens=1500
        )
        llm_output = res.get("content", "").strip()
        if llm_output.startswith("{") and llm_output.endswith("}"):
            try:
                parsed_out = json.loads(llm_output)
                if isinstance(parsed_out, dict):
                    extracted = parsed_out.get("response") or parsed_out.get("answer") or parsed_out.get("content") or parsed_out.get("text") or parsed_out.get("output")
                    if isinstance(extracted, str) and extracted.strip():
                        llm_output = extracted.strip()
            except Exception:
                pass
        if not llm_output or llm_output.startswith("[Mock Completion"):
            # If mock provider or empty, generate a clean conversational response
            if llm_output.startswith("[Mock Completion"):
                raise ValueError("Groq returned mock completion.")
            raise ValueError("LLM returned empty output string.")
        logger.info(f"Groq LLM generated response ({len(llm_output.split())} words) in {(time.perf_counter()-t0)*1000:.1f}ms.")
    except Exception as exc:
        logger.warning(f"LLM generation node fallback triggered ({exc}). Using intelligent conversational synthesis.")
        errors.append(f"LLM Generation Fallback: {exc}")
        user_query = state.get("user_query", "").strip()
        final_context = state.get("final_context", "").strip()
        
        q_lower = user_query.lower()
        if any(w in q_lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good evening", "howdy"]):
            llm_output = "Hello! I'm here and ready to help. What would you like to explore, build, or discuss today?"
        elif any(w in q_lower for w in ["who are you", "what are you", "tell me about yourself"]):
            llm_output = "I am Antigravity, an advanced AI assistant created by Anvesh Mishra. I'm designed to help you answer questions, analyze data, solve coding tasks, and reason through complex problems. How can I assist you today?"
        elif final_context:
            llm_output = f"Based on the relevant information found:\n\n{final_context}\n\nIf you'd like more specific details or deeper analysis on any part of this topic, feel free to let me know!"
        else:
            llm_output = f"I understand you're asking about '{user_query}'. Could you provide a bit more context or detail on what specific aspects you'd like to dive into so I can give you the best possible answer?"

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
    metadata["retrieved_chunks"] = state.get("retrieved_chunks") or []

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
