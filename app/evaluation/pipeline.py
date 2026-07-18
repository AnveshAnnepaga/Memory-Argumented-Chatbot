# File: app/evaluation/pipeline.py
"""
(`Milestone 14 Evaluation & Observability Pipeline Wrapper`)
Provides a unified, async-compatible facade coordinating the read-only inspection
of LangGraph workflows (`observe_workflow`), telemetry aggregation, and dashboard summaries.
"""
import logging
from typing import Any, Dict, Optional

from app.evaluation.dashboard import dashboard_service
from app.evaluation.evaluator import evaluator
from app.evaluation.metrics import metrics_engine
from app.evaluation.monitor import monitoring_engine
from app.evaluation.schemas import DashboardResponse, EvaluationReport

logger = logging.getLogger("app.evaluation.pipeline")


class EvaluationPipeline:
    """
    (`Unified Read-Only Evaluation & Observability Pipeline`)
    Sits alongside the LangGraph orchestration layer. Never blocks or modifies
    application logic; observes finalized state outputs and computes enterprise telemetry.
    """
    def __init__(self):
        self._evaluator = evaluator
        self._monitor = monitoring_engine
        self._metrics = metrics_engine
        self._dashboard = dashboard_service

    async def observe_workflow(
        self,
        state: Dict[str, Any],
        response_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationReport:
        """
        Observes a finalized workflow state, computes multi-layer evaluation metrics,
        logs monitoring events, and aggregates telemetry in real time.
        """
        try:
            # 1. Evaluate the workflow state read-only across all 6 layers
            report = await self._evaluator.evaluate_workflow(
                state=state,
                response_text=response_text,
                metadata=metadata
            )

            # 2. Capture monitoring event telemetry
            event = self._monitor.observe_event(
                state=state,
                metadata=metadata
            )

            # 3. Record evaluation report and event in MetricsEngine for aggregation & dashboard
            self._metrics.record_evaluation(report, event)

            logger.info(
                f"EvaluationPipeline observed workflow '{report.workflow_id}' | "
                f"Route: {report.workflow_report.route_taken} | "
                f"Health: {report.system_health_report.status} | "
                f"Groundedness: {report.rag_metrics.groundedness:.2f}"
            )
            return report

        except Exception as exc:
            logger.error(f"Non-blocking evaluation observation error: {exc}", exc_info=True)
            # Safe read-only fallback report to guarantee zero disruption to core user flow
            return EvaluationReport(
                workflow_id="eval-fallback",
                workflow_report={"workflow_id": "eval-fallback", "route_taken": "UNKNOWN", "executed_nodes": [], "status": "EVAL_ERROR", "latency_ms": 0.0, "error_count": 1},
                rag_report={"query": "", "retrieved_chunks_count": 0, "precision": 0.0, "recall": 0.0, "mrr": 0.0, "groundedness": 0.0, "faithfulness": 0.0},
                memory_report={"user_id": "default", "retrieval_accuracy": 0.0, "memory_tokens": 0},
                graph_report={"query": "", "relationship_accuracy": 0.0, "average_degree": 0.0, "graph_tokens": 0},
                tool_report={"tool_name": "none", "success_rate": 0.0, "execution_time_ms": 0.0, "cached": False},
                llm_report={"response_time_ms": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "cost_estimate_usd": 0.0, "hallucination_score": 0.0, "confidence_score": 0.0},
                system_health_report={"status": "DEGRADED", "active_modules": [], "error_rate": 1.0, "avg_latency_ms": 0.0}
            )

    async def observe_workflow_background(
        self,
        state: Dict[str, Any],
        response_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Non-blocking background wrapper. Can be scheduled via `asyncio.create_task(...)`
        after the final AI response is returned to the user, ensuring zero latency overhead.
        """
        try:
            await self.observe_workflow(state, response_text, metadata)
        except Exception as e:
            logger.warning(f"Background evaluation task warning: {e}")

    def get_dashboard_summary(self) -> DashboardResponse:
        """Returns structured JSON summary metrics for dashboard presentation."""
        return self._dashboard.get_dashboard_summary()

    def get_dashboard_json(self) -> Dict[str, Any]:
        """Returns serialized dictionary representation of the dashboard summary."""
        return self._dashboard.get_dashboard_json()

    def get_aggregated_metrics(self, scope: str = "system", target_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns aggregate metrics across request, session, user, day, or system scopes."""
        return self._metrics.get_aggregated_metrics(scope=scope, target_id=target_id)

    def clear_telemetry(self) -> None:
        """Clears all observed evaluation and monitoring telemetry (useful for tests)."""
        self._metrics.clear()
        self._monitor.clear()


# Singleton instance of the evaluation pipeline
evaluation_pipeline = EvaluationPipeline()
