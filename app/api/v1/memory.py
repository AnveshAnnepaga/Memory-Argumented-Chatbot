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
