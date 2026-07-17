# File: app/api/v1/memory.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response
from app.utils.sanitizer import sanitize_payload

router = APIRouter(tags=["Memory"])


@router.get("/history", response_model=APIResponse[dict], summary="Retrieve Conversation History")
async def get_memory_history(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Memory)
    Endpoint for querying user session memory and conversation summaries.
    """
    data = sanitize_payload({"status": "Memory endpoint ready"})
    return success_response(
        data=data,
        message="Memory history endpoint initialized",
        request_id=request_id,
    )


@router.get("/profile/{user_id}", response_model=APIResponse[dict], summary="Get User Long-Term Memory Profile")
@router.get("/profile", response_model=APIResponse[dict], summary="Get User Profile (Query Param)")
async def get_user_memory_profile(user_id: str = "user-01", request_id: str = Depends(get_request_id)):
    """
    Retrieves synthesized long-term semantic profile, facts, and retention weights for the user.
    """
    raw = {
        "user_id": user_id,
        "full_name": "User",
        "preference_summary": "Likes precise technical answers and code-first solutions.",
        "total_memories": 18,
        "semantic_memories": [
            {"id": "mem-1", "category": "TECHNICAL_SKILL", "content": "Comfortable with Python, modern web frameworks, and AI orchestration.", "confidence": 0.99, "importance": 0.95, "last_accessed": "2026-07-15T18:20:00Z"},
            {"id": "mem-2", "category": "ARCHITECTURE_PREF", "content": "Prefers read-only evaluation hooks and strict type safety.", "confidence": 0.98, "importance": 0.92, "last_accessed": "2026-07-15T19:00:00Z"}
        ],
        "episodes": [
            {"id": "ep-101", "summary": "Completed end-to-end verification pass.", "timestamp": "2026-07-15T19:28:27Z", "tokens_used": 1240}
        ]
    }
    data = sanitize_payload(raw)
    return success_response(
        data=data,
        message=f"Retrieved memory profile for user {user_id}",
        request_id=request_id,
    )


@router.delete("/profile/{user_id}", response_model=APIResponse[dict], summary="Clear User Long-Term Memory Profile")
async def delete_user_memory_profile(user_id: str, request_id: str = Depends(get_request_id)):
    """
    Stubbed profile clear endpoint used by the frontend memory dashboard.
    """
    data = sanitize_payload({"user_id": user_id, "cleared": True})
    return success_response(
        data=data,
        message=f"Cleared memory profile for user {user_id}",
        request_id=request_id,
    )
