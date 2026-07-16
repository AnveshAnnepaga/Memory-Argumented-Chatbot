# File: app/evaluation/dashboard.py
"""
(`Milestone 14 Dashboard JSON Service`)
Exposes `DashboardService` returning clean API-ready JSON metrics for system
monitoring dashboards. Zero frontend dependencies or UI coupling.
"""
import logging
from typing import Any, Dict

from app.evaluation.metrics import metrics_engine
from app.evaluation.schemas import DashboardResponse

logger = logging.getLogger("app.evaluation.dashboard")


class DashboardService:
    """
    (`Dashboard Telemetry Service`)
    Aggregates stored reports from `metrics_engine` and returns API-ready JSON
    summaries reflecting overall system health, accuracy, and latency.
    """
    def get_dashboard_summary(self) -> DashboardResponse:
        """
        Returns clean, API-ready JSON metrics across all observed workflow executions.
        """
        reports = metrics_engine._reports
        count = len(reports)

        if count == 0:
            return DashboardResponse(
                system_health="OPTIMAL",
                workflow_latency="0.0ms",
                rag_accuracy="100.0%",
                graph_quality="100.0%",
                memory_usage="100.0%",
                tool_success_rate="100.0%",
                hallucination_score="0.000",
                average_response_time="0.0ms",
                total_requests=0,
                cost_estimate_total="$0.0000"
            )

        # Calculate averages across all recorded evaluation reports
        avg_lat = sum(r.system_metrics.total_latency_ms for r in reports) / count
        avg_resp = sum(r.system_metrics.response_time_ms for r in reports) / count
        avg_halluc = sum(r.system_metrics.hallucination_score for r in reports) / count
        total_cost = sum(r.system_metrics.llm_cost_estimate_usd for r in reports)

        # Layer averages
        rag_acc = sum(r.rag_metrics.groundedness for r in reports) / count
        graph_qual = sum(r.graph_metrics.graph_context_quality for r in reports) / count
        mem_use = sum(r.memory_metrics.memory_retrieval_accuracy for r in reports) / count
        tool_succ = sum(r.tool_metrics.tool_success_rate for r in reports) / count

        # Check 4-tier system health criteria
        error_rate = sum(r.workflow_report.error_count for r in reports) / max(1, count)
        if error_rate > 0.20 or avg_halluc > 0.50 or avg_lat > 10000.0:
            health = "CRITICAL"
        elif error_rate > 0.05 or avg_halluc > 0.30 or avg_lat > 5000.0:
            health = "DEGRADED"
        elif error_rate > 0.0 or avg_halluc > 0.15 or avg_lat > 2000.0:
            health = "WARNING"
        else:
            health = "HEALTHY"

        response = DashboardResponse(
            system_health=health,
            workflow_latency=f"{avg_lat:.1f}ms",
            rag_accuracy=f"{rag_acc * 100:.1f}%",
            graph_quality=f"{graph_qual * 100:.1f}%",
            memory_usage=f"{mem_use * 100:.1f}%",
            tool_success_rate=f"{tool_succ * 100:.1f}%",
            hallucination_score=f"{avg_halluc:.3f}",
            average_response_time=f"{avg_resp:.1f}ms",
            total_requests=count,
            cost_estimate_total=f"${total_cost:.4f}"
        )

        logger.debug(f"Generated Dashboard Summary JSON | Health: {health} | Total Requests: {count}")
        return response

    def get_dashboard_json(self) -> Dict[str, Any]:
        """Returns the dashboard summary as a clean Python dictionary suitable for JSON serialization."""
        return self.get_dashboard_summary().model_dump()


# Singleton instance of the dashboard service
dashboard_service = DashboardService()
