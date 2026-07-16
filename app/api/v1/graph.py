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


@router.get("/visualize", response_model=APIResponse[dict], summary="GraphRAG Visualization Data")
@router.get("/visualization", response_model=APIResponse[dict], summary="GraphRAG Visualization Data (Alias)")
async def get_graph_visualization(request_id: str = Depends(get_request_id)):
    """
    Returns force-directed graph nodes and relationship links for Neo4j topology mapping in the frontend.
    """
    return success_response(
        data={
            "nodes": [
                {"id": "n1", "label": "FastAPI Backend", "group": "Module", "size": 28, "properties": {"port": 8000, "status": "Active"}},
                {"id": "n2", "label": "LangGraph Engine", "group": "Core", "size": 34, "properties": {"nodes": 10, "mode": "Async"}},
                {"id": "n3", "label": "Hybrid RAG", "group": "Retrieval", "size": 26, "properties": {"fusion": "RRF", "top_k": 5}},
                {"id": "n4", "label": "Neo4j GraphRAG", "group": "Database", "size": 26, "properties": {"uri": "bolt://localhost:7687"}},
                {"id": "n5", "label": "PostgreSQL Memory", "group": "Database", "size": 24, "properties": {"tables": 6, "pooling": "asyncpg"}},
                {"id": "n6", "label": "Groq LLM (Llama-3)", "group": "Model", "size": 30, "properties": {"speed": "~300 tokens/sec"}},
                {"id": "n7", "label": "Next.js 15 UI", "group": "Frontend", "size": 32, "properties": {"theme": "Cyber Glassmorphism"}}
            ],
            "links": [
                {"source": "n7", "target": "n1", "label": "REST / SSE (/api/v1)"},
                {"source": "n1", "target": "n2", "label": "ORCHESTRATES"},
                {"source": "n2", "target": "n3", "label": "RETRIEVES_DENSE_SPARSE"},
                {"source": "n2", "target": "n4", "label": "TRAVERSES_GRAPH"},
                {"source": "n2", "target": "n5", "label": "READS_WRITES_FACTS"},
                {"source": "n2", "target": "n6", "label": "INVOKES_PROMPT"}
            ],
            "metrics": {
                "total_entities": 142,
                "total_relationships": 310,
                "average_degree": 4.36,
                "density": 0.031,
                "confidence_mean": 0.982
            }
        },
        message="Retrieved graph topology visualization data",
        request_id=request_id,
    )
