# File: app/api/v1/monitoring.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Monitoring"])


@router.get("/metrics", response_model=APIResponse[dict], summary="Application Telemetry Metrics")
async def get_system_metrics(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Monitoring)
    Endpoint exposing application latency, active connections, and system resource metrics.
    """
    return success_response(
        data={"status": "Monitoring router ready for OpenTelemetry & custom metrics tracking"},
        message="System telemetry endpoint initialized",
        request_id=request_id,
    )
