# File: app/core/openapi.py
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.core.config import settings

OPENAPI_TAGS = [
    {
        "name": "Chat",
        "description": "Conversational AI interaction endpoints with memory augmentation (`5.11 OpenAPI Tags`).",
    },
    {
        "name": "Memory",
        "description": "User session, conversation history, and summary management.",
    },
    {
        "name": "Knowledge",
        "description": "Semantic knowledge base queries and document ingestion pipeline.",
    },
    {
        "name": "Retrieval",
        "description": "Hybrid RAG search combining BM25 and dense Pinecone vector similarity.",
    },
    {
        "name": "Graph",
        "description": "Neo4j Knowledge Graph entity lookups and relationship querying.",
    },
    {
        "name": "Tools",
        "description": "External API tool integrations (Weather, News, Search, Currency).",
    },
    {
        "name": "Evaluation",
        "description": "Ragas and DeepEval evaluation benchmarks (Faithfulness, Groundedness).",
    },
    {
        "name": "Monitoring",
        "description": "System liveness, readiness probes, and telemetry metrics.",
    },
    {
        "name": "Admin",
        "description": "Administrative system controls and configuration inspection.",
    },
]


def customize_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    (`5.4 OpenAPI Customization`)
    Generates and caches a customized OpenAPI schema overriding default Swagger metadata.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )

    openapi_schema["info"]["contact"] = {
        "name": "AI Platform Engineering Team",
        "email": "support@example.com",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
