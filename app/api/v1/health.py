# File: app/api/v1/health.py
from fastapi import APIRouter, Depends, Request
from app.api.dependencies import get_config, get_request_id
from app.core.config import Settings
from app.core.infrastructure import InfrastructureRegistry
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Monitoring"])


@router.get("/health", response_model=APIResponse[dict], summary="Application & Infrastructure Health Check")
async def health_check(
    request_id: str = Depends(get_request_id),
    config: Settings = Depends(get_config),
):
    """
    (`6.7 Health Integration`)
    Returns high-level health status of the application and diagnostic status across
    PostgreSQL, MongoDB, Pinecone, Neo4j, and Groq LLM Manager.
    """
    infra_health = await InfrastructureRegistry.health_check_all()
    return success_response(
        data={
            "status": infra_health.get("overall_status", "healthy"),
            "app_name": config.APP_NAME,
            "version": config.APP_VERSION,
            "environment": config.APP_ENV,
            "infrastructure": infra_health.get("services", {}),
        },
        message="System and infrastructure health check completed",
        request_id=request_id,
    )


@router.get("/status", response_model=APIResponse[dict], summary="Detailed System Status Check")
async def system_status(
    request_id: str = Depends(get_request_id),
    config: Settings = Depends(get_config),
):
    """
    (`6.7 Health Integration`)
    Returns detailed configuration, active feature flags, database reachability,
    and LLM provider readiness diagnostics.
    """
    infra_health = await InfrastructureRegistry.health_check_all()
    services = infra_health.get("services", {})
    return success_response(
        data={
            "application": {
                "name": config.APP_NAME,
                "version": config.APP_VERSION,
                "build": config.APP_BUILD_VERSION,
                "environment": config.APP_ENV,
                "debug": config.DEBUG,
            },
            "feature_flags": config.feature_flags.model_dump(),
            "databases": {
                "postgres": services.get("postgres", {}),
                "mongodb": services.get("mongodb", {}),
                "pinecone": services.get("pinecone", {}),
                "neo4j": services.get("neo4j", {}),
            },
            "ai_provider": services.get("groq", services.get("llm", {})),
            "overall_infrastructure_status": infra_health.get("overall_status", "healthy"),
        },
        message="Detailed system status and infrastructure diagnostics retrieved successfully",
        request_id=request_id,
    )


@router.get("/ready", response_model=APIResponse[dict], summary="Readiness Probe")
async def readiness_probe(request_id: str = Depends(get_request_id)):
    """
    (`5.9 Health APIs`) Kubernetes / container readiness probe.
    """
    return success_response(
        data={"ready": True},
        message="Application is ready to accept traffic",
        request_id=request_id,
    )


@router.get("/live", response_model=APIResponse[dict], summary="Liveness Probe")
async def liveness_probe(request_id: str = Depends(get_request_id)):
    """
    (`5.9 Health APIs`) Kubernetes / container liveness probe.
    """
    return success_response(
        data={"live": True},
        message="Application process is alive and responsive",
        request_id=request_id,
    )
