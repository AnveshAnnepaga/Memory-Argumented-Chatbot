# File: app/evaluation/evaluator.py
"""
(`Milestone 14 Read-Only Evaluation Engine`)
Evaluates the complete multi-layer AI workflow without modifying state or application logic.
Computes groundedness, faithfulness, hallucination detection, latency breakdowns, and
structured diagnostic reports (`EvaluationReport`).
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.evaluation.metrics import (
    calculate_faithfulness,
    calculate_graph_metrics,
    calculate_groundedness,
    calculate_langgraph_metrics,
    calculate_memory_metrics,
    calculate_rag_metrics,
    calculate_system_metrics,
    calculate_tool_metrics,
)
from app.evaluation.ragas_evaluator import ragas_evaluator, _RAGAS_AVAILABLE
from app.evaluation.schemas import (
    EvaluationReport,
    GraphReport,
    LLMReport,
    MemoryReport,
    RAGReport,
    SystemHealthReport,
    ToolReport,
    WorkflowReport,
)

logger = logging.getLogger("app.evaluation.evaluator")


class EvaluationEngine:
    """
    (`Core Read-Only Evaluation Engine`)
    Observes LangGraph state outputs, measures individual intelligence layers,
    and constructs the unified `EvaluationReport`.
    """
    async def evaluate_workflow(
        self,
        state: Dict[str, Any],
        response_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationReport:
        """
        Performs read-only inspection of the finalized workflow state and returns a complete evaluation report.
        """
        # Read-only extraction of state variables
        user_query = str(state.get("user_query", "")).strip()
        final_response = (response_text or state.get("llm_response", "")).strip()
        if not final_response:
            final_response = "No response generated."

        meta = metadata or state.get("metadata") or {}
        workflow_id = str(meta.get("workflow_id", meta.get("conversation_id", "default-run")))
        route_taken = str(meta.get("route_taken", meta.get("route", "UNKNOWN")))
        node_path = list(meta.get("node_path") or state.get("node_path") or [])
        errors = list(meta.get("errors") or state.get("errors") or [])
        timing = dict(state.get("timing") or {})
        total_latency_ms = float(meta.get("execution_time_ms", 0.0))

        # Extract token metrics from metadata
        rag_tokens = int(meta.get("rag_tokens", 0))
        graph_tokens = int(meta.get("graph_tokens", 0))
        memory_tokens = int(meta.get("memory_tokens", 0))
        tool_tokens = int(meta.get("tool_tokens", 0))
        prompt_tokens = int(meta.get("total_prompt_tokens", len(user_query.split()) * 2))
        completion_tokens = max(1, len(final_response.split()) * 2)

        # Extract context strings
        rag_ctx = str(state.get("retrieved_rag_context", "")).strip()
        graph_ctx = str(state.get("retrieved_graph_context", "")).strip()
        memory_ctx = str(state.get("retrieved_memory_context", "")).strip()
        tool_ctx = str(state.get("retrieved_tool_context", "")).strip()

        # 1. Calculate layer-level metrics (heuristic)
        rag_metrics = calculate_rag_metrics(user_query, final_response, rag_ctx)
        graph_metrics = calculate_graph_metrics(user_query, final_response, graph_ctx)
        memory_metrics = calculate_memory_metrics(user_query, final_response, memory_ctx, memory_tokens)
        tool_metrics = calculate_tool_metrics(user_query, final_response, tool_ctx, route_taken)
        langgraph_metrics = calculate_langgraph_metrics(node_path, timing, errors, total_latency_ms)

        # 1b. Run RAGAS LLM-as-judge evaluation if RAG context is present
        ragas_metrics = {}
        if rag_ctx and "Offline:" not in rag_ctx and _RAGAS_AVAILABLE:
            try:
                ragas_metrics = await ragas_evaluator.evaluate(
                    queries=[user_query],
                    responses=[final_response],
                    contexts=[[rag_ctx]],
                    ground_truths=None,
                )
                if ragas_metrics.get("faithfulness", 0.0) > 0:
                    rag_metrics.faithfulness = ragas_metrics["faithfulness"]
                if ragas_metrics.get("context_precision", 0.0) > 0:
                    rag_metrics.context_precision = ragas_metrics["context_precision"]
                    rag_metrics.retrieval_precision = ragas_metrics["context_precision"]
                if ragas_metrics.get("context_recall", 0.0) > 0:
                    rag_metrics.context_recall = ragas_metrics["context_recall"]
                    rag_metrics.retrieval_recall = ragas_metrics["context_recall"]
                if ragas_metrics.get("answer_relevancy", 0.0) > 0:
                    rag_metrics.context_relevance = ragas_metrics["answer_relevancy"]
                logger.info(f"RAGAS evaluation integrated: {ragas_metrics}")
            except Exception as e:
                logger.warning(f"RAGAS evaluation failed (non-blocking): {e}")

        # 2. Calculate overall groundedness & faithfulness across active contexts
        combined_context = "\n\n".join([c for c in [rag_ctx, graph_ctx, memory_ctx, tool_ctx] if c and "Offline:" not in c])
        overall_groundedness = calculate_groundedness(final_response, combined_context)
        overall_faithfulness = calculate_faithfulness(final_response, combined_context)
        # Override with RAGAS faithfulness if available
        if ragas_metrics.get("faithfulness", 0.0) > 0:
            overall_faithfulness = ragas_metrics["faithfulness"]

        system_metrics = calculate_system_metrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            rag_tokens=rag_tokens,
            graph_tokens=graph_tokens,
            memory_tokens=memory_tokens,
            tool_tokens=tool_tokens,
            total_latency_ms=total_latency_ms,
            response_time_ms=total_latency_ms * 0.8,  # LLM generation approx 80% of total
            groundedness=overall_groundedness,
            faithfulness=overall_faithfulness
        )

        # 3. Construct structured report sub-objects
        workflow_report = WorkflowReport(
            workflow_id=workflow_id,
            route_taken=route_taken,
            executed_nodes=node_path,
            status="SUCCESS" if not errors else "DEGRADED_OR_FALLBACK",
            latency_ms=total_latency_ms,
            error_count=len(errors)
        )

        rag_report = RAGReport(
            query=user_query,
            retrieved_chunks_count=len([c for c in rag_ctx.split("\n\n") if c.strip()]) if rag_ctx and "Offline:" not in rag_ctx else 0,
            precision=rag_metrics.retrieval_precision,
            recall=rag_metrics.retrieval_recall,
            mrr=rag_metrics.mrr,
            groundedness=rag_metrics.groundedness,
            faithfulness=rag_metrics.faithfulness
        )

        memory_report = MemoryReport(
            user_id=str(meta.get("user_id", state.get("user_id", "default"))),
            retrieval_accuracy=memory_metrics.memory_retrieval_accuracy,
            memory_tokens=memory_tokens
        )

        graph_report = GraphReport(
            query=user_query,
            relationship_accuracy=graph_metrics.relationship_accuracy,
            average_degree=graph_metrics.average_node_degree,
            graph_tokens=graph_tokens
        )

        tool_report = ToolReport(
            tool_name="tool_batch" if tool_ctx and "Offline:" not in tool_ctx else "none",
            success_rate=tool_metrics.tool_success_rate,
            execution_time_ms=tool_metrics.average_execution_time_ms,
            cached=tool_metrics.cache_hit_ratio > 0.0
        )

        llm_report = LLMReport(
            response_time_ms=system_metrics.response_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate_usd=system_metrics.llm_cost_estimate_usd,
            hallucination_score=system_metrics.hallucination_score,
            confidence_score=system_metrics.answer_confidence
        )

        active_mods = []
        if rag_ctx and "Offline:" not in rag_ctx:
            active_mods.append("Hybrid RAG")
        if graph_ctx and "Offline:" not in graph_ctx:
            active_mods.append("GraphRAG")
        if memory_ctx and "Offline:" not in memory_ctx:
            active_mods.append("Long-Term Memory")
        if tool_ctx and "Offline:" not in tool_ctx:
            active_mods.append("Tool System")

        # Strict 4-tier health calculation (HEALTHY, WARNING, DEGRADED, CRITICAL)
        err_rate = len(errors) / max(1, len(node_path))
        if err_rate > 0.20 or system_metrics.hallucination_score > 0.50 or total_latency_ms > 10000.0:
            health_status = "CRITICAL"
        elif err_rate > 0.05 or system_metrics.hallucination_score > 0.30 or total_latency_ms > 5000.0:
            health_status = "DEGRADED"
        elif err_rate > 0.0 or system_metrics.hallucination_score > 0.15 or total_latency_ms > 2000.0:
            health_status = "WARNING"
        else:
            health_status = "HEALTHY"

        system_health_report = SystemHealthReport(
            status=health_status,
            active_modules=active_mods or ["Direct LLM"],
            error_rate=err_rate,
            avg_latency_ms=total_latency_ms
        )

        # 4. Return consolidated EvaluationReport
        report = EvaluationReport(
            workflow_id=workflow_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            rag_metrics=rag_metrics,
            graph_metrics=graph_metrics,
            memory_metrics=memory_metrics,
            tool_metrics=tool_metrics,
            langgraph_metrics=langgraph_metrics,
            system_metrics=system_metrics,
            workflow_report=workflow_report,
            rag_report=rag_report,
            memory_report=memory_report,
            graph_report=graph_report,
            tool_report=tool_report,
            llm_report=llm_report,
            system_health_report=system_health_report
        )

        logger.info(
            f"Evaluated workflow '{workflow_id}' | Status: {system_health_report.status} | "
            f"Hallucination: {system_metrics.hallucination_score:.3f} | Confidence: {system_metrics.answer_confidence:.3f} | "
            f"Groundedness: {overall_groundedness:.3f} | Faithfulness: {overall_faithfulness:.3f}"
        )
        return report


# Singleton instance of the evaluation engine
evaluator = EvaluationEngine()
