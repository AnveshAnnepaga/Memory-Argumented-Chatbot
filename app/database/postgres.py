# File: app/database/postgres.py
import asyncio
import logging
import sys
from typing import Any, AsyncGenerator, Dict

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.core.infrastructure import BaseInfrastructureManager
from app.core.retry import execute_with_retry

logger = logging.getLogger("app.database.postgres")


class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base class for all PostgreSQL ORM models."""
    pass


class PostgresManager(BaseInfrastructureManager):
    """
    (`6.1 PostgreSQL Manager`)
    Manages SQLAlchemy async engine connection pooling, session lifecycle,
    and health diagnostic pings for PostgreSQL relational database.
    """
    def __init__(self):
        super().__init__(name="postgres")
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.stub_mode: bool = False

    @execute_with_retry(max_attempts=1, min_wait=0.2, max_wait=0.5, exceptions=(Exception,))
    async def _ping_db(self) -> bool:
        if not self.engine:
            return False
        async with self.engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=1.5)
        return True

    async def initialize(self) -> bool:
        """Initializes connection pool (`engine`) and `session_factory`."""
        db_cfg = settings.postgres
        # Ensure async driver prefix for psycopg3
        url = db_cfg.async_url
        if url.startswith("postgresql+psycopg://"):
            url = url.replace("postgresql+psycopg://", "postgresql+psycopg_async://", 1)

        try:
            self.engine = create_async_engine(
                url,
                pool_size=db_cfg.pool_size,
                echo=db_cfg.echo,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 2} if "psycopg" in url else {},
            )
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            await self._ping_db()
            try:
                from app.repositories.postgres.user_repository import UserTable
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("PostgreSQL database tables verified/created via metadata.create_all.")
            except Exception as table_exc:
                logger.warning(f"Could not verify/create tables ({table_exc})")
            self._is_initialized = True
            self.stub_mode = False
            logger.info("PostgreSQL connection pool initialized and verified.")
            return True
        except Exception as exc:
            logger.warning(
                f"PostgreSQL server not reachable at '{db_cfg.host}:{db_cfg.port}' during startup ({exc}). Entering offline/stub mode."
            )
            self._is_initialized = True
            self.stub_mode = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Verifies connection pool vitality via SELECT 1."""
        if self.stub_mode or not self.engine:
            return {
                "healthy": False,
                "status": "stubbed_local_dev",
                "message": f"PostgreSQL not connected (target: {settings.postgres.host}:{settings.postgres.port})",
            }
        try:
            await self._ping_db()
            return {"healthy": True, "status": "online", "pool_size": settings.postgres.pool_size}
        except Exception as exc:
            return {"healthy": False, "status": "error", "error": str(exc)}

    def get_client(self) -> AsyncEngine | None:
        return self.engine

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency generator yielding transactional AsyncSession objects."""
        if self.stub_mode or not self.session_factory:
            # Yield None or raise when db operations are actually attempted while offline
            yield None
            return
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as exc:
                await session.rollback()
                raise DatabaseException(f"Transaction failure: {exc}") from exc
            finally:
                await session.close()

    async def close(self) -> None:
        """(`6.9 Connection Lifecycle`) Gracefully disposes engine connection pool."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self._is_initialized = False
            logger.info("PostgreSQL connection pool closed.")


postgres_manager = PostgresManager()
