# File: app/database/mongodb.py
import asyncio
import logging
from typing import Any, Dict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.core.infrastructure import BaseInfrastructureManager
from app.core.retry import execute_with_retry

logger = logging.getLogger("app.database.mongodb")


class MongoManager(BaseInfrastructureManager):
    """
    (`6.2 MongoDB Manager`)
    Manages async Motor client connection pool, database access,
    and health diagnostics for MongoDB NoSQL document store.
    """
    def __init__(self):
        super().__init__(name="mongodb")
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.stub_mode: bool = False

    @execute_with_retry(max_attempts=1, min_wait=0.2, max_wait=0.5, exceptions=(Exception,))
    async def _ping_mongo(self) -> bool:
        if not self.client:
            return False
        await asyncio.wait_for(self.client.admin.command("ping"), timeout=1.5)
        return True

    async def initialize(self) -> bool:
        """Initializes Motor AsyncIOMotorClient and database handle."""
        cfg = settings.mongodb
        try:
            self.client = AsyncIOMotorClient(
                cfg.uri,
                maxPoolSize=cfg.max_connections,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
                socketTimeoutMS=1500,
            )
            self.db = self.client[cfg.db_name]
            await self._ping_mongo()
            self._is_initialized = True
            self.stub_mode = False
            logger.info(f"MongoDB connection pool initialized [DB: '{cfg.db_name}'].")
            return True
        except Exception as exc:
            logger.warning(
                f"MongoDB server not reachable at '{cfg.uri}' ({exc}). Entering offline/stub mode."
            )
            self._is_initialized = True
            self.stub_mode = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Diagnostic ping to MongoDB server."""
        if self.stub_mode or not self.client:
            return {
                "healthy": False,
                "status": "stubbed_local_dev",
                "message": f"MongoDB not connected (target: {settings.mongodb.uri})",
            }
        try:
            await self._ping_mongo()
            return {"healthy": True, "status": "online", "database": settings.mongodb.db_name}
        except Exception as exc:
            return {"healthy": False, "status": "error", "error": str(exc)}

    def get_client(self) -> AsyncIOMotorClient | None:
        return self.client

    def get_db(self) -> AsyncIOMotorDatabase | None:
        return self.db

    def get_collection(self, collection_name: str) -> Any:
        if self.stub_mode or not self.db:
            return None
        return self.db[collection_name]

    async def close(self) -> None:
        """(`6.9 Connection Lifecycle`) Closes Motor client connections."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self._is_initialized = False
            logger.info("MongoDB connection closed.")


mongo_manager = MongoManager()
