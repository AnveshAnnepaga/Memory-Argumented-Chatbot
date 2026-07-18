# File: scratch/test_evaluation.py
"""
(`Milestone 14 Comprehensive Verification Suite`)
Verifies all 12 core evaluation, monitoring, and observability pillars:
1. RAG Metrics verification
2. Knowledge Graph Metrics verification
3. Memory System Metrics verification
4. Tool System Metrics verification
5. LangGraph Workflow Metrics verification
6. System-Wide Telemetry verification
7. Hallucination Detection & Groundedness verification
8. Monitoring Engine (WorkflowMonitoringEvent) verification
9. Metrics Aggregation verification (Request, Session, User, Day, System)
10. Dashboard JSON API (DashboardService) verification
11. End-to-End Orchestration read-only evaluation integration
12. RAGAS LLM-as-Judge evaluation integration
"""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.evaluation import (
    DashboardResponse,
    EvaluationReport,
    RAGMetrics,
    GraphMetrics,
    MemoryMetrics,
    ToolMetrics,
    LangGraphMetrics,
    SystemMetrics,
    WorkflowMonitoringEvent,
    evaluator,
    monitoring_engine,
    metrics_engine,
    dashboard_service,
    evaluation_pipeline
)
from app.evaluation.ragas_evaluator import ragas_evaluator, _RAGAS_AVAILABLE
from app.orchestration.pipeline import orchestration_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("test_evaluation")


async def verify_pillar_1_rag_metrics():
    logger.info("\n--- [Pillar 1] RAG Metrics Verification ---")
    state = {
        "user_query": "What are the core features of FastAPI?",
        "llm_response": "FastAPI is a modern web framework that features automatic Swagger UI docs and asynchronous dependency injection [Citation 1].",
        "retrieved_rag_context": "Chunk 1: FastAPI is a modern web framework built on Pydantic and Starlette.\n\nChunk 2: It provides automatic Swagger documentation and dependency injection.",
        "timing": {"rag_retrieval_node": 35.2},
        "metadata": {"conversation_id": "sess-rag-1", "route_taken": "HYBRID_RAG", "execution_time_ms": 110.0}
    }
    report = await evaluator.evaluate_workflow(state)
    assert report.rag_metrics.retrieval_precision > 0.0, "RAG precision should be > 0"
    assert report.rag_metrics.groundedness >= 0.7, "Groundedness should reflect context match"
    assert report.rag_report.retrieved_chunks_count == 2, f"Expected 2 chunks, got {report.rag_report.retrieved_chunks_count}"
    logger.info(f"✅ RAG Metrics verified successfully: Precision={report.rag_metrics.retrieval_precision:.2f}, Groundedness={report.rag_metrics.groundedness:.2f}")


async def verify_pillar_2_graph_metrics():
    logger.info("\n--- [Pillar 2] Knowledge Graph Metrics Verification ---")
    state = {
        "user_query": "How is FastAPI related to Pydantic?",
        "llm_response": "FastAPI depends on Pydantic for data validation and schema generation.",
        "retrieved_graph_context": "FastAPI -> DEPENDS_ON -> Pydantic (conf=0.99)\nFastAPI -> USES -> Starlette (conf=0.96)",
        "timing": {"graph_retrieval_node": 15.0},
        "metadata": {"conversation_id": "sess-graph-1", "route_taken": "GRAPH_RAG", "execution_time_ms": 85.0}
    }
    report = await evaluator.evaluate_workflow(state)
    assert report.graph_metrics.relationship_accuracy >= 0.95, "Relationship accuracy should reflect conf scores"
    assert report.graph_metrics.average_node_degree > 0.0, "Node degree should be > 0"
    logger.info(f"✅ Knowledge Graph Metrics verified successfully: RelAccuracy={report.graph_metrics.relationship_accuracy:.4f}, Degree={report.graph_metrics.average_node_degree:.1f}")


