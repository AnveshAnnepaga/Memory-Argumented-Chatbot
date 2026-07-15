# File: app/api/dependencies.py
import logging
from typing import Any, AsyncGenerator, Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.ai.llm.llm_manager import llm_manager, LLMProviderManager
from app.core.config import settings, Settings
from app.core.settings import FeatureFlagsConfig
from app.database.mongodb import mongo_manager
from app.database.neo4j import neo4j_manager
from app.database.pinecone import pinecone_manager
from app.database.postgres import postgres_manager

logger = logging.getLogger("app.api.dependencies")


def get_config() -> Settings:
    """Dependency provider yielding the centralized Settings object (`5.8 Dependency Injection`)."""
    return settings


def get_feature_flags() -> FeatureFlagsConfig:
    """Dependency provider yielding active feature flags."""
    return settings.feature_flags


def get_request_id(request: Request) -> str:
    """Dependency provider extracting unique Request ID from request state or header."""
    return getattr(request.state, "request_id", "N/A")


def get_logger() -> logging.Logger:
    """Dependency provider returning application logger."""
    return logger


# --- Infrastructure & Database Dependency Injectors (`Milestone 6`) ---

async def get_postgres_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yields a managed PostgreSQL AsyncSession transaction (`6.1 PostgreSQL Manager`)."""
    async for session in postgres_manager.get_session():
        yield session


def get_mongo_db() -> Optional[AsyncIOMotorDatabase]:
    """Returns active MongoDB database handle (`6.2 MongoDB Manager`)."""
    return mongo_manager.get_db()


def get_vector_client() -> Any:
    """Returns active Pinecone client / index (`6.3 Pinecone Manager`)."""
    return pinecone_manager.get_index()


def get_graph_client() -> Any:
    """Returns active Neo4j driver (`6.4 Neo4j Manager`)."""
    return neo4j_manager.get_driver()


def get_llm_manager() -> LLMProviderManager:
    """Returns active LLM Provider Manager orchestration layer (`6.5 Groq Manager ⭐`)."""
    return llm_manager


# --- Repository Dependency Injectors (`7.6 Repository Registry & Centralized Access`) ---

from fastapi import Depends
from app.repositories import (
    UserRepository,
    UserProfileRepository,
    SessionRepository,
    KnowledgeSourceRepository,
    EvaluationRepository,
    ConfigurationRepository,
    DocumentRepository,
    ConversationRepository,
    MessageRepository,
    MemorySnapshotRepository,
    ToolHistoryRepository,
    RouterHistoryRepository,
    PromptHistoryRepository,
    VectorRepository,
    KnowledgeRepository,
    SemanticMemoryRepository,
    GraphRepository,
    EntityRepository,
    RelationshipRepository,
)


def get_user_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> UserRepository:
    return UserRepository(session=session)


def get_profile_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> UserProfileRepository:
    return UserProfileRepository(session=session)


def get_session_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> SessionRepository:
    return SessionRepository(session=session)


def get_knowledge_source_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> KnowledgeSourceRepository:
    return KnowledgeSourceRepository(session=session)


def get_evaluation_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> EvaluationRepository:
    return EvaluationRepository(session=session)


def get_configuration_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> ConfigurationRepository:
    return ConfigurationRepository(session=session)


def get_document_repository(session: Optional[AsyncSession] = Depends(get_postgres_session)) -> DocumentRepository:
    """Returns PostgreSQL DocumentRepository (`Milestone 8 Knowledge Repository`)."""
    return DocumentRepository(session=session)


def get_conversation_repository(db: Optional[AsyncIOMotorDatabase] = Depends(get_mongo_db)) -> ConversationRepository:
    return ConversationRepository(db=db)


def get_message_repository(db: Optional[AsyncIOMotorDatabase] = Depends(get_mongo_db)) -> MessageRepository:
    return MessageRepository(db=db)


def get_memory_snapshot_repository(db: Optional[AsyncIOMotorDatabase] = Depends(get_mongo_db)) -> MemorySnapshotRepository:
    return MemorySnapshotRepository(db=db)


def get_tool_history_repository(db: Optional[AsyncIOMotorDatabase] = Depends(get_mongo_db)) -> ToolHistoryRepository:
    return ToolHistoryRepository(db=db)


def get_router_history_repository(db: Optional[AsyncIOMotorDatabase] = Depends(get_mongo_db)) -> RouterHistoryRepository:
    return RouterHistoryRepository(db=db)


def get_prompt_history_repository(db: Optional[AsyncIOMotorDatabase] = Depends(get_mongo_db)) -> PromptHistoryRepository:
    return PromptHistoryRepository(db=db)


def get_vector_repository() -> VectorRepository:
    return VectorRepository()


def get_knowledge_repository() -> KnowledgeRepository:
    return KnowledgeRepository()


def get_semantic_memory_repository() -> SemanticMemoryRepository:
    return SemanticMemoryRepository()


def get_graph_repository() -> GraphRepository:
    return GraphRepository()


def get_entity_repository() -> EntityRepository:
    return EntityRepository()


def get_relationship_repository() -> RelationshipRepository:
    return RelationshipRepository()

