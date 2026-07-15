# File: app/rag/schemas.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChunkSchema(BaseModel):
    """
    (`9.1 Chunker Schema`)
    Represents a semantic or recursively chunked segment of a document with inherited metadata.
    """
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str = Field(..., description="Parent document ID from Knowledge Repository")
    chunk_index: int = Field(default=0, ge=0)
    text: str = Field(..., description="Clean text segment of the chunk")
    token_count: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Inherited metadata from Document + chunk specifics (title, url, category, source)",
    )


class EmbeddingVector(BaseModel):
    """
    (`9.2 Embedder Schema`)
    Represents a generated embedding vector ready for Pinecone vector store indexing.
    """
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    values: List[float] = Field(default_factory=list, description="Vector embedding representation (e.g., 1024 dims for BAAI/bge-large-en-v1.5)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    """
    (`9.4 & 9.5 Retriever & Context Schema`)
    Represents a chunk retrieved via Hybrid Search + Retrieval Fusion Engine + Cross-Encoder Reranker.
    """
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    document_id: str
    text: str
    score: float = Field(default=0.0, description="Final fused/reranked relevance score")
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    rerank_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGContext(BaseModel):
    """
    (`9.5 Context Builder Schema`)
    Represents the clean, deduplicated, sorted context block ready for injection into LangGraph / LLM prompts.
    """
    model_config = ConfigDict(from_attributes=True)

    query: str
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    formatted_context: str = Field(default="", description="Ordered text block formatted for LLM system prompt")
    total_tokens: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=_utcnow)

    @property
    def chunks(self) -> List[RetrievedChunk]:
        """Convenience alias for retrieved_chunks."""
        return self.retrieved_chunks
