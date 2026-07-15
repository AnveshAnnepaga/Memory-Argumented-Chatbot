# File: app/repositories/postgres/profile_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, DateTime, JSON, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import RepositoryNotFoundException
from app.database.postgres import Base, postgres_manager
from app.domain.user import UserProfile
from app.repositories.base import BaseRepository, log_and_handle_errors


class UserProfileTable(Base):
    """SQLAlchemy ORM table definition for user profiles (`7.2 User Profile Repository`)."""
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    preferences = Column(JSON, default=dict, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class UserProfileRepository(BaseRepository[UserProfile]):
    """
    (`7.2 User Profile Repository`)
    Manages user preferences, UI customization, and avatar metadata in PostgreSQL.
    Responsibilities: Store preferences, Update profile, Retrieve profile.
    """
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=UserProfile, repository_name="UserProfileRepository")
        self.session = session
        self._memory_store: Dict[str, UserProfile] = {}

    def _is_stub(self) -> bool:
        return self.session is None and (postgres_manager.stub_mode or postgres_manager.session_factory is None)

    @log_and_handle_errors("create")
    async def create(self, entity: UserProfile, session: Optional[AsyncSession] = None) -> UserProfile:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            self._memory_store[entity.user_id] = entity
            return entity

        row = UserProfileTable(
            user_id=entity.user_id,
            full_name=entity.full_name,
            avatar_url=entity.avatar_url,
            preferences=entity.preferences,
            updated_at=entity.updated_at,
        )
        active_session.add(row)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row) or entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str, session: Optional[AsyncSession] = None) -> Optional[UserProfile]:
        """Retrieve user profile by user_id."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.get(entity_id)

        stmt = select(UserProfileTable).where(UserProfileTable.user_id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[UserProfile]:
        """Update profile and store preferences (`Store preferences`, `Update profile`)."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"UserProfile for user '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated_dict["updated_at"] = datetime.now(timezone.utc)
            updated_profile = UserProfile.model_validate(updated_dict)
            self._memory_store[entity_id] = updated_profile
            return updated_profile

        stmt = select(UserProfileTable).where(UserProfileTable.user_id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise RepositoryNotFoundException(f"UserProfile for user '{entity_id}' not found in database.")

        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("store_preferences")
    async def store_preferences(self, user_id: str, preferences: Dict[str, Any], session: Optional[AsyncSession] = None) -> UserProfile:
        """Convenience method to store or merge preferences dictionary for a user."""
        profile = await self.retrieve(user_id, session=session)
        if not profile:
            profile = UserProfile(user_id=user_id, preferences=preferences)
            return await self.create(profile, session=session)
        merged = dict(profile.preferences)
        merged.update(preferences)
        updated = await self.update(user_id, {"preferences": merged}, session=session)
        return updated or profile

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.pop(entity_id, None) is not None

        stmt = select(UserProfileTable).where(UserProfileTable.user_id == entity_id)
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
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> List[UserProfile]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            items = list(self._memory_store.values())
            return items[skip : skip + limit]

        stmt = select(UserProfileTable).offset(skip).limit(limit)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> int:
        if self._is_stub() or not (session or self.session):
            return len(self._memory_store)
        return len(await self.list(skip=0, limit=10000, filters=filters, session=session))
