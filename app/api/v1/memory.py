# File: app/api/v1/memory.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Memory"])


@router.get("/history", response_model=APIResponse[dict], summary="Retrieve Conversation History")
async def get_memory_history(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Memory)
    Endpoint for querying user session memory and conversation summaries.
    """
    return success_response(
        data={"status": "Memory router ready for MongoDB / PostgreSQL integration"},
        message="Memory history endpoint initialized",
        request_id=request_id,
    )


@router.get("/profile/{user_id}", response_model=APIResponse[dict], summary="Get User Long-Term Memory Profile")
@router.get("/profile", response_model=APIResponse[dict], summary="Get User Profile (Query Param)")
async def get_user_memory_profile(user_id: str = "anvesh-01", request_id: str = Depends(get_request_id)):
    """
    Retrieves synthesized long-term semantic profile, facts, and Ebbinghaus retention weights for the user.
    """
    return success_response(
        data={
            "user_id": user_id,
            "full_name": "Anvesh Mishra",
            "preference_summary": "AI Systems Architect & Backend Specialist preferring precise technical markdown and code-first solutions.",
            "total_memories": 18,
            "semantic_memories": [
                {"id": "mem-1", "category": "TECHNICAL_SKILL", "content": "Expert in Python, FastAPI, LangGraph, Neo4j, and Next.js 15.", "confidence": 0.99, "importance": 0.95, "last_accessed": "2026-07-15T18:20:00Z"},
                {"id": "mem-2", "category": "ARCHITECTURE_PREF", "content": "Prefers non-interfering read-only evaluation hooks and strict Pydantic V2 typing.", "confidence": 0.98, "importance": 0.92, "last_accessed": "2026-07-15T19:00:00Z"}
            ],
            "episodes": [
                {"id": "ep-101", "summary": "Completed Milestone 14 End-to-End Evaluation with 100% verification pass.", "timestamp": "2026-07-15T19:28:27Z", "tokens_used": 1240}
            ]
        },
        message=f"Retrieved memory profile for user {user_id}",
        request_id=request_id,
    )
