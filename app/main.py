# File: app/main.py
import asyncio
import logging
import sys
from fastapi import Depends, FastAPI, Request

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
from app.api.dependencies import get_config, get_request_id
from app.api.exceptions import register_exception_handlers
from app.api.middleware import register_middleware
from app.api.v1.router import v1_router
from app.core.config import settings, Settings
from app.core.openapi import customize_openapi
from app.lifespan import lifespan
from app.schemas.common import APIResponse, success_response

logger = logging.getLogger("app.main")


def create_app() -> FastAPI:
    """
    (`5.1 Application Factory`)
    Constructs and configures the centralized FastAPI application instance.
    Wires configuration, middleware, global exception handlers, OpenAPI overrides,
    and all versioned API routers.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. Register Middleware (`5.6 Middleware Registration`)
    register_middleware(application)

    # 2. Register Global Exception Handlers (`5.7 Exception Registration`)
    register_exception_handlers(application)

    # 3. Register API Versioned Routers (`5.3 API Versioning` & `5.5 Router Registration`)
    application.include_router(v1_router, prefix=settings.API_PREFIX)

    # 4. Customize OpenAPI Schema (`5.4 OpenAPI Customization` & `5.11 OpenAPI Tags`)
    application.openapi = lambda: customize_openapi(application)

    # 5. Register Root Welcome Endpoint (`5.10 Root Endpoint`)
    @application.get("/", response_model=APIResponse[dict], tags=["Monitoring"], summary="Welcome Endpoint")
    async def root_welcome(
        request: Request,
        request_id: str = Depends(get_request_id),
        config: Settings = Depends(get_config),
    ):
        """
        (`5.10 Root Endpoint`)
        Acts as the primary application welcome endpoint reporting core metadata and documentation URLs.
        """
        base_url = str(request.base_url).rstrip("/")
        return success_response(
            data={
                "application": config.APP_NAME,
                "version": config.APP_VERSION,
                "build": config.APP_BUILD_VERSION,
                "environment": config.APP_ENV,
                "status": "operational",
                "documentation": {
                    "swagger": f"{base_url}/docs",
                    "redoc": f"{base_url}/redoc",
                    "openapi_json": f"{base_url}/openapi.json",
                },
                "api_v1_prefix": config.API_PREFIX,
            },
            message=f"Welcome to {config.APP_NAME} API v{config.APP_VERSION}",
            request_id=request_id,
        )

    logger.info(f"FastAPI Application initialized cleanly via create_app() [Prefix: {settings.API_PREFIX}]")
    return application


# Global application instance for ASGI servers (`uvicorn app.main:app`)
app = create_app()
