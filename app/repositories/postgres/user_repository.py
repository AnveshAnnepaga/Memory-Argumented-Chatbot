# File: app/repositories/postgres/user_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, DateTime, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import RepositoryNotFoundException
from app.database.postgres import Base, postgres_manager
from app.domain.user import User
from app.repositories.base import BaseRepository, log_and_handle_errors


class UserTable(Base):
    """SQLAlchemy ORM table definition for users (`7.2 User Repository`)."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_ip = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class UserRepository(BaseRepository[User]):
    """
    (`7.2 User Repository`)
    Manages structured user authentication and identity records in PostgreSQL.
    Responsibilities: Create user, Retrieve user, Update user, Delete user, Find by email, Find by username.
    """
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=User, repository_name="UserRepository")
        self.session = session
        self._memory_store: Dict[str, User] = self._load_mock_data()  # Fallback for offline/mock test execution

    def _is_stub(self) -> bool:
        return self.session is None and (postgres_manager.stub_mode or postgres_manager.session_factory is None)

    @log_and_handle_errors("create")
    async def create(self, entity: User, session: Optional[AsyncSession] = None) -> User:
        """Create user record."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            self._memory_store[entity.id] = entity
            self._save_mock_data(self._memory_store)
            return entity

        row = UserTable(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            password_hash=entity.password_hash,
            is_active=entity.is_active,
            is_superuser=entity.is_superuser,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        active_session.add(row)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row) or entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """Retrieve user by ID."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.get(entity_id)

        stmt = select(UserTable).where(UserTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[User]:
        """Update user fields."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"User '{entity_id}' not found.")
            updated_user = existing.model_copy(update=data)
            updated_user.updated_at = datetime.now(timezone.utc)
            self._memory_store[entity_id] = updated_user
            self._save_mock_data(self._memory_store)
            return updated_user

        stmt = select(UserTable).where(UserTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise RepositoryNotFoundException(f"User '{entity_id}' not found in database.")

        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        """Delete user record."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            popped = self._memory_store.pop(entity_id, None)
            if popped:
                self._save_mock_data(self._memory_store)
            return popped is not None

        stmt = select(UserTable).where(UserTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await active_session.delete(row)
        await active_session.commit()
        return True

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        """Check if user exists."""
        return (await self.retrieve(entity_id, session=session)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> List[User]:
        """List paginated users."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            items = list(self._memory_store.values())
            return items[skip : skip + limit]

        stmt = select(UserTable).offset(skip).limit(limit)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> int:
        """Count total users."""
        if self._is_stub() or not (session or self.session):
            return len(self._memory_store)
        return len(await self.list(skip=0, limit=10000, filters=filters, session=session))

    @log_and_handle_errors("find_by_email")
    async def find_by_email(self, email: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """Find user by email address."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            for u in self._memory_store.values():
                if u.email.lower() == email.lower():
                    return u
            return None

        stmt = select(UserTable).where(UserTable.email == email)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("find_by_username")
    async def find_by_username(self, username: str, session: Optional[AsyncSession] = None) -> Optional[User]:
        """Find user by username."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            for u in self._memory_store.values():
                if u.username.lower() == username.lower():
                    return u
            return None

        stmt = select(UserTable).where(UserTable.username == username)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)
