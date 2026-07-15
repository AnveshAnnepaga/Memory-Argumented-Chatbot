# File: app/database/pinecone.py
import asyncio
import logging
from typing import Any, Dict
from pinecone import Pinecone
from app.core.config import settings
from app.core.exceptions import PineconeException
from app.core.infrastructure import BaseInfrastructureManager
from app.core.retry import execute_with_retry

logger = logging.getLogger("app.database.pinecone")


class PineconeManager(BaseInfrastructureManager):
    """
    (`6.3 Pinecone Manager`)
    Manages Pinecone client connection, vector index access, namespace management,
    and index diagnostic health checks.
    """
    def __init__(self):
        super().__init__(name="pinecone")
        self.client: Pinecone | None = None
        self.index: Any | None = None
        self.stub_mode: bool = False

    @execute_with_retry(max_attempts=1, min_wait=0.2, max_wait=0.5, exceptions=(Exception,))
    def _check_stats(self) -> Dict[str, Any]:
        if not self.index:
            return {}
        return self.index.describe_index_stats()

    async def initialize(self) -> bool:
        """Initializes Pinecone client and connects to configured vector index."""
        cfg = settings.pinecone
        if not cfg.api_key or cfg.api_key == "your_pinecone_api_key_here":
            logger.warning("Pinecone API key not configured or placeholder. Entering offline/stub mode.")
            self._is_initialized = True
            self.stub_mode = True
            return False

        try:
            self.client = Pinecone(api_key=cfg.api_key)
            self.index = self.client.Index(cfg.index_name)
            # Verify connectivity asynchronously across threadpool with 2s timeout
            await asyncio.wait_for(asyncio.to_thread(self._check_stats), timeout=2.0)
            self._is_initialized = True
            self.stub_mode = False
            logger.info(f"Pinecone Vector Manager initialized [Index: '{cfg.index_name}' | Dim: {cfg.dimension}].")
            return True
        except Exception as exc:
            logger.warning(f"Pinecone initialization failed ({exc}). Entering offline/stub mode.")
            self._is_initialized = True
            self.stub_mode = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Diagnoses index status and vector counts."""
        if self.stub_mode or not self.index:
            return {
                "healthy": False,
                "status": "stubbed_local_dev",
                "message": f"Pinecone not connected (Index: '{settings.pinecone.index_name}')",
            }
        try:
            stats = self._check_stats()
            # Convert stats to dict if it's an object
            stats_dict = stats.to_dict() if hasattr(stats, "to_dict") else dict(stats) if isinstance(stats, dict) else {}
            return {"healthy": True, "status": "online", "index": settings.pinecone.index_name, "stats": stats_dict}
        except Exception as exc:
            return {"healthy": False, "status": "error", "error": str(exc)}

    def get_client(self) -> Pinecone | None:
        return self.client

    def get_index(self, index_name: str | None = None) -> Any | None:
        if index_name and self.client and index_name != settings.pinecone.index_name:
            return self.client.Index(index_name)
        return self.index

    def get_namespace(self, custom_namespace: str | None = None) -> str:
        return custom_namespace or settings.pinecone.namespace

    async def close(self) -> None:
        """(`6.9 Connection Lifecycle`) Clears active Pinecone client references."""
        if self.client:
            self.client = None
            self.index = None
            self._is_initialized = False
            logger.info("Pinecone client closed.")


pinecone_manager = PineconeManager()
