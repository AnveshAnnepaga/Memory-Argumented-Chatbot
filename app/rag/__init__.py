# File: app/rag/__init__.py
"""
Milestone 9 — Hybrid RAG Pipeline.
Responsible for converting raw documents into a searchable semantic knowledge base:
Chunking -> Embedding Generation (BAAI/bge-large-en-v1.5) -> Pinecone Vector Store + BM25 ->
Retrieval Fusion Engine -> Cross-Encoder Reranker -> Context Builder -> Ready for LangGraph.
"""
from app.rag.schemas import (
    ChunkSchema,
    EmbeddingVector,
    RetrievedChunk,
    RAGContext,
)
from app.rag.chunker import SemanticRecursiveChunker, chunker
from app.rag.embedder import BGEEmbedder, embedder
from app.rag.vector_store import PineconeVectorStore, vector_store
from app.rag.retriever import (
    BM25SparseRetriever,
    RetrievalFusionEngine,
    CrossEncoderReranker,
    HybridRetriever,
    sparse_retriever,
    fusion_engine,
    reranker,
    hybrid_retriever,
)
from app.rag.context_builder import ContextBuilder, context_builder
from app.rag.pipeline import RAGPipeline, rag_pipeline

__all__ = [
    "ChunkSchema",
    "EmbeddingVector",
    "RetrievedChunk",
    "RAGContext",
    "SemanticRecursiveChunker",
    "chunker",
    "BGEEmbedder",
    "embedder",
    "PineconeVectorStore",
    "vector_store",
    "BM25SparseRetriever",
    "RetrievalFusionEngine",
    "CrossEncoderReranker",
    "HybridRetriever",
    "sparse_retriever",
    "fusion_engine",
    "reranker",
    "hybrid_retriever",
    "ContextBuilder",
    "context_builder",
    "RAGPipeline",
    "rag_pipeline",
]
