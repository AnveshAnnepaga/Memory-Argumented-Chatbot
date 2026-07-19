import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgres import Base
from app.domain.knowledge import DocumentFile
from app.repositories.base import BaseRepository, log_and_handle_errors

logger = logging.getLogger("app.repositories.postgres.document_file")


class DocumentFileTable(Base):
    """SQLAlchemy table mapping uploaded file BLOBs stored in PostgreSQL."""
    __tablename__ = "document_files"

    id = Column(String(64), primary_key=True)
    filename = Column(String(512), nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    file_hash = Column(String(64), nullable=False, index=True)
    blob_data = Column(LargeBinary, nullable=True)
    extracted_text = Column(Text, nullable=True)
    document_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class DocumentFileRepository(BaseRepository[DocumentFile]):
    """PostgreSQL repository for uploaded file BLOBs."""

    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=DocumentFile, repository_name="DocumentFileRepository")
        self.session = session
        self._memory_store: Dict[str, DocumentFile] = self._load_mock_data()

    def _is_stub(self) -> bool:
        return self.session is None

    def _to_domain(self, row: DocumentFileTable) -> DocumentFile:
        return DocumentFile(
            id=row.id,
            filename=row.filename,
            mime_type=row.mime_type,
            size_bytes=row.size_bytes,
            file_hash=row.file_hash,
            blob_data=row.blob_data,
            extracted_text=row.extracted_text,
            document_id=row.document_id,
            created_at=row.created_at or datetime.now(timezone.utc),
        )

    def _to_table(self, entity: DocumentFile) -> DocumentFileTable:
        return DocumentFileTable(
            id=entity.id,
            filename=entity.filename,
            mime_type=entity.mime_type,
            size_bytes=entity.size_bytes,
            file_hash=entity.file_hash,
            blob_data=entity.blob_data,
            extracted_text=entity.extracted_text,
            document_id=entity.document_id,
            created_at=entity.created_at,
        )

    @log_and_handle_errors("compute_file_hash")
    async def compute_file_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @log_and_handle_errors("save")
    async def save(self, entity: DocumentFile) -> DocumentFile:
        if self._is_stub():
            self._memory_store[entity.id] = entity
            self._save_mock_data(self._memory_store)
            return entity
        row = self._to_table(entity)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("get")
    async def get(self, file_id: str) -> Optional[DocumentFile]:
        if self._is_stub():
            return self._memory_store.get(file_id)
        row = await self.session.get(DocumentFileTable, file_id)
        return self._to_domain(row) if row else None

    @log_and_handle_errors("delete")
    async def delete(self, file_id: str) -> bool:
        if self._is_stub():
            popped = self._memory_store.pop(file_id, None)
            if popped:
                self._save_mock_data(self._memory_store)
            return popped is not None
        row = await self.session.get(DocumentFileTable, file_id)
        if row:
            await self.session.delete(row)
            await self.session.commit()
            return True
        return False

    @log_and_handle_errors("find_by_hash")
    async def find_by_hash(self, file_hash: str) -> Optional[DocumentFile]:
        if self._is_stub():
            for f in self._memory_store.values():
                if f.file_hash == file_hash:
                    return f
            return None
        stmt = select(DocumentFileTable).where(DocumentFileTable.file_hash == file_hash).limit(1)
        res = await self.session.execute(stmt)
        row = res.scalar_one_or_none()
        return self._to_domain(row) if row else None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[DocumentFile]:
        if self._is_stub():
            items = list(self._memory_store.values())
            if filters:
                for key, value in filters.items():
                    items = [i for i in items if getattr(i, key, None) == value]
            return items[skip : skip + limit]
        stmt = select(DocumentFileTable)
        if filters:
            for key, value in filters.items():
                if hasattr(DocumentFileTable, key):
                    stmt = stmt.where(getattr(DocumentFileTable, key) == value)
        stmt = stmt.offset(skip).limit(limit).order_by(DocumentFileTable.created_at.desc())
        res = await self.session.execute(stmt)
        return [self._to_domain(r) for r in res.scalars().all()]

    @log_and_handle_errors("update_document_id")
    async def update_document_id(self, file_id: str, document_id: str) -> Optional[DocumentFile]:
        if self._is_stub():
            f = self._memory_store.get(file_id)
            if f:
                f.document_id = document_id
                self._save_mock_data(self._memory_store)
            return f
        row = await self.session.get(DocumentFileTable, file_id)
        if row:
            row.document_id = document_id
            await self.session.commit()
            await self.session.refresh(row)
            return self._to_domain(row)
        return None

    @log_and_handle_errors("create")
    async def create(self, entity: DocumentFile) -> DocumentFile:
        return await self.save(entity)

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[DocumentFile]:
        return await self.get(entity_id)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[DocumentFile]:
        existing = await self.get(entity_id)
        if not existing:
            return None
        dump = existing.model_dump()
        dump.update(data)
        updated = DocumentFile.model_validate(dump)
        if self._is_stub():
            self._memory_store[entity_id] = updated
            self._save_mock_data(self._memory_store)
            return updated
        row = await self.session.get(DocumentFileTable, entity_id)
        if row:
            for k, v in data.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            await self.session.commit()
            await self.session.refresh(row)
            return self._to_domain(row)
        return None

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.get(entity_id)) is not None

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        if self._is_stub():
            items = list(self._memory_store.values())
            if filters:
                for key, value in filters.items():
                    items = [i for i in items if getattr(i, key, None) == value]
            return len(items)
        stmt = select(func.count(DocumentFileTable.id))
        if filters:
            for key, value in filters.items():
                if hasattr(DocumentFileTable, key):
                    stmt = stmt.where(getattr(DocumentFileTable, key) == value)
        res = await self.session.execute(stmt)
        return res.scalar() or 0
