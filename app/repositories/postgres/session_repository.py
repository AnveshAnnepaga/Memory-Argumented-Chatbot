# File: app/repositories/postgres/session_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, DateTime, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import RepositoryNotFoundException
from app.database.postgres import Base, postgres_manager
from app.domain.user import Session
from app.repositories.base import BaseRepository, log_and_handle_errors


class SessionTable(Base):
    """SQLAlchemy ORM table definition for user authentication sessions (`7.2 Session Repository`)."""
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class SessionRepository(BaseRepository[Session]):
    """
    (`7.2 Session Repository`)
    Manages user sessions, tokens, and login history in PostgreSQL.
    Responsibilities: Create session, Close session, Get active sessions.
    """
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=Session, repository_name="SessionRepository")
        self.session = session
        self._memory_store: Dict[str, Session] = {}

    def _is_stub(self) -> bool:
        return self.session is None and (postgres_manager.stub_mode or postgres_manager.session_factory is None)

    @log_and_handle_errors("create")
    async def create(self, entity: Session, session: Optional[AsyncSession] = None) -> Session:
        """Create session."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            self._memory_store[entity.id] = entity
            return entity

        row = SessionTable(
            id=entity.id,
            user_id=entity.user_id,
            token=entity.token,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            is_active=entity.is_active,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
        )
        active_session.add(row)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row) or entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str, session: Optional[AsyncSession] = None) -> Optional[Session]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.get(entity_id)

        stmt = select(SessionTable).where(SessionTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[Session]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"Session '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated_session = Session.model_validate(updated_dict)
            self._memory_store[entity_id] = updated_session
            return updated_session

        stmt = select(SessionTable).where(SessionTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise RepositoryNotFoundException(f"Session '{entity_id}' not found in database.")

        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("close_session")
    async def close_session(self, session_id: str, session: Optional[AsyncSession] = None) -> bool:
        """Close session by setting is_active = False (`Close session`)."""
        updated = await self.update(session_id, {"is_active": False}, session=session)
        return updated is not None

    @log_and_handle_errors("get_active_sessions")
    async def get_active_sessions(self, user_id: str, session: Optional[AsyncSession] = None) -> List[Session]:
        """Get active sessions for a user (`Get active sessions`)."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return [
                s for s in self._memory_store.values()
                if s.user_id == user_id and s.is_active
            ]

        stmt = select(SessionTable).where(SessionTable.user_id == user_id, SessionTable.is_active == True)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.pop(entity_id, None) is not None

        stmt = select(SessionTable).where(SessionTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await active_session.delete(row)
        await active_session.commit()
        return True

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        return (await self.retrieve(entity_id, session=session)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> List[Session]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            items = list(self._memory_store.values())
            return items[skip : skip + limit]

        stmt = select(SessionTable).offset(skip).limit(limit)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> int:
        if self._is_stub() or not (session or self.session):
            return len(self._memory_store)
        return len(await self.list(skip=0, limit=10000, filters=filters, session=session))
