# File: app/repositories/base/interfaces.py
import abc
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class IRepository(Generic[T], abc.ABC):
    """
    (`7.1 Base Repository` / `Standard Repository Interface`)
    Top-level contract ensuring every repository exposes consistent, type-safe operations
    and returns schema-agnostic Domain Models instead of raw database drivers or dicts.
    """
    pass


class ICrudRepository(IRepository[T]):
    """Standard CRUD contract for structured database repositories (`Create, Retrieve, Update, Delete, Exists, List, Count`)."""

    @abc.abstractmethod
    async def create(self, entity: T) -> T:
        """Persists a new domain entity."""
        pass

    @abc.abstractmethod
    async def retrieve(self, entity_id: str) -> Optional[T]:
        """Retrieves a domain entity by its primary ID."""
        pass

    @abc.abstractmethod
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[T]:
        """Updates attributes of an existing domain entity."""
        pass

    @abc.abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Deletes a domain entity by ID. Returns True if deleted, False if not found."""
        pass

    @abc.abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """Checks whether an entity exists without loading its full payload."""
        pass

    @abc.abstractmethod
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Returns a paginated list of domain entities."""
        pass

    @abc.abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Counts the total number of entities matching criteria."""
        pass


class ISearchRepository(IRepository[T]):
    """Contract for semantic similarity search or complex query filtering (`Search`)."""

    @abc.abstractmethod
    async def search(self, query: Any, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Executes a similarity search or full-text/graph search and returns ranked domain entities."""
        pass
