# File: app/orchestration/pipeline.py
"""
(`Milestone 11 LangGraph Orchestration Pipeline`)
High-level orchestration wrapper exposing the clean public API (`process_query`)
used by FastAPI routers and background tasks.
"""
import logging
from typing import Optional

from app.orchestration.schemas import (
    IntentResult,
    IntentType,
    PromptContext,
    RouterDecision,
    RouteType,
    WorkflowMetadata,
    WorkflowResponse,
)
from app.orchestration.state import create_initial_state
from app.orchestration.workflow import orchestration_workflow
from app.evaluation.pipeline import evaluation_pipeline

logger = logging.getLogger("app.orchestration.pipeline")


class OrchestrationPipeline:
    """
    (`5️⃣ pipeline.py`)
    High-level orchestrator wrapper for Milestone 11.
    Initializes state, executes the LangGraph StateGraph, and returns validated API response payloads.
    """
    def __init__(self):
        self._graph = orchestration_workflow.app

    async def process_query(
        self,
        user_query: str,
        conversation_id: str = "default",
        user_id: str = "default",
        file_context: str = ""
    ) -> WorkflowResponse:
        """
        Executes the full LangGraph reasoning workflow on the incoming user query.
        """
        clean_query = user_query.strip()
        logger.info(f"Orchestration pipeline processing query: '{clean_query[:60]}...' (Session: {conversation_id})")

        initial_state = create_initial_state(
            user_query=clean_query,
            conversation_id=conversation_id,
            user_id=user_id,
            file_context=file_context
        )

        try:
            # Execute StateGraph
            final_state = await self._graph.ainvoke(initial_state)
            
            intent_data = final_state.get("intent")
            router_data = final_state.get("router_decision")
            meta_data = final_state.get("metadata", {})
            prompt_data = final_state.get("prompt_context")

            intent = IntentResult(**intent_data) if intent_data else IntentResult(intent=IntentType.GENERAL_CHAT)
            decision = RouterDecision(**router_data) if router_data else RouterDecision(route=RouteType.DIRECT_LLM)
            metadata = WorkflowMetadata(**meta_data) if meta_data else WorkflowMetadata()
            prompt_ctx = PromptContext(**prompt_data) if prompt_data else None

            response_text = final_state.get("llm_response", "").strip()
            if not response_text:
                response_text = f"Processed request: '{clean_query}' via route {decision.route.value}."

            # Read-only evaluation and observability hook
            eval_report = await evaluation_pipeline.observe_workflow(
                state=final_state,
                response_text=response_text,
                metadata=metadata.model_dump() if hasattr(metadata, "model_dump") else {}
            )

            return WorkflowResponse(
                response=response_text,
                intent=intent,
                router_decision=decision,
                metadata=metadata,
                prompt_context=prompt_ctx,
                evaluation=eval_report.model_dump() if hasattr(eval_report, "model_dump") else {}
            )
        except Exception as exc:
            logger.error(f"Critical workflow execution failure in OrchestrationPipeline: {exc}", exc_info=True)
            # Safe fallback response guaranteeing zero unhandled API crashes
            fallback_intent = IntentResult(intent=IntentType.GENERAL_CHAT, confidence=0.0, reasoning="Error fallback")
            fallback_decision = RouterDecision(route=RouteType.UNKNOWN, reasoning=str(exc))
            fallback_meta = WorkflowMetadata(
                conversation_id=conversation_id,
                user_id=user_id,
                route_taken=RouteType.UNKNOWN,
                errors=[str(exc)]
            )
            return WorkflowResponse(
                response=f"I encountered an internal orchestration issue processing your query: {exc}",
                intent=fallback_intent,
                router_decision=fallback_decision,
                metadata=fallback_meta
            )


# Singleton instance of the orchestration pipeline wrapper
orchestration_pipeline = OrchestrationPipeline()
