# File: app/api/v1/tools.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Tools"])


@router.get("", response_model=APIResponse[dict], summary="List Registered Tools (Root)")
@router.get("/list", response_model=APIResponse[dict], summary="List Registered Tools")
async def list_tools(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Tools)
    Endpoint listing all available external APIs and tools (Weather, News, Search, Currency).
    """
    return success_response(
        data={
            "tools": [
                {"name": "CalculatorTool", "description": "Evaluates arithmetic expressions and symbolic math equations safely.", "status": "ENABLED", "calls_24h": 18, "success_rate": "100%"},
                {"name": "WebSearchTool", "description": "Searches live external documentation and APIs.", "status": "ENABLED", "calls_24h": 24, "success_rate": "95.8%"},
                {"name": "SQLQueryTool", "description": "Executes analytical read-only SQL queries on system repositories.", "status": "ENABLED", "calls_24h": 12, "success_rate": "100%"},
                {"name": "GraphCypherTool", "description": "Generates and validates Cypher graph queries for multi-hop reasoning.", "status": "ENABLED", "calls_24h": 9, "success_rate": "100%"}
            ]
        },
        message="Tools list endpoint initialized",
        request_id=request_id,
    )
