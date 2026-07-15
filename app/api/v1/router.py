# File: app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.admin import router as admin_router
from app.api.v1.chat import router as chat_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.memory import router as memory_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.tools import router as tools_router

# Central API v1 Router Aggregator (`5.3 API Versioning` & `5.5 Router Registration`)
v1_router = APIRouter()

# Register all endpoint sub-routers under their respective API prefixes
v1_router.include_router(health_router)
v1_router.include_router(chat_router, prefix="/chat")
v1_router.include_router(memory_router, prefix="/memory")
v1_router.include_router(knowledge_router, prefix="/knowledge")
v1_router.include_router(ingestion_router, prefix="/ingestion")
v1_router.include_router(graph_router, prefix="/graph")
v1_router.include_router(retrieval_router, prefix="/retrieval")
v1_router.include_router(tools_router, prefix="/tools")
v1_router.include_router(evaluation_router, prefix="/evaluation")
v1_router.include_router(monitoring_router, prefix="/monitoring")
v1_router.include_router(admin_router, prefix="/admin")
