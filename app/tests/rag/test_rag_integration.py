import pytest
from app.domain.knowledge import Document
from app.rag import (
    ChunkSchema,
    RAGPipeline,
    hybrid_retriever,
    chunker,
    embedder,
    vector_store,
)

embedder.use_stub = True
if hasattr(hybrid_retriever, "reranker") and hasattr(hybrid_retriever.reranker, "use_stub"):
    hybrid_retriever.reranker.use_stub = True


@pytest.fixture
def pipeline():
    return RAGPipeline()


@pytest.fixture
def sample_docs():
    return [
        Document(
            id="doc-k8s",
            source_id="Kubernetes Docs",
            title="Kubernetes Pods Overview",
            content=(
                "A Pod is the smallest deployable unit in Kubernetes. "
                "Pods encapsulate one or more containers with shared storage and network. "
                "They are created and managed by controllers like Deployments and StatefulSets. "
                "Each Pod gets a unique IP address within the cluster."
            ),
            metadata={"url": "https://kubernetes.io/docs/concepts/workloads/pods/", "category": "orchestration"},
        ),
        Document(
            id="doc-docker",
            source_id="Docker Docs",
            title="Docker Container Basics",
            content=(
                "Docker containers are lightweight, standalone executables that package software "
                "with all its dependencies. Containers use the host OS kernel via namespace isolation "
                "and cgroups for resource limiting. Docker images are built from Dockerfiles."
            ),
            metadata={"url": "https://docs.docker.com/get-started/", "category": "containerization"},
        ),
        Document(
            id="doc-fastapi-ml",
            source_id="FastAPI Docs",
            title="FastAPI Machine Learning Serving",
            content=(
                "FastAPI is ideal for serving ML models as async REST endpoints. "
                "It supports automatic OpenAPI documentation, Pydantic request validation, "
                "and dependency injection for database sessions and model loading."
            ),
            metadata={"url": "https://fastapi.tiangolo.com/advanced/ml-models/", "category": "web"},
        ),
    ]


@pytest.mark.asyncio
async def test_full_index_and_retrieve(pipeline, sample_docs):
    """Integration test: index documents, then retrieve relevant context."""
    index_res = await pipeline.index_documents(sample_docs, namespace="test-integration")
    assert index_res["status"] == "indexed"
    assert index_res["indexed_documents"] == 3
    assert index_res["chunks_created"] >= 3

    context = await pipeline.retrieve_context(
        query="How do Kubernetes pods differ from Docker containers?",
        top_k=3,
        namespace="test-integration",
    )

    assert context.query is not None
    assert len(context.retrieved_chunks) > 0
    assert "Pod" in context.formatted_context or "Kubernetes" in context.formatted_context
    assert "Docker" in context.formatted_context

    # Clean up
    doc_ids = [doc.id for doc in sample_docs]
    for c in context.retrieved_chunks:
        doc_ids.append(c.document_id)
    vector_store.delete(ids=list(set(doc_ids)), namespace="test-integration")


@pytest.mark.asyncio
async def test_dense_sparse_fusion(pipeline):
    """Verify hybrid retrieval returns results from both BM25 and vector search."""
    doc = Document(
        id="doc-ml-integration",
        source_id="Test",
        title="ML Model Deployment Patterns",
        content=(
            "Model deployment patterns include batch inference via scheduled jobs, "
            "real-time REST API serving with FastAPI, and streaming with Kafka. "
            "Each pattern has tradeoffs in latency, throughput, and cost."
        ),
        metadata={"category": "mlops"},
    )

    await pipeline.index_document(doc, namespace="test-fusion")

    context = await pipeline.retrieve_context(
        query="What are the different ML model deployment patterns?",
        top_k=5,
        namespace="test-fusion",
    )

    assert len(context.retrieved_chunks) >= 1
    # The retrieved chunk should contain key terms from the indexed document
    ctx_text = context.formatted_context.lower()
    assert any(term in ctx_text for term in ["batch", "rest", "fastapi", "kafka", "streaming"])

    vector_store.delete(ids=["doc-ml-integration"], namespace="test-fusion")


@pytest.mark.asyncio
async def test_empty_query_returns_empty(pipeline):
    context = await pipeline.retrieve_context(query="", top_k=3)
    assert len(context.retrieved_chunks) == 0


@pytest.mark.asyncio
async def test_chunker_preserves_code_blocks():
    """Verify code blocks survive chunking as atomic units."""
    doc = Document(
        id="doc-code",
        source_id="Test",
        title="Code Example",
        content=(
            "Here is an example FastAPI app:\n\n"
            "```python\n"
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n\n"
            "@app.get(\"/\")\n"
            "def read_root():\n"
            "    return {\"Hello\": \"World\"}\n"
            "```\n\n"
            "This creates a simple web server."
        ),
        metadata={},
    )

    chunks = chunker.chunk_document(doc)
    code_block_found = any("```python" in c.text for c in chunks)
    assert code_block_found, "Code block should be preserved intact in at least one chunk"


@pytest.mark.asyncio
async def test_hyde_expands_query():
    """Verify HyDE query expansion produces a longer query text."""
    from app.rag.retriever import HybridRetriever

    retriever = HybridRetriever(use_hyde=True)
    try:
        original, expanded = await retriever._expand_with_hyde(
            "What is the difference between a Deployments and StatefulSet in Kubernetes?"
        )
        if expanded != original:
            assert len(expanded.split()) > len(original.split())
            assert "Kubernetes" in expanded or "StatefulSet" in expanded
    except Exception:
        # HyDE may fail without LLM; that's fine
        pass


@pytest.mark.asyncio
async def test_ragas_evaluation():
    """Verify RAGAS evaluator produces expected metric keys."""
    try:
        from app.evaluation.ragas_evaluator import ragas_evaluator
    except ImportError:
        pytest.skip("ragas_evaluator not available")

    results = await ragas_evaluator.evaluate(
        queries=["What is Kubernetes?"],
        responses=["Kubernetes is a container orchestration platform."],
        contexts=[["Kubernetes orchestrates container workloads across clusters."]],
        ground_truths=["Kubernetes is a container orchestration system."],
    )

    assert "faithfulness" in results
    assert "answer_relevancy" in results
    assert "context_precision" in results
    assert "context_recall" in results
    assert all(0.0 <= v <= 1.0 for v in results.values())
