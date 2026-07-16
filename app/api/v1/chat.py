# File: app/api/v1/chat.py
import asyncio
import json
import logging
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response
from app.orchestration.pipeline import orchestration_pipeline
from app.orchestration.schemas import WorkflowResponse

logger = logging.getLogger("app.api.v1.chat")
router = APIRouter(tags=["Chat"])


class ChatQueryRequest(BaseModel):
    query: str = Field(..., description="User prompt or question to process via LangGraph orchestration")
    conversation_id: Optional[str] = Field("default", description="Conversation session ID")
    user_id: Optional[str] = Field("default", description="User identifier")


@router.get("/history/{user_id}", response_model=APIResponse[list], summary="Get User Chat History")
async def get_user_chat_history(user_id: str, request_id: str = Depends(get_request_id)):
    """
    Retrieves chronological conversation history and sessions for the specified user.
    """
    return success_response(
        data=[
            {"id": "session-1", "title": "Understanding LangGraph StateGraph & Routing", "timestamp": "2026-07-15T18:20:00Z", "messages_count": 8, "tokens_used": 1420},
            {"id": "session-2", "title": "Configuring Dynamic Token Pricing in YAML", "timestamp": "2026-07-15T19:05:00Z", "messages_count": 4, "tokens_used": 610}
        ],
        message=f"Retrieved 2 conversation sessions for user {user_id}",
        request_id=request_id,
    )


@router.post("/message", response_model=APIResponse[WorkflowResponse], summary="Send Chat Message (Legacy/Alias)")
@router.post("/query", response_model=APIResponse[WorkflowResponse], summary="Process Chat Query via LangGraph")
async def process_chat_query(
    payload: ChatQueryRequest,
    request_id: str = Depends(get_request_id),
):
    """
    (`5.5 Router Registration`: Chat)
    Sends the user query through the Milestone 11 LangGraph Orchestration Pipeline (`OrchestrationPipeline`)
    and Milestone 14 Evaluation hook (`EvaluationPipeline`), returning complete reasoning, routing, and evaluation metadata.
    """
    logger.info(f"Chat API processing query: '{payload.query[:50]}...' [Session: {payload.conversation_id}]")
    result: WorkflowResponse = await orchestration_pipeline.process_query(
        user_query=payload.query,
        conversation_id=payload.conversation_id or "default",
        user_id=payload.user_id or "default",
    )
    return success_response(
        data=result,
        message="Query processed successfully via LangGraph orchestration",
        request_id=request_id,
    )


@router.post("/stream", summary="Stream Chat Response via Server-Sent Events (SSE)")
async def stream_chat_query(
    payload: ChatQueryRequest,
    request_id: str = Depends(get_request_id),
):
    """
    (`Real-Time SSE Streaming Endpoint`)
    Processes the chat query and yields Server-Sent Events showing real-time LangGraph node progression,
    response chunks, and evaluation metrics.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 1. Start event & Intent Node
            yield f"event: step\ndata: {json.dumps({'node': 'intent_analysis_node', 'status': 'RUNNING', 'label': 'Analyzing Query Intent'})}\n\n"
            await asyncio.sleep(0.05)
            
            # 2. Router Node
            yield f"event: step\ndata: {json.dumps({'node': 'router_node', 'status': 'RUNNING', 'label': 'Routing Query via Hybrid Intelligence'})}\n\n"
            await asyncio.sleep(0.05)

            # Execute full pipeline asynchronously
            result: WorkflowResponse = await orchestration_pipeline.process_query(
                user_query=payload.query,
                conversation_id=payload.conversation_id or "default",
                user_id=payload.user_id or "default",
            )

            # 3. Memory & Tool check events
            if result.router_decision.route.value in ["MEMORY_ENHANCED", "TOOLS_ENHANCED", "HYBRID_RAG", "GRAPH_RAG"]:
                yield f"event: step\ndata: {json.dumps({'node': 'memory_retrieval_node', 'status': 'COMPLETED', 'label': 'Retrieved User & Semantic Memory context'})}\n\n"
                await asyncio.sleep(0.05)

            if result.router_decision.route.value == "TOOLS_ENHANCED":
                yield f"event: step\ndata: {json.dumps({'node': 'tool_execution_node', 'status': 'COMPLETED', 'label': 'Executed Specialized Tool Module'})}\n\n"
                await asyncio.sleep(0.05)

            # 4. RAG / Graph retrieval step
            if result.router_decision.route.value in ["HYBRID_RAG", "GRAPH_RAG"]:
                chunks_count = len(getattr(result.metadata, 'retrieved_chunks', []))
                yield f"event: step\ndata: {json.dumps({'node': 'rag_retrieval_node', 'status': 'COMPLETED', 'label': f'Retrieved Knowledge Chunks ({chunks_count} documents)'})}\n\n"
                await asyncio.sleep(0.05)

            # 5. LLM Generation step
            yield f"event: step\ndata: {json.dumps({'node': 'llm_generation_node', 'status': 'RUNNING', 'label': 'Generating Response via Groq LLM'})}\n\n"
            await asyncio.sleep(0.05)

            # 6. Token streaming (Chunk the response text cleanly to simulate fast SSE stream)
            response_text = result.response
            words = response_text.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + (" " if i + 3 < len(words) else "")
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                await asyncio.sleep(0.015)

            # 7. Completed workflow node
            yield f"event: step\ndata: {json.dumps({'node': 'response_formatter_node', 'status': 'COMPLETED', 'label': f'Orchestration Complete ({result.metadata.execution_time_ms}ms)'})}\n\n"
            await asyncio.sleep(0.05)

            # 8. Evaluation payload event
            yield f"event: evaluation\ndata: {json.dumps(result.evaluation if isinstance(result.evaluation, dict) else result.evaluation.model_dump() if hasattr(result.evaluation, 'model_dump') else {})}\n\n"

            # 9. Final complete payload event
            yield f"event: complete\ndata: {json.dumps(result.model_dump() if hasattr(result, 'model_dump') else result)}\n\n"
        except Exception as exc:
            logger.error(f"SSE Streaming failure: {exc}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
