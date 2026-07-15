# File: app/api/v1/graph.py
from fastapi import APIRouter, Depends
from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Graph"])


@router.get("/entities", response_model=APIResponse[dict], summary="Query Knowledge Graph Entities")
async def get_graph_entities(request_id: str = Depends(get_request_id)):
    """
    (`5.5 Router Registration`: Graph)
    Endpoint for querying Neo4j entities and relational triplets.
    """
    return success_response(
        data={"status": "Graph router ready for Neo4j Cypher query execution"},
        message="Graph entities endpoint initialized",
        request_id=request_id,
    )
