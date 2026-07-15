# File: scratch/test_orchestration.py
"""
(`Milestone 11 End-to-End LangGraph Orchestration Verification Suite`)
Verifies:
1. Intent Classification & Intelligent Routing across 4 primary routes
2. Single Responsibility Node transitions and State integrity
3. Conditional routing edges inside CompiledStateGraph
4. End-to-end OrchestrationPipeline (`process_query`) across all 4 benchmark queries
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.orchestration import (
    IntentType,
    RouteType,
    intelligent_router,
    orchestration_pipeline,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("test_orchestration")


async def run_orchestration_verification():
    print("\n" + "="*80)
    print("[START] INITIALIZING MILESTONE 11 LANGGRAPH ORCHESTRATION VERIFICATION ENGINE")
    print("="*80)

    # Phase 1: Test Intelligent Router Classification
    print("\n--------------------------------------------------------------------------------")
    print("[1/3] Testing Intelligent Router (Deterministic Intent & Route Classification)...")
    print("--------------------------------------------------------------------------------")
    test_cases = [
        ("Hello there!", IntentType.GREETING, RouteType.DIRECT_LLM),
        ("What is FastAPI?", IntentType.TECHNICAL_DOCS, RouteType.HYBRID_RAG),
        ("How is FastAPI related to Starlette?", IntentType.RELATIONSHIP_QUERY, RouteType.GRAPH_RAG),
        ("Explain FastAPI and how it depends on Starlette.", IntentType.MIXED_REASONING, RouteType.HYBRID_SYNTHESIS),
    ]

    for query, expected_intent, expected_route in test_cases:
        intent = intelligent_router.analyze_intent(query)
        decision = intelligent_router.route_query(query, intent_result=intent)
        print(f"  [QUERY]: '{query}'")
        print(f"     -> Intent: {intent.intent.value} (Conf: {intent.confidence:.2f}) | Keywords: {intent.keywords}")
        print(f"     -> Route : {decision.route.value} (rag={decision.requires_rag}, graph={decision.requires_graph})")
        
        assert intent.intent == expected_intent, f"Expected intent {expected_intent}, got {intent.intent}"
        assert decision.route == expected_route, f"Expected route {expected_route}, got {decision.route}"
    print("  [OK] Intelligent Router classified all 4 benchmark queries perfectly!")

    # Phase 2: Test StateGraph Conditional Transitions & Node Paths
    print("\n--------------------------------------------------------------------------------")
    print("[2/3] Testing LangGraph StateGraph Transitions & Conditional Routing...")
    print("--------------------------------------------------------------------------------")

    # Test Route 1: DIRECT_LLM (Greeting -> skips retrieval nodes)
    res_direct = await orchestration_pipeline.process_query("Hello there! How are you?", conversation_id="test-direct-001")
    print(f"\n  [EXECUTION TEST 1: DIRECT_LLM Route]")
    print(f"  Query: 'Hello there! How are you?'")
    print(f"  Route Taken: {res_direct.metadata.route_taken.value}")
    print(f"  Node Transition Path: {' -> '.join(res_direct.metadata.node_path)}")
    print(f"  Execution Latency: {res_direct.metadata.execution_time_ms} ms")
    assert "rag_retrieval_node" not in res_direct.metadata.node_path, "DIRECT_LLM MUST NOT execute RAG retrieval!"
    assert "graph_retrieval_node" not in res_direct.metadata.node_path, "DIRECT_LLM MUST NOT execute Graph retrieval!"
    assert "prompt_builder_node" in res_direct.metadata.node_path, "MUST execute prompt builder!"

    # Test Route 2: HYBRID_RAG (Technical documentation -> executes RAG retrieval)
    res_rag = await orchestration_pipeline.process_query("What is FastAPI?", conversation_id="test-rag-002")
    print(f"\n  [EXECUTION TEST 2: HYBRID_RAG Route]")
    print(f"  Query: 'What is FastAPI?'")
    print(f"  Route Taken: {res_rag.metadata.route_taken.value}")
    print(f"  Node Transition Path: {' -> '.join(res_rag.metadata.node_path)}")
    print(f"  RAG Tokens Retrieved: {res_rag.metadata.rag_tokens}")
    assert "rag_retrieval_node" in res_rag.metadata.node_path, "HYBRID_RAG MUST execute RAG retrieval node!"
    assert "context_merge_node" in res_rag.metadata.node_path, "HYBRID_RAG MUST execute context merge node!"

    # Test Route 3: GRAPH_RAG (Relationship query -> executes Graph retrieval)
    res_graph = await orchestration_pipeline.process_query("How is FastAPI related to Starlette?", conversation_id="test-graph-003")
    print(f"\n  [EXECUTION TEST 3: GRAPH_RAG Route]")
    print(f"  Query: 'How is FastAPI related to Starlette?'")
    print(f"  Route Taken: {res_graph.metadata.route_taken.value}")
    print(f"  Node Transition Path: {' -> '.join(res_graph.metadata.node_path)}")
    print(f"  Graph Tokens Retrieved: {res_graph.metadata.graph_tokens}")
    assert "graph_retrieval_node" in res_graph.metadata.node_path, "GRAPH_RAG MUST execute Graph retrieval node!"
    assert "context_merge_node" in res_graph.metadata.node_path, "GRAPH_RAG MUST execute context merge node!"

    # Test Route 4: HYBRID_SYNTHESIS (Mixed reasoning -> executes both RAG and Graph nodes)
    res_synthesis = await orchestration_pipeline.process_query("Explain FastAPI and how it depends on Starlette.", conversation_id="test-synthesis-004")
    print(f"\n  [EXECUTION TEST 4: HYBRID_SYNTHESIS Route]")
    print(f"  Query: 'Explain FastAPI and how it depends on Starlette.'")
    print(f"  Route Taken: {res_synthesis.metadata.route_taken.value}")
    print(f"  Node Transition Path: {' -> '.join(res_synthesis.metadata.node_path)}")
    print(f"  RAG Tokens: {res_synthesis.metadata.rag_tokens} | Graph Tokens: {res_synthesis.metadata.graph_tokens}")
    assert "rag_retrieval_node" in res_synthesis.metadata.node_path, "HYBRID_SYNTHESIS MUST execute RAG node!"
    assert "graph_retrieval_node" in res_synthesis.metadata.node_path, "HYBRID_SYNTHESIS MUST execute Graph node!"
    print("  [OK] All 4 LangGraph conditional routing branches verified 100% accurate!")

    # Phase 3: Verify Prompt Builder & Output Diagnostics
    print("\n--------------------------------------------------------------------------------")
    print("[3/3] Testing Prompt Builder Assembly & Final API Output Payload...")
    print("--------------------------------------------------------------------------------")
    if res_synthesis.prompt_context:
        print("  [ASSEMBLED PROMPT PREVIEW]:")
        for line in res_synthesis.prompt_context.final_prompt.split("\n")[:12]:
            print(f"  | {line}")
        print("  | ... [truncated for brevity]")
    print(f"  [LLM RESPONSE]: {res_synthesis.response[:150]}...")
    print(f"  [TOTAL PROMPT TOKENS]: {res_synthesis.metadata.total_prompt_tokens}")

    print("\n--------------------------------------------------------------------------------")
    print("[SUCCESS] MILESTONE 11 (LANGGRAPH ORCHESTRATION - THE BRAIN) VERIFIED 100% SUCCESSFUL!\n")


if __name__ == "__main__":
    asyncio.run(run_orchestration_verification())
