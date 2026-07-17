# File: app/repositories/__init__.py
"""
Centralized Repository Layer (`Milestone 7 Repository Layer`).
Exposes Base, PostgreSQL, MongoDB, Pinecone, and Neo4j repositories cleanly to services.
"""
from app.repositories.base import (
    IRepository,
    ICrudRepository,
    ISearchRepository,
    BaseRepository,
    PaginatedResult,
    log_and_handle_errors,
)
from app.repositories.postgres import (
    UserRepository,
    UserTable,
    UserProfileRepository,
    UserProfileTable,
    SessionRepository,
    SessionTable,
    KnowledgeSourceRepository,
    KnowledgeSourceTable,
    EvaluationRepository,
    EvaluationResultTable,
    ConfigurationRepository,
    ConfigurationItemTable,
    DocumentRepository,
    DocumentTable,
    DocumentFileRepository,
    DocumentFileTable,
)
from app.repositories.mongodb import (
    ConversationRepository,
    MessageRepository,
    MemorySnapshotRepository,
    ToolHistoryRepository,
    RouterHistoryRepository,
    PromptHistoryRepository,
)
from app.repositories.pinecone import (
    VectorRepository,
    KnowledgeRepository,
    SemanticMemoryRepository,
)
from app.repositories.neo4j import (
    GraphRepository,
    EntityRepository,
    RelationshipRepository,
)

__all__ = [
    # Base
    "IRepository",
    "ICrudRepository",
    "ISearchRepository",
    "BaseRepository",
    "PaginatedResult",
    "log_and_handle_errors",
    # PostgreSQL
    "UserRepository",
    "UserTable",
    "UserProfileRepository",
    "UserProfileTable",
    "SessionRepository",
    "SessionTable",
    "KnowledgeSourceRepository",
    "KnowledgeSourceTable",
    "EvaluationRepository",
    "EvaluationResultTable",
    "ConfigurationRepository",
    "ConfigurationItemTable",
    "DocumentRepository",
    "DocumentTable",
    "DocumentFileRepository",
    "DocumentFileTable",
    # MongoDB
    "ConversationRepository",
    "MessageRepository",
    "MemorySnapshotRepository",
    "ToolHistoryRepository",
    "RouterHistoryRepository",
    "PromptHistoryRepository",
    # Pinecone
    "VectorRepository",
    "KnowledgeRepository",
    "SemanticMemoryRepository",
    # Neo4j
    "GraphRepository",
    "EntityRepository",
    "RelationshipRepository",
]
