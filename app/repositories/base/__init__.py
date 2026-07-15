# File: app/repositories/base/__init__.py
"""
Base Repository Layer (`7.1 Base Repository`).
Provides interfaces, base classes, error translation, and logging hooks.
"""
from app.repositories.base.interfaces import (
    IRepository,
    ICrudRepository,
    ISearchRepository,
)
from app.repositories.base.base_repository import (
    BaseRepository,
    PaginatedResult,
    log_and_handle_errors,
)

__all__ = [
    "IRepository",
    "ICrudRepository",
    "ISearchRepository",
    "BaseRepository",
    "PaginatedResult",
    "log_and_handle_errors",
]
