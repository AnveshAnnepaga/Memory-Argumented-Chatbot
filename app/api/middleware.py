# File: app/api/middleware.py
import logging
import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger("app.api.middleware")


class RequestLoggerAndTimerMiddleware(BaseHTTPMiddleware):
    """
    (`5.6 Middleware Registration`: Request Logger & Request Timer)
    Assigns a unique X-Request-ID to every request, tracks start and completion time,
    and logs request metrics.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()
        logger.info(
            f"--> [{request.method}] {request.url.path} | RequestID: {request_id} | Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            # Let global exception handlers catch or re-raise
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"<-- [{request.method}] {request.url.path} | RequestID: {request_id} | FAILED in {process_time_ms}ms | Error: {exc}"
            )
            raise

        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)

        logger.info(
            f"<-- [{request.method}] {request.url.path} | RequestID: {request_id} | Status: {response.status_code} | Time: {process_time_ms}ms"
        )
        return response


def register_middleware(app: FastAPI) -> None:
    """
    Registers CORS, Request Logger/Timer, Trusted Host, and optional GZip middleware.
    (`5.6 Middleware Registration`)
    """
    # Note: Starlette executes BaseHTTPMiddleware in reverse order of addition.
    # We add CORS first so it is the outermost wrapping handler for preflight OPTIONS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://localhost",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )

    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
    )

    # Custom request tracking and timing middleware
    app.add_middleware(RequestLoggerAndTimerMiddleware)

    logger.info("Application middleware registered successfully (CORS, TrustedHost, GZip, RequestLoggerAndTimer).")
