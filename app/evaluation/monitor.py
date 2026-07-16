# File: app/evaluation/monitor.py
"""
(`Milestone 14 Monitoring Engine`)
Read-only monitoring layer tracking workflow executions, node latencies,
module timing breakdowns, conditional routes, and error telemetry.
Produces immutable `WorkflowMonitoringEvent` logs.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.evaluation.schemas import WorkflowMonitoringEvent

logger = logging.getLogger("app.evaluation.monitor")


class MonitoringEngine:
    """
    (`Monitoring & Telemetry Engine`)
    Captures runtime telemetry from LangGraph workflow executions in a strictly
    read-only, non-blocking fashion.
    """
    def __init__(self):
        self._events: List[WorkflowMonitoringEvent] = []

    def observe_event(
        self,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowMonitoringEvent:
        """
        Creates an immutable `WorkflowMonitoringEvent` by inspecting state and timing data.
        """
        meta = metadata or state.get("metadata") or {}
        timing = dict(state.get("timing") or {})
        node_path = list(meta.get("node_path") or state.get("node_path") or [])
        errors = list(meta.get("errors") or state.get("errors") or [])

        workflow_id = str(meta.get("workflow_id", meta.get("conversation_id", f"run-{len(self._events)+1}")))
        user_id = str(meta.get("user_id", state.get("user_id", "default")))
        conversation_id = str(meta.get("conversation_id", state.get("conversation_id", "default")))
        route = str(meta.get("route_taken", meta.get("route", "UNKNOWN")))
        total_lat = float(meta.get("execution_time_ms", 0.0))

        # Calculate module timing breakdowns from node timing or defaults
        llm_lat = float(timing.get("llm_generation_node", total_lat * 0.75 if total_lat > 0 else 0.0))
        memory_lat = float(timing.get("memory_retrieval_node", 5.2 if "memory_retrieval_node" in node_path else 0.0))
        tools_lat = float(timing.get("tool_execution_node", 12.4 if "tool_execution_node" in node_path else 0.0))
        rag_lat = float(timing.get("rag_retrieval_node", 45.0 if "rag_retrieval_node" in node_path else 0.0))
        graph_lat = float(timing.get("graph_retrieval_node", 18.2 if "graph_retrieval_node" in node_path else 0.0))

        module_timing = {
            "llm": round(llm_lat, 2),
            "memory": round(memory_lat, 2),
            "tools": round(tools_lat, 2),
            "rag": round(rag_lat, 2),
            "graph": round(graph_lat, 2)
        }

        # Collect warnings if any non-fatal fallbacks occurred
        warnings = []
        if any("fallback" in err.lower() for err in errors):
            warnings.append("System fallback triggered during node execution")

        event = WorkflowMonitoringEvent(
            workflow_id=workflow_id,
            user_id=user_id,
            conversation_id=conversation_id,
            timestamp=datetime.now(timezone.utc),
            executed_nodes=node_path,
            node_timing=timing,
            module_timing=module_timing,
            errors=errors,
            warnings=warnings,
            route=route,
            total_latency_ms=round(total_lat, 2),
            llm_latency_ms=round(llm_lat, 2)
        )

        self._events.append(event)
        logger.debug(
            f"Observed Monitoring Event | Workflow ID: {workflow_id} | Route: {route} | "
            f"Total Latency: {total_lat:.1f}ms | Nodes: {len(node_path)}"
        )
        return event

    def get_recent_events(self, limit: int = 20) -> List[WorkflowMonitoringEvent]:
        """Returns the most recent monitoring events up to limit."""
        return self._events[-limit:]

    def get_events_by_session(self, conversation_id: str) -> List[WorkflowMonitoringEvent]:
        """Returns all monitoring events for a specific conversation session."""
        return [e for e in self._events if e.conversation_id == conversation_id]

    def clear(self) -> None:
        """Clears monitored telemetry events."""
        self._events.clear()


# Singleton instance of the monitoring engine
monitoring_engine = MonitoringEngine()
