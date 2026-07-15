# File: app/domain/__init__.py
"""
Domain Model Layer (`Milestone 7` Domain-Driven Design Improvement ⭐)
Defines clean, schema-agnostic domain objects returned by repositories.
Keeps the service and business logic independent of underlying SQL/NoSQL schemas.
"""
from app.domain.user import (
    User,
    UserProfile,
    Session,
    KnowledgeSource,
    EvaluationResult,
    ConfigurationItem,
)
from app.domain.conversation import (
    Conversation,
    Message,
    MemorySnapshot,
    ToolExecutionHistory,
    RouterDecisionHistory,
    PromptHistoryItem,
)
from app.domain.knowledge import (
    Document,
    Chunk,
    KnowledgeVector,
    SemanticMemoryVector,
)
from app.domain.graph import (
    GraphNode,
    GraphRelationship,
    Entity,
    Relationship,
)

__all__ = [
    "User",
    "UserProfile",
    "Session",
    "KnowledgeSource",
    "EvaluationResult",
    "ConfigurationItem",
    "Conversation",
    "Message",
    "MemorySnapshot",
    "ToolExecutionHistory",
    "RouterDecisionHistory",
    "PromptHistoryItem",
    "Document",
    "Chunk",
    "KnowledgeVector",
    "SemanticMemoryVector",
    "GraphNode",
    "GraphRelationship",
    "Entity",
    "Relationship",
]
