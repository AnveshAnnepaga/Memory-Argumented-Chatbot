# File: app/repositories/postgres/knowledge_source_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, DateTime, JSON, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import RepositoryNotFoundException
from app.database.postgres import Base, postgres_manager
from app.domain.user import KnowledgeSource
from app.repositories.base import BaseRepository, log_and_handle_errors


class KnowledgeSourceTable(Base):
    """SQLAlchemy ORM table definition for ingested knowledge sources (`7.2 Knowledge Source Repository`)."""
    __tablename__ = "knowledge_sources"

    id = Column(String, primary_key=True, index=True)
    source_type = Column(String, index=True, nullable=False)
    uri = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    crawl_history = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class KnowledgeSourceRepository(BaseRepository[KnowledgeSource]):
    """
    (`7.2 Knowledge Source Repository`)
    Manages external document crawl roots, status tracking, and metadata in PostgreSQL.
    Responsibilities: Register source, Update crawl status, Track crawl history.
    """
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=KnowledgeSource, repository_name="KnowledgeSourceRepository")
        self.session = session
        self._memory_store: Dict[str, KnowledgeSource] = self._load_mock_data()

    def _is_stub(self) -> bool:
        return self.session is None and (postgres_manager.stub_mode or postgres_manager.session_factory is None)

    @log_and_handle_errors("register_source")
    async def register_source(self, entity: KnowledgeSource, session: Optional[AsyncSession] = None) -> KnowledgeSource:
        """Register source (`Register source`)."""
        return await self.create(entity, session=session)

    @log_and_handle_errors("create")
    async def create(self, entity: KnowledgeSource, session: Optional[AsyncSession] = None) -> KnowledgeSource:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            self._memory_store[entity.id] = entity
            self._save_mock_data(self._memory_store)
            return entity

        row = KnowledgeSourceTable(
            id=entity.id,
            source_type=entity.source_type,
            uri=entity.uri,
            name=entity.name,
            status=entity.status,
            crawl_history=entity.crawl_history,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        active_session.add(row)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row) or entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str, session: Optional[AsyncSession] = None) -> Optional[KnowledgeSource]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.get(entity_id)

        stmt = select(KnowledgeSourceTable).where(KnowledgeSourceTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[KnowledgeSource]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"KnowledgeSource '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated_dict["updated_at"] = datetime.now(timezone.utc)
            updated_source = KnowledgeSource.model_validate(updated_dict)
            self._memory_store[entity_id] = updated_source
            self._save_mock_data(self._memory_store)
            return updated_source

        stmt = select(KnowledgeSourceTable).where(KnowledgeSourceTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise RepositoryNotFoundException(f"KnowledgeSource '{entity_id}' not found in database.")

        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("update_crawl_status")
    async def update_crawl_status(self, source_id: str, status: str, session: Optional[AsyncSession] = None) -> Optional[KnowledgeSource]:
        """Update crawl status (`Update crawl status`)."""
        return await self.update(source_id, {"status": status}, session=session)

    @log_and_handle_errors("track_crawl_history")
    async def track_crawl_history(self, source_id: str, history_entry: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[KnowledgeSource]:
        """Append entry to crawl history (`Track crawl history`)."""
        source = await self.retrieve(source_id, session=session)
        if not source:
            raise RepositoryNotFoundException(f"KnowledgeSource '{source_id}' not found.")
        history = list(source.crawl_history)
        history_entry["timestamp"] = history_entry.get("timestamp", datetime.now(timezone.utc).isoformat())
        history.append(history_entry)
        return await self.update(source_id, {"crawl_history": history}, session=session)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            popped = self._memory_store.pop(entity_id, None)
            if popped:
                self._save_mock_data(self._memory_store)
            return popped is not None

        stmt = select(KnowledgeSourceTable).where(KnowledgeSourceTable.id == entity_id)
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
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> List[KnowledgeSource]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            items = list(self._memory_store.values())
            return items[skip : skip + limit]

        stmt = select(KnowledgeSourceTable).offset(skip).limit(limit)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> int:
        if self._is_stub() or not (session or self.session):
            return len(self._memory_store)
        return len(await self.list(skip=0, limit=10000, filters=filters, session=session))