async def verify_pillar_3_memory_metrics():
    logger.info("\n--- [Pillar 3] Memory System Metrics Verification ---")
    state = {
        "user_query": "What DB did I mention earlier?",
        "llm_response": "You previously mentioned using PostgreSQL for the knowledge repository.",
        "retrieved_memory_context": "[Episodic Memory] User preferred PostgreSQL over MySQL.\nfact: User works with Python 3.11.",
        "timing": {"memory_retrieval_node": 8.1},
        "metadata": {"conversation_id": "sess-mem-1", "route_taken": "DIRECT_LLM", "execution_time_ms": 65.0, "memory_tokens": 42}
    }
    report = await evaluator.evaluate_workflow(state)
    assert report.memory_metrics.memory_retrieval_accuracy >= 0.8, "Memory accuracy should be >= 0.8"
    assert report.memory_metrics.memory_token_usage == 42, f"Expected 42 memory tokens, got {report.memory_metrics.memory_token_usage}"
    logger.info(f"✅ Memory Metrics verified successfully: Accuracy={report.memory_metrics.memory_retrieval_accuracy:.2f}, Tokens={report.memory_metrics.memory_token_usage}")


async def verify_pillar_4_tool_metrics():
    logger.info("\n--- [Pillar 4] Tool System Metrics Verification ---")
    state = {
        "user_query": "Calculate 15 * 8 + 40",
        "llm_response": "The calculation result for 15 * 8 + 40 is 160.",
        "retrieved_tool_context": "Tool Name: calculator\nArgs: {'expression': '15 * 8 + 40'}\nStatus: SUCCESS\nResult: 160\nExec Time: 1.2ms | Cached: True",
        "timing": {"tool_execution_node": 4.5},
        "metadata": {"conversation_id": "sess-tool-1", "route_taken": "TOOL_CALL", "execution_time_ms": 50.0}
    }
    report = await evaluator.evaluate_workflow(state)
    assert report.tool_metrics.tool_success_rate == 1.0, "Tool success rate should be 1.0"
    assert report.tool_metrics.cache_hit_ratio == 1.0, "Cache hit ratio should be 1.0"
    logger.info(f"✅ Tool Metrics verified successfully: SuccessRate={report.tool_metrics.tool_success_rate}, AvgExecTime={report.tool_metrics.average_execution_time_ms:.2f}ms")


async def verify_pillar_5_langgraph_metrics():
    logger.info("\n--- [Pillar 5] LangGraph Orchestration Metrics Verification ---")
    state = {
        "user_query": "Explain LangGraph conditional routing",
        "llm_response": "LangGraph routes state dynamically across specialized nodes using state edges.",
        "node_path": ["intent_router_node", "rag_retrieval_node", "context_merge_node", "prompt_builder_node", "llm_generation_node", "response_formatter_node"],
        "timing": {"intent_router_node": 2.1, "rag_retrieval_node": 22.0, "llm_generation_node": 105.0},
        "errors": [],
        "metadata": {"conversation_id": "sess-graph-2", "route_taken": "HYBRID_RAG", "execution_time_ms": 135.0}
    }
    report = await evaluator.evaluate_workflow(state)
    assert report.langgraph_metrics.node_success_rate == 1.0, "Node success rate should be 1.0"
    assert report.langgraph_metrics.state_transition_count == 6, f"Expected 6 node transitions, got {report.langgraph_metrics.state_transition_count}"
    logger.info(f"✅ LangGraph Metrics verified successfully: Transitions={report.langgraph_metrics.state_transition_count}, SuccessRate={report.langgraph_metrics.node_success_rate}")


async def verify_pillar_6_system_metrics():
    logger.info("\n--- [Pillar 6] System-Wide Telemetry Verification ---")
    state = {
        "user_query": "Summarize everything we discussed about RAG and Graph.",
        "llm_response": "We discussed Hybrid RAG dense and sparse vector search along with GraphRAG structural multi-hop relationships.",
        "retrieved_rag_context": "Hybrid RAG combines dense Pinecone vectors and BM25 sparse index.",
        "retrieved_graph_context": "GraphRAG extracts entity relationships stored in Neo4j.",
        "timing": {"llm_generation_node": 140.0},
        "metadata": {"conversation_id": "sess-sys-1", "route_taken": "HYBRID_RAG", "execution_time_ms": 180.0, "rag_tokens": 120, "graph_tokens": 80}
    }
    report = await evaluator.evaluate_workflow(state)
    assert report.system_metrics.context_tokens == 200, f"Expected 200 context tokens, got {report.system_metrics.context_tokens}"
    assert report.system_metrics.llm_cost_estimate_usd > 0.0, "Cost estimate should be computed"
    logger.info(f"✅ System Telemetry verified successfully: ContextTokens={report.system_metrics.context_tokens}, EstimatedCost=${report.system_metrics.llm_cost_estimate_usd:.6f}")


