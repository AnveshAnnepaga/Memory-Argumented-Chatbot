# File: app/api/exceptions.py
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import AppException
from app.schemas.common import error_response

logger = logging.getLogger("app.api.exceptions")


def _get_request_id(request: Request) -> str:
    """Safely extracts request ID from state or headers."""
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID", "N/A")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handles custom domain exceptions (`AppException` and subclasses)."""
    request_id = _get_request_id(request)
    logger.error(
        f"Domain exception occurred [{exc.code}]: {exc.message} | Path: {request.url.path} | RequestID: {request_id}"
    )
    payload = error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI Pydantic request validation failures."""
    request_id = _get_request_id(request)
    logger.warning(
        f"Validation failure | Path: {request.url.path} | RequestID: {request_id} | Errors: {exc.errors()}"
    )
    payload = error_response(
        code="VALIDATION_ERROR",
        message="Request payload validation failed",
        details={"errors": exc.errors()},
        request_id=request_id,
    )
    return JSONResponse(status_code=422, content=payload)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard Starlette / FastAPI HTTPExceptions (404, 401, 403, etc.)."""
    request_id = _get_request_id(request)
    logger.warning(
        f"HTTP exception [{exc.status_code}]: {exc.detail} | Path: {request.url.path} | RequestID: {request_id}"
    )
    code = "HTTP_ERROR"
    if exc.status_code == 404:
        code = "RESOURCE_NOT_FOUND"
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 429:
        code = "RATE_LIMIT_EXCEEDED"

    payload = error_response(
        code=code,
        message=str(exc.detail),
        details={},
        request_id=request_id,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected application crashes (`500 Internal Server Error`)."""
    request_id = _get_request_id(request)
    logger.exception(
        f"Unhandled system crash | Path: {request.url.path} | RequestID: {request_id} | Error: {str(exc)}"
    )
    payload = error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected system error occurred. Please try again later.",
        details={"error_type": type(exc).__name__} if hasattr(request.app.state, "debug") and request.app.state.debug else {},
        request_id=request_id,
    )
    return JSONResponse(status_code=500, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers all custom and system exception handlers to the FastAPI application.
    (`5.7 Exception Registration`)
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    logger.info("Global exception handlers registered successfully.")
