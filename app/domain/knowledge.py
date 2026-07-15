# File: app/domain/knowledge.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(BaseModel):
    """Domain model representing a complete ingested document (`7.4 Knowledge Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: Optional[str] = None
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


class Chunk(BaseModel):
    """Domain model representing a text chunk extracted from a document (`7.4 Knowledge Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    chunk_index: int
    text_content: str
    token_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeVector(BaseModel):
    """Domain model representing an embedding vector in Pinecone (`7.4 Vector / Knowledge Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    chunk_id: Optional[str] = None
    values: List[float] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    namespace: Optional[str] = None
    score: Optional[float] = None  # Similarity search score when retrieved


class SemanticMemoryVector(BaseModel):
    """Domain model representing a semantic vector memory item (`7.4 Semantic Memory Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    memory_text: str
    values: List[float] = Field(default_factory=list)
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
