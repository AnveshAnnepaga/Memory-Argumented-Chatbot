# File: app/api/v1/evaluation.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Evaluation"])


@router.get("/metrics", response_model=APIResponse[dict], summary="Get Evaluation Metrics")
async def get_evaluation_metrics(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Evaluation)
    Endpoint for querying Ragas and DeepEval benchmark metrics (Faithfulness, Groundedness).
    """
    return success_response(
        data={"status": "Evaluation router ready for Ragas & DeepEval pipeline reporting"},
        message="Evaluation metrics endpoint initialized",
        request_id=request_id,
    )
