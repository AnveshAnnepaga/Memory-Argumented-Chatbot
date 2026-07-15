# File: app/tests/rag/test_rag_pipeline.py
import math
import pytest
from app.domain.knowledge import Document
from app.rag import (
    BM25SparseRetriever,
    ChunkSchema,
    ContextBuilder,
    CrossEncoderReranker,
    EmbeddingVector,
    HybridRetriever,
    PineconeVectorStore,
    RAGContext,
    RAGPipeline,
    RetrievalFusionEngine,
    RetrievedChunk,
    SemanticRecursiveChunker,
    embedder,
    hybrid_retriever,
)

# Enable fast deterministic stub mode for unit testing without downloading 1.34GB weights
embedder.use_stub = True
if hasattr(hybrid_retriever, "reranker") and hasattr(hybrid_retriever.reranker, "use_stub"):
    hybrid_retriever.reranker.use_stub = True


def test_chunker():
    """(`9.1 Chunker`) Verify recursive semantic splitting and metadata inheritance."""
    chunker = SemanticRecursiveChunker(chunk_size=15, chunk_overlap=3)
    doc = Document(
        id="doc-python-101",
        source_id="Python Docs",
        title="Python Multi-Threading Guide",
        content="The Global Interpreter Lock is a mutex that protects access to Python objects. It prevents multiple native threads from executing Python bytecodes simultaneously. Subinterpreters in modern Python provide per-interpreter locks for better concurrency.",
        metadata={"url": "https://docs.python.org/3/c-api/init.html", "category": "concurrency"},
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1
    assert chunks[0].document_id == "doc-python-101"
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata["url"] == "https://docs.python.org/3/c-api/init.html"
    assert chunks[0].metadata["document_title"] == "Python Multi-Threading Guide"
    assert chunks[0].token_count > 0
    # Verify deterministic ID generation
    assert chunks[0].chunk_id == chunker.chunk_document(doc)[0].chunk_id


def test_embedder_and_caching():
    """(`9.2 Embedder`) Verify 1024-dimensional embedding generation, normalization, and caching."""
    # Ensure fast stub mode or active model mode works consistently
    text = "Semantic vector embedding representation of knowledge."
    vec1 = embedder.embed_text(text)
    vec2 = embedder.embed_text(text)  # Should hit cache

    assert len(vec1) == 1024
    assert vec1 == vec2
    # Verify unit sphere normalization (L2 norm approx 1.0)
    l2_norm = math.sqrt(sum(v * v for v in vec1))
    assert 0.99 <= l2_norm <= 1.01

    chunk = ChunkSchema(
        chunk_id="chk-abc",
        document_id="doc-xyz",
        text=text,
        metadata={"source": "test"},
    )
    embed_vector: EmbeddingVector = embedder.embed_chunk(chunk)
    assert embed_vector.chunk_id == "chk-abc"
    assert len(embed_vector.values) == 1024
    assert embed_vector.metadata["source"] == "test"


def test_vector_store():
    """(`9.3 Vector Store`) Verify Pinecone wrapper upsert, similarity search, and deletion."""
    store = PineconeVectorStore()
    v1 = EmbeddingVector(
        chunk_id="chk-1",
        values=embedder.embed_text("FastAPI web framework for async Python APIs"),
        metadata={"document_id": "doc-fastapi", "text": "FastAPI web framework for async Python APIs"},
    )
    v2 = EmbeddingVector(
        chunk_id="chk-2",
        values=embedder.embed_text("SQLAlchemy ORM engine and relational database sessions"),
        metadata={"document_id": "doc-sql", "text": "SQLAlchemy ORM engine and relational database sessions"},
    )

    upserted = store.upsert([v1, v2], namespace="test-ns")
    assert upserted == 2

    # Query for FastAPI
    q_vec = embedder.embed_text("How to build async APIs with FastAPI?")
    matches = store.similarity_search(query_vector=q_vec, top_k=2, namespace="test-ns")
    assert len(matches) == 2
    assert matches[0]["id"] == "chk-1"  # Highest cosine similarity

    # Delete
    store.delete(ids=["chk-1"], namespace="test-ns")
    matches_after = store.similarity_search(query_vector=q_vec, top_k=2, namespace="test-ns")
    assert len(matches_after) == 1
    assert matches_after[0]["id"] == "chk-2"


def test_retrieval_fusion_engine_and_reranker():
    """(`9.4 Retriever & ⭐ Retrieval Fusion Engine`) Verify score normalization, RRF, deduplication, and reranking."""
    sparse = BM25SparseRetriever()
    c1 = ChunkSchema(chunk_id="chk-dense-and-sparse", document_id="doc-1", text="Python async io event loop management")
    c2 = ChunkSchema(chunk_id="chk-sparse-only", document_id="doc-2", text="Async asyncio task sleep and coroutine execution")
    sparse.index_chunks([c1, c2])

    dense_matches = [
        {"id": "chk-dense-and-sparse", "score": 0.88, "metadata": {"text": c1.text, "document_id": c1.document_id}},
        {"id": "chk-dense-only", "score": 0.75, "metadata": {"text": "Vector database embeddings with Pinecone", "document_id": "doc-3"}},
    ]
    sparse_matches = sparse.search("asyncio event loop coroutine", top_k=2)

    fusion = RetrievalFusionEngine(alpha=0.5)
    fused_list = fusion.fuse_results(dense_matches, sparse_matches, candidate_pool_size=10)

    # Check deduplication and fused scores
    ids = [x.chunk_id for x in fused_list]
    assert "chk-dense-and-sparse" in ids
    assert "chk-sparse-only" in ids
    assert "chk-dense-only" in ids
    assert len(ids) == len(set(ids))  # No duplicates!

    # Test Cross-Encoder Reranking
    reranker = CrossEncoderReranker(use_stub=True)
    top_k = reranker.rerank(query="asyncio event loop", candidates=fused_list, top_k=2)
    assert len(top_k) <= 2
    assert top_k[0].score >= top_k[-1].score


def test_context_builder():
    """(`9.5 Context Builder`) Verify deduplication, header formatting, and token budgeting."""
    builder = ContextBuilder(max_tokens=25)
    r1 = RetrievedChunk(
        chunk_id="chk-1",
        document_id="doc-1",
        text="FastAPI high performance async router.",
        score=0.95,
        metadata={"source_name": "FastAPI Docs", "url": "https://fastapi.tiangolo.com"},
    )
    r2 = RetrievedChunk(
        chunk_id="chk-2",
        document_id="doc-2",
        text="Detailed deep dive into database migrations and connection pooling with async SQLAlchemy.",
        score=0.82,
        metadata={"source_name": "SQLAlchemy Docs"},
    )

    ctx = builder.build_context(query="FastAPI router", retrieved_chunks=[r1, r2])
    assert isinstance(ctx, RAGContext)
    assert "[Context 1 | Source: FastAPI Docs" in ctx.formatted_context
    assert "URL: https://fastapi.tiangolo.com" in ctx.formatted_context
    # Check budget enforced (r2 text should be excluded if 25 word token budget exceeded)
    assert ctx.total_tokens <= 25


@pytest.mark.asyncio
async def test_end_to_end_rag_pipeline():
    """(`9.6 Pipeline & Checklist Verification`) Verify full end-to-end RAG indexing and hybrid retrieval."""
    pipeline = RAGPipeline()

    doc_gil = Document(
        id="doc-gil",
        source_id="Python Docs",
        title="Python GIL & Threads",
        content="The Python Global Interpreter Lock protects object access across multiple threads in CPython. True multi-core execution requires subinterpreters or multiprocessing.",
        metadata={"category": "python", "url": "https://docs.python.org/threads"},
    )
    doc_fastapi = Document(
        id="doc-fastapi",
        source_id="FastAPI Docs",
        title="FastAPI Async DI",
        content="FastAPI dependency injection system enables clean architecture, database session injection, and automatic OpenAPI schema validation using Pydantic models.",
        metadata={"category": "web", "url": "https://fastapi.tiangolo.com/di"},
    )

    # 1. Index documents into Pinecone vector store + BM25
    index_res = await pipeline.index_documents([doc_gil, doc_fastapi], namespace="test-pipeline")
    assert index_res["status"] == "indexed"
    assert index_res["indexed_documents"] == 2
    assert index_res["chunks_created"] >= 2
    assert index_res["vectors_upserted"] >= 2
    assert index_res["total_bm25_chunks"] >= 2

    # 2. Execute Hybrid Retrieval Context Query (does NOT call LLM!)
    context = await pipeline.retrieve_context(
        query="How does FastAPI dependency injection handle database session injection and OpenAPI validation?",
        top_k=2,
        namespace="test-pipeline",
    )

    assert context.query == "How does FastAPI dependency injection handle database session injection and OpenAPI validation?"
    assert len(context.retrieved_chunks) > 0
    # Top candidate must be doc_fastapi
    assert context.retrieved_chunks[0].document_id == "doc-fastapi"
    assert "FastAPI dependency injection system" in context.formatted_context
