# File: app/repositories/postgres/configuration_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, DateTime, JSON, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import RepositoryNotFoundException
from app.database.postgres import Base, postgres_manager
from app.domain.user import ConfigurationItem
from app.repositories.base import BaseRepository, log_and_handle_errors


class ConfigurationItemTable(Base):
    """SQLAlchemy ORM table definition for dynamic system runtime configurations (`7.2 Configuration Repository`)."""
    __tablename__ = "system_configurations"

    key = Column(String, primary_key=True, index=True)
    value = Column(JSON, nullable=False)
    description = Column(String, nullable=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ConfigurationRepository(BaseRepository[ConfigurationItem]):
    """
    (`7.2 Configuration Repository`)
    Manages dynamic runtime feature flags and application thresholds stored in PostgreSQL.
    Responsibilities: Read configuration, Update runtime configuration.
    """
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=ConfigurationItem, repository_name="ConfigurationRepository")
        self.session = session
        self._memory_store: Dict[str, ConfigurationItem] = {}

    def _is_stub(self) -> bool:
        return self.session is None and (postgres_manager.stub_mode or postgres_manager.session_factory is None)

    @log_and_handle_errors("read_configuration")
    async def read_configuration(self, key: str, session: Optional[AsyncSession] = None) -> Optional[ConfigurationItem]:
        """Read configuration by key (`Read configuration`)."""
        return await self.retrieve(key, session=session)

    @log_and_handle_errors("update_runtime_configuration")
    async def update_runtime_configuration(self, key: str, value: Any, description: Optional[str] = None, session: Optional[AsyncSession] = None) -> ConfigurationItem:
        """Update runtime configuration (`Update runtime configuration`). Creates if missing."""
        existing = await self.retrieve(key, session=session)
        if not existing:
            new_item = ConfigurationItem(key=key, value=value, description=description)
            return await self.create(new_item, session=session)
        updated = await self.update(key, {"value": value, "description": description or existing.description}, session=session)
        return updated or existing

    @log_and_handle_errors("create")
    async def create(self, entity: ConfigurationItem, session: Optional[AsyncSession] = None) -> ConfigurationItem:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            self._memory_store[entity.key] = entity
            return entity

        row = ConfigurationItemTable(
            key=entity.key,
            value=entity.value,
            description=entity.description,
            is_sensitive=entity.is_sensitive,
            updated_at=entity.updated_at,
        )
        active_session.add(row)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row) or entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str, session: Optional[AsyncSession] = None) -> Optional[ConfigurationItem]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.get(entity_id)

        stmt = select(ConfigurationItemTable).where(ConfigurationItemTable.key == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[ConfigurationItem]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"ConfigurationItem '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated_dict["updated_at"] = datetime.now(timezone.utc)
            updated_item = ConfigurationItem.model_validate(updated_dict)
            self._memory_store[entity_id] = updated_item
            return updated_item

        stmt = select(ConfigurationItemTable).where(ConfigurationItemTable.key == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise RepositoryNotFoundException(f"ConfigurationItem '{entity_id}' not found in database.")

        for k, v in data.items():
            if hasattr(row, k):
                setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.pop(entity_id, None) is not None

        stmt = select(ConfigurationItemTable).where(ConfigurationItemTable.key == entity_id)
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
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> List[ConfigurationItem]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            items = list(self._memory_store.values())
            return items[skip : skip + limit]

        stmt = select(ConfigurationItemTable).offset(skip).limit(limit)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> int:
        if self._is_stub() or not (session or self.session):
            return len(self._memory_store)
        return len(await self.list(skip=0, limit=10000, filters=filters, session=session))
