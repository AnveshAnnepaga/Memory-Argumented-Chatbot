# File: app/database/neo4j.py
import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from app.core.config import settings
from app.core.exceptions import Neo4jException
from app.core.infrastructure import BaseInfrastructureManager
from app.core.retry import execute_with_retry

logger = logging.getLogger("app.database.neo4j")


class Neo4jManager(BaseInfrastructureManager):
    """
    (`6.4 Neo4j Manager`)
    Manages Neo4j AsyncGraphDatabase driver initialization, session management,
    transaction handling, and diagnostic connectivity verification.
    """
    def __init__(self):
        super().__init__(name="neo4j")
        self.driver: AsyncDriver | None = None
        self.stub_mode: bool = False

    @execute_with_retry(max_attempts=1, min_wait=0.2, max_wait=0.5, exceptions=(Exception,))
    async def _verify_driver(self) -> bool:
        if not self.driver:
            return False
        await asyncio.wait_for(self.driver.verify_connectivity(), timeout=1.5)
        return True

    async def initialize(self) -> bool:
        """Initializes Neo4j async driver pool."""
        cfg = settings.neo4j
        try:
            self.driver = AsyncGraphDatabase.driver(
                cfg.uri,
                auth=(getattr(cfg, "username", getattr(cfg, "user", "neo4j")), getattr(cfg, "password", "password")),
                max_connection_pool_size=getattr(cfg, "max_connection_pool_size", 50),
                connection_timeout=1.5,
            )
            await self._verify_driver()
            self._is_initialized = True
            self.stub_mode = False
            logger.info(f"Neo4j Graph Database driver initialized [URI: '{cfg.uri}'].")
            return True
        except Exception as exc:
            logger.warning(
                f"Neo4j graph server not reachable at '{cfg.uri}' ({exc}). Entering offline/stub mode."
            )
            self._is_initialized = True
            self.stub_mode = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Diagnoses Neo4j driver reachability."""
        if self.stub_mode or not self.driver:
            return {
                "healthy": False,
                "status": "stubbed_local_dev",
                "message": f"Neo4j not connected (target: {settings.neo4j.uri})",
            }
        try:
            await self._verify_driver()
            return {"healthy": True, "status": "online", "target": settings.neo4j.uri}
        except Exception as exc:
            return {"healthy": False, "status": "error", "error": str(exc)}

    def get_client(self) -> AsyncDriver | None:
        return self.driver

    def get_driver(self) -> AsyncDriver | None:
        return self.driver

    async def get_session(self, database: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
        """Yields an async graph session for Cypher query execution."""
        if self.stub_mode or not self.driver:
            yield None
            return
        async with self.driver.session(database=database or settings.neo4j.database) as session:
            yield session

    @execute_with_retry(max_attempts=3, min_wait=1.0, max_wait=5.0, exceptions=(Exception,))
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Executes Cypher queries inside a managed transaction with retry logic (`6.8 Retry Policy`)."""
        if self.stub_mode or not self.driver:
            raise Neo4jException("Cannot execute query: Neo4j is in offline/stub mode.")
        async with self.driver.session(database=settings.neo4j.database) as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    async def close(self) -> None:
        """(`6.9 Connection Lifecycle`) Closes driver connection pools."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            self._is_initialized = False
            logger.info("Neo4j driver closed.")


neo4j_manager = Neo4jManager()
