# File: app/api/v1/tools.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Tools"])


@router.get("/list", response_model=APIResponse[dict], summary="List Registered Tools")
async def list_tools(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Tools)
    Endpoint listing all available external APIs and tools (Weather, News, Search, Currency).
    """
    return success_response(
        data={"status": "Tools router ready for Tool Manager API execution"},
        message="Tools list endpoint initialized",
        request_id=request_id,
    )