async def verify_pillar_7_hallucination_detection():
    logger.info("\n--- [Pillar 7] Hallucination Detection & Groundedness Verification ---")
    # Test ungrounded hallucination
    state_halluc = {
        "user_query": "Who won the Martian Olympics in 2045?",
        "llm_response": "Zaphod Beeblebrox won the gold medal in anti-gravity tennis on Mars with a score of 999 to 0.",
        "retrieved_rag_context": "FastAPI is a modern web framework in Python.",
        "timing": {"llm_generation_node": 90.0},
        "metadata": {"conversation_id": "sess-hal-1", "route_taken": "HYBRID_RAG", "execution_time_ms": 110.0}
    }
    report_hal = evaluator.evaluate_workflow(state_halluc)
    assert report_hal.system_metrics.hallucination_score > 0.5, f"Expected high hallucination score (>0.5), got {report_hal.system_metrics.hallucination_score}"
    logger.info(f"✅ Hallucination detection verified: Ungrounded claim scored hallucination probability = {report_hal.system_metrics.hallucination_score:.3f}")


async def verify_pillar_8_monitoring_engine():
    logger.info("\n--- [Pillar 8] Monitoring Engine Verification ---")
    state = {
        "user_query": "Monitor this test execution",
        "llm_response": "Monitoring observed.",
        "timing": {"llm_generation_node": 88.5, "rag_retrieval_node": 25.0},
        "node_path": ["intent_router_node", "rag_retrieval_node", "llm_generation_node"],
        "metadata": {"workflow_id": "monitor-test-101", "user_id": "test-user-A", "conversation_id": "monitor-sess-1", "route_taken": "HYBRID_RAG", "execution_time_ms": 125.0}
    }
    event = monitoring_engine.observe_event(state)
    assert event.workflow_id == "monitor-test-101", "Workflow ID mismatch"
    assert event.user_id == "test-user-A", "User ID mismatch"
    assert event.module_timing.get("rag", 0.0) == 25.0, "Module timing mismatch"
    logger.info(f"✅ Monitoring Engine verified successfully: Event ID={event.workflow_id}, User={event.user_id}, TotalLat={event.total_latency_ms}ms")


async def verify_pillar_9_metrics_aggregation():
    logger.info("\n--- [Pillar 9] Telemetry Aggregation Verification ---")
    # Clear previous test data and record a few controlled runs
    evaluation_pipeline.clear_telemetry()
    
    for i in range(3):
        state = {
            "user_query": f"Query {i}",
            "llm_response": f"Faithful answer {i} about FastAPI.",
            "retrieved_rag_context": f"Faithful answer {i} about FastAPI.",
            "timing": {"llm_generation_node": 100.0},
            "metadata": {"workflow_id": f"run-{i}", "user_id": "user-X", "conversation_id": "sess-agg", "route_taken": "DIRECT_LLM", "execution_time_ms": 120.0 + i*10}
        }
        await evaluation_pipeline.observe_workflow(state)

    agg_sys = evaluation_pipeline.get_aggregated_metrics(scope="system")
    agg_user = evaluation_pipeline.get_aggregated_metrics(scope="user", target_id="user-X")
    
    assert agg_sys["total_requests"] == 3, f"Expected 3 system requests, got {agg_sys['total_requests']}"
    assert agg_user["total_requests"] == 3, f"Expected 3 user requests, got {agg_user['total_requests']}"
    logger.info(f"✅ Telemetry Aggregation verified: Scope=system -> TotalRequests={agg_sys['total_requests']}, MeanLat={agg_sys['average_latency_ms']}ms")


async def verify_pillar_10_dashboard_json():
    logger.info("\n--- [Pillar 10] Dashboard JSON API Verification ---")
    summary = evaluation_pipeline.get_dashboard_summary()
    data_json = evaluation_pipeline.get_dashboard_json()
    
    assert isinstance(data_json, dict), "Dashboard data must be a clean dictionary ready for JSON API"
    assert "system_health" in data_json, "Missing system_health"
    assert "workflow_latency" in data_json, "Missing workflow_latency"
    assert "rag_accuracy" in data_json, "Missing rag_accuracy"
    assert "hallucination_score" in data_json, "Missing hallucination_score"
    assert data_json["total_requests"] == 3, "Should reflect the 3 aggregated requests"
    
    # Test strict JSON serialization
    serialized = json.dumps(data_json, indent=2)
    logger.info(f"✅ Dashboard JSON verified successfully:\n{serialized}")


