# File: app/lifespan.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from app.core.bootstrap import BootstrapManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    (`5.2 Lifespan Manager`)
    Orchestrates application lifecycle events during startup and shutdown
    by delegating to the centralized BootstrapManager.
    """
    # --- Startup Lifecycle ---
    await BootstrapManager.startup(app)
    try:
        yield
    finally:
        # --- Shutdown Lifecycle ---
        await BootstrapManager.shutdown(app)
