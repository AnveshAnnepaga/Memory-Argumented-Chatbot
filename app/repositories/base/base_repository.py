# File: app/repositories/base/base_repository.py
import functools
import logging
import time
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from app.core.exceptions import (
    DatabaseException,
    Neo4jException,
    PineconeException,
    RepositoryException,
    RepositoryNotFoundException,
)
from app.repositories.base.interfaces import ICrudRepository, T

logger = logging.getLogger("app.repositories.base")


class PaginatedResult(BaseModel, Generic[T]):
    """Standard pagination container returning items and total count (`7.1 Base Repository`)."""
    items: List[T]
    total: int
    skip: int
    limit: int


def log_and_handle_errors(operation_name: str):
    """
    (`Repository Error Handling` & `Repository Logging`)
    Decorator ensuring every repository operation logs timing and outcome while automatically
    translating low-level driver exceptions into clean repository exceptions.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            repo_name = getattr(self, "repository_name", self.__class__.__name__)
            start_time = time.perf_counter()
            try:
                result = await func(self, *args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.debug(
                    f"[REPO LOG] Operation: {operation_name} | Repository: {repo_name} | "
                    f"ExecutionTime: {duration_ms:.2f}ms | Status: SUCCESS"
                )
                return result
            except (RepositoryException, RepositoryNotFoundException) as repo_exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.warning(
                    f"[REPO LOG] Operation: {operation_name} | Repository: {repo_name} | "
                    f"ExecutionTime: {duration_ms:.2f}ms | Status: FAILURE | Error: {repo_exc.message}"
                )
                raise
            except (DatabaseException, PineconeException, Neo4jException) as infra_exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.error(
                    f"[REPO LOG] Operation: {operation_name} | Repository: {repo_name} | "
                    f"ExecutionTime: {duration_ms:.2f}ms | Status: FAILURE | InfraError: {infra_exc.message}"
                )
                raise RepositoryException(
                    message=f"Database infrastructure failure during '{operation_name}' on {repo_name}: {infra_exc.message}",
                    details={"operation": operation_name, "repository": repo_name, "original_error": str(infra_exc)},
                ) from infra_exc
            except Exception as raw_exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.error(
                    f"[REPO LOG] Operation: {operation_name} | Repository: {repo_name} | "
                    f"ExecutionTime: {duration_ms:.2f}ms | Status: FAILURE | RawError: {raw_exc}",
                    exc_info=True,
                )
                raise RepositoryException(
                    message=f"Repository error during '{operation_name}' on {repo_name}: {str(raw_exc)}",
                    details={"operation": operation_name, "repository": repo_name, "raw_exception": str(raw_exc)},
                ) from raw_exc
        return wrapper
    return decorator


class BaseRepository(ICrudRepository[T]):
    """
    (`7.1 Base Repository`)
    Abstract implementation base class providing standard logging hooks, error handling,
    domain model mapping helpers, and pagination utilities for all database repositories.
    """
    def __init__(self, domain_model_class: type[T], repository_name: Optional[str] = None):
        self.domain_model_class = domain_model_class
        self.repository_name = repository_name or self.__class__.__name__

    def _to_domain(self, raw_data: Any) -> Optional[T]:
        """Safely maps ORM models, MongoDB dicts, or Graph records to the domain model (`DDD Improvement ⭐`)."""
        if raw_data is None:
            return None
        if isinstance(raw_data, self.domain_model_class):
            return raw_data
        if isinstance(raw_data, dict):
            # Clean up MongoDB '_id' or Neo4j internal IDs if present alongside 'id'
            cleaned = dict(raw_data)
            if "_id" in cleaned and "id" not in cleaned:
                cleaned["id"] = str(cleaned.pop("_id"))
            return self.domain_model_class.model_validate(cleaned)
        return self.domain_model_class.model_validate(raw_data)

    def _to_domain_list(self, raw_list: List[Any]) -> List[T]:
        """Maps a list of raw database records to domain models."""
        items = []
        for row in raw_list:
            domain_item = self._to_domain(row)
            if domain_item:
                items.append(domain_item)
        return items

    def paginate(self, items: List[T], total: int, skip: int, limit: int) -> PaginatedResult[T]:
        """Helper to wrap results in standard PaginatedResult container."""
        return PaginatedResult(items=items, total=total, skip=skip, limit=limit)