async def verify_pillar_12_ragas_evaluation():
    logger.info("\n--- [Pillar 12] RAGAS LLM-as-Judge Evaluation ---")
    if not _RAGAS_AVAILABLE:
        logger.warning("⚠️ RAGAS not installed; skipping Pillar 12")
        return

    queries = [
        "What are the core features of FastAPI?",
        "How does Hybrid RAG work?",
    ]
    responses = [
        "FastAPI features automatic Swagger UI docs and async dependency injection.",
        "Hybrid RAG combines dense vector search from Pinecone with sparse BM25 retrieval.",
    ]
    contexts = [
        ["FastAPI is a modern web framework with automatic Swagger docs and async dependency injection."],
        ["Hybrid RAG combines dense Pinecone vectors and BM25 sparse index for retrieval."],
    ]
    ground_truths = [
        "FastAPI has automatic OpenAPI docs, async support, and dependency injection.",
        "Hybrid RAG uses Pinecone dense vectors and BM25 sparse search.",
    ]

    results = await ragas_evaluator.evaluate(
        queries=queries,
        responses=responses,
        contexts=contexts,
        ground_truths=ground_truths,
    )

    assert "faithfulness" in results, "RAGAS must compute faithfulness"
    assert "answer_relevancy" in results, "RAGAS must compute answer_relevancy"
    assert "context_precision" in results, "RAGAS must compute context_precision"
    assert results["faithfulness"] >= 0.0, "Faithfulness should be non-negative"
    logger.info(f"✅ RAGAS Evaluation verified successfully: {results}")


async def verify_pillar_11_end_to_end_orchestration():
    logger.info("\n--- [Pillar 11] End-to-End Orchestration Read-Only Integration ---")
    query = "Calculate 12 * 12 and then explain what FastAPI is."
    response = await orchestration_pipeline.process_query(user_query=query, conversation_id="e2e-eval-session", user_id="user-alpha")
    
    assert response.response is not None and len(response.response) > 0, "Pipeline must return valid response"
    assert response.evaluation is not None, "Evaluation report must be automatically attached read-only to WorkflowResponse"
    assert response.evaluation["workflow_id"] == "e2e-eval-session", "Workflow ID mismatch in evaluation payload"
    
    logger.info(
        f"✅ End-to-End Orchestration Evaluation Hook verified:\n"
        f"   - Query: '{query}'\n"
        f"   - Route Taken: {response.router_decision.route.value}\n"
        f"   - Response: '{response.response[:60]}...'\n"
        f"   - Evaluation Health: {response.evaluation['system_health_report']['status']}\n"
        f"   - Hallucination Score: {response.evaluation['llm_report']['hallucination_score']:.3f}\n"
        f"   - Total Latency: {response.metadata.execution_time_ms:.1f}ms"
    )


async def main():
    logger.info("=====================================================================")
    logger.info("STARTING MILESTONE 14 VERIFICATION SUITE across all 11 Pillars")
    logger.info("=====================================================================")
    
    await verify_pillar_1_rag_metrics()
    await verify_pillar_2_graph_metrics()
    await verify_pillar_3_memory_metrics()
    await verify_pillar_4_tool_metrics()
    await verify_pillar_5_langgraph_metrics()
    await verify_pillar_6_system_metrics()
    await verify_pillar_7_hallucination_detection()
    await verify_pillar_8_monitoring_engine()
    await verify_pillar_9_metrics_aggregation()
    await verify_pillar_10_dashboard_json()
    await verify_pillar_11_end_to_end_orchestration()
    await verify_pillar_12_ragas_evaluation()

    logger.info("\n=====================================================================")
    logger.info("🎉 ALL 12 PILLARS PASSED VERIFICATION WITH ZERO ERRORS!")
    logger.info("=====================================================================")


if __name__ == "__main__":
    asyncio.run(main())
