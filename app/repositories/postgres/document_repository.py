# File: app/repositories/postgres/document_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgres import Base
from app.domain.knowledge import Document
from app.repositories.base import BaseRepository, log_and_handle_errors


class DocumentTable(Base):
    """
    (`Milestone 8 Knowledge Repository`)
    SQLAlchemy table mapping clean, processed documents stored as the single source of truth in PostgreSQL.
    """
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True)
    title = Column(String(512), nullable=False)
    url = Column(String(2048), nullable=False, index=True)
    category = Column(String(128), nullable=False, index=True)
    source = Column(String(256), nullable=False, index=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    checksum = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DocumentRepository(BaseRepository[Document]):
    """
    PostgreSQL repository managing clean, versioned documents produced by the Ingestion Pipeline.
    Responsibilities: Store clean document, Versioning queries, Checksum lookup, Find by URL.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=Document, repository_name="DocumentRepository")
        self.session = session
        self._memory_store: Dict[str, Document] = {}

    def _is_stub(self) -> bool:
        return self.session is None

    def _to_domain(self, row: DocumentTable) -> Document:
        meta = dict(row.metadata_json or {})
        meta.update({
            "url": row.url,
            "category": row.category,
            "source": row.source,
            "version": row.version,
            "checksum": row.checksum,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        })
        return Document(
            id=row.id,
            source_id=row.source,
            title=row.title,
            content=row.content,
            metadata=meta,
            created_at=row.created_at or datetime.now(timezone.utc),
        )

    def _to_table(self, entity: Document) -> DocumentTable:
        meta = dict(entity.metadata)
        url = str(meta.get("url", ""))
        category = str(meta.get("category", "general"))
        source = str(meta.get("source", entity.source_id or "unknown"))
        version = int(meta.get("version", 1))
        checksum = str(meta.get("checksum", ""))

        clean_meta = {k: v for k, v in meta.items() if k not in ("url", "category", "source", "version", "checksum", "updated_at")}
        return DocumentTable(
            id=entity.id,
            title=entity.title,
            url=url,
            category=category,
            source=source,
            content=entity.content,
            metadata_json=clean_meta,
            version=version,
            checksum=checksum,
            created_at=entity.created_at,
            updated_at=datetime.now(timezone.utc),
        )

    @log_and_handle_errors("find_by_url")
    async def find_by_url(self, url: str) -> Optional[Document]:
        """Find the latest version of a document by URL."""
        if self._is_stub():
            matches = [d for d in self._memory_store.values() if d.metadata.get("url") == url]
            if not matches:
                return None
            matches.sort(key=lambda x: int(x.metadata.get("version", 1)), reverse=True)
            return matches[0]

        stmt = select(DocumentTable).where(DocumentTable.url == url).order_by(DocumentTable.version.desc()).limit(1)
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        return self._to_domain(row) if row else None

    @log_and_handle_errors("find_by_checksum")
    async def find_by_checksum(self, checksum: str) -> Optional[Document]:
        """Check if a document with exact checksum already exists (`Duplicate Check`)."""
        if self._is_stub():
            matches = [d for d in self._memory_store.values() if d.metadata.get("checksum") == checksum]
            return matches[0] if matches else None

        stmt = select(DocumentTable).where(DocumentTable.checksum == checksum).limit(1)
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        return self._to_domain(row) if row else None

    @log_and_handle_errors("create")
    async def create(self, entity: Document) -> Document:
        if self._is_stub():
            self._memory_store[entity.id] = entity
            return entity

        row = self._to_table(entity)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[Document]:
        if self._is_stub():
            return self._memory_store.get(entity_id)

        row = await self.session.get(DocumentTable, entity_id)
        return self._to_domain(row) if row else None

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Document]:
        existing = await self.retrieve(entity_id)
        if not existing:
            return None

        dump = existing.model_dump()
        dump.update(data)
        updated = Document.model_validate(dump)

        if self._is_stub():
            self._memory_store[entity_id] = updated
            return updated

        row = await self.session.get(DocumentTable, entity_id)
        if row:
            for k, v in data.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            await self.session.commit()
            await self.session.refresh(row)
            return self._to_domain(row)
        return None

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        if self._is_stub():
            return self._memory_store.pop(entity_id, None) is not None

        row = await self.session.get(DocumentTable, entity_id)
        if row:
            await self.session.delete(row)
            await self.session.commit()
            return True
        return False

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        if self._is_stub():
            items = list(self._memory_store.values())
            if filters and "source" in filters:
                items = [i for i in items if i.metadata.get("source") == filters["source"]]
            return items[skip : skip + limit]

        stmt = select(DocumentTable)
        if filters and "source" in filters:
            stmt = stmt.where(DocumentTable.source == filters["source"])
        stmt = stmt.offset(skip).limit(limit)
        res = await self.session.execute(stmt)
        return [self._to_domain(r) for r in res.scalars().all()]

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(await self.list(skip=0, limit=10000, filters=filters))
