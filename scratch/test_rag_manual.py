# File: scratch/test_rag_manual.py
"""
Interactive Manual RAG Evaluation & Testing Script
--------------------------------------------------
Indices sample knowledge base documents into your live Pinecone vector index ('chatbot-vectors')
and local BM25 engine, then runs the ⭐ Retrieval Fusion Engine and Cross-Encoder Reranker
to display retrieved chunks, relevance metrics, and formatted RAGContext.
"""
import asyncio
import sys
import os

# Add project root to python path so app modules can be imported directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.database.pinecone import pinecone_manager
from app.rag.pipeline import rag_pipeline
from app.ingestion.schemas import ProcessedDocument, DocumentMetadata


SAMPLE_DOCUMENTS = [
    ProcessedDocument(
        document_id="doc-python-async",
        url="https://docs.python.org/3/library/asyncio.html",
        title="Python Asyncio & Event Loop Architecture",
        source_name="Python Docs",
        category="Backend Development",
        clean_text=(
            "Python's asyncio library enables concurrent programming using the async and await syntax. "
            "At the core of asyncio is the event loop, which schedules and runs asynchronous tasks, "
            "handles system I/O events, and manages coroutines without requiring OS-level threads. "
            "Using coroutines avoids race conditions commonly found in multi-threaded Python applications."
        ),
        metadata=DocumentMetadata(title="Python Asyncio & Event Loop Architecture", author="Antigravity Engineering"),
        content_hash="hash-1"
    ),
    ProcessedDocument(
        document_id="doc-hybrid-rag",
        url="https://antigravity.ai/docs/hybrid-rag",
        title="Hybrid RAG & Retrieval Fusion Engine Design",
        source_name="Antigravity AI",
        category="AI Architecture",
        clean_text=(
            "Hybrid Retrieval-Augmented Generation (RAG) combines dense semantic vector search with sparse "
            "lexical keyword matching like BM25Okapi. To prevent BM25 and Pinecone scores from competing unfairly, "
            "the Retrieval Fusion Engine applies Min-Max score normalization followed by Reciprocal Rank Fusion (RRF). "
            "After fusion, a Cross-Encoder Reranker evaluates exact query-passage contextual relevance before injecting "
            "the context into LangGraph workflows without calling the LLM during retrieval."
        ),
        metadata=DocumentMetadata(title="Hybrid RAG & Retrieval Fusion Engine Design", author="Antigravity AI Team"),
        content_hash="hash-2"
    ),
    ProcessedDocument(
        document_id="doc-neo4j-graph",
        url="https://neo4j.com/docs/",
        title="Knowledge Graphs with Neo4j and Cypher Queries",
        source_name="Neo4j Docs",
        category="Database Systems",
        clean_text=(
            "Knowledge Graphs store structured relationships between entities using nodes, edges, and properties. "
            "Neo4j is a high-performance native graph database queried via the Cypher query language. "
            "In GraphRAG systems, graph traversals retrieve multi-hop relationships such as 'User -> LIKES -> Topic' "
            "or 'Service -> DEPENDS_ON -> Database', complementing vector similarity search."
        ),
        metadata=DocumentMetadata(title="Knowledge Graphs with Neo4j and Cypher Queries", author="Data Engineering"),
        content_hash="hash-3"
    ),
    ProcessedDocument(
        document_id="doc-pinecone-vector",
        url="https://docs.pinecone.io/",
        title="Pinecone Serverless Vector Index Management",
        source_name="Pinecone Docs",
        category="Database Systems",
        clean_text=(
            "Pinecone is a cloud-native vector database designed for low-latency similarity search at scale. "
            "Serverless Pinecone indexes automatically scale compute and storage resources. "
            "When indexing high-dimensional vectors (such as 1024-dim BAAI/bge-large-en-v1.5 embeddings), "
            "using cosine similarity ensures invariant angle comparison regardless of vector magnitude."
        ),
        metadata=DocumentMetadata(title="Pinecone Serverless Vector Index Management", author="Infrastructure Layer"),
        content_hash="hash-4"
    )
]


async def run_manual_rag_test():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 75)
    print("[START] INITIALIZING MANUAL RAG EVALUATION ENGINE")
    print("=" * 75)

    # 1. Initialize live Pinecone connection
    print("\n[1/4] Connecting to live Pinecone Cloud Index...")
    connected = await pinecone_manager.initialize()
    if connected:
        print(f"  [OK] Connected to Pinecone index: '{settings.pinecone.index_name}' (Live Mode)")
    else:
        print("  [WARN] Pinecone live connection stubbed (Check API key or network). Using local RAM store.")
    
    use_sample = "--sample" in sys.argv
    target_namespace = "manual_test" if use_sample else "knowledge"

    # 2. Index sample documents or connect to production knowledge base
    if use_sample:
        print("\n[2/4] Indexing sample knowledge documents into Pinecone + BM25 (--sample passed)...")
        index_stats = await rag_pipeline.index_documents(SAMPLE_DOCUMENTS, namespace=target_namespace)
        print(f"  [OK] Indexing Complete:")
        print(f"     - Documents Processed : {index_stats.get('indexed_documents', 0)}")
        print(f"     - Chunks Created      : {index_stats.get('chunks_created', 0)}")
        print(f"     - Vectors Upserted    : {index_stats.get('vectors_upserted', 0)} (Pinecone)")
        print(f"     - BM25 Chunks Indexed : {index_stats.get('total_bm25_chunks', 0)} (RAM)")
    else:
        print(f"\n[2/4] Using Production RAG Index (Namespace: '{target_namespace}')...")
        print("  [OK] Ready to query production knowledge base (Python, FastAPI, LangChain, LangGraph, PostgreSQL docs)")

    # 3. Run benchmark automated queries
    benchmark_queries = [
        "How does the asyncio event loop execute coroutines in Python?",
        "What is Dependency Injection in FastAPI?",
        "Explain PostgreSQL Multi-Version Concurrency Control (MVCC).",
    ]

    print("\n[3/4] Running Benchmark Evaluation Queries:")
    for idx, query in enumerate(benchmark_queries, 1):
        print(f"\n--- Benchmark Query #{idx}: \"{query}\" ---")
        context = await rag_pipeline.retrieve_context(
            query=query,
            top_k=2,
            candidate_pool_size=15,
            namespace=target_namespace
        )
        print(f"  Retrieved {len(context.retrieved_chunks)} top candidate chunks:")
        for rank, chunk in enumerate(context.retrieved_chunks, 1):
            title = chunk.metadata.get("document_title", "Unknown Title")
            print(f"    [{rank}] Chunk ID : {chunk.chunk_id[:16]}...")
            print(f"        Document : {title}")
            print(f"        Scores   : Final={chunk.score:.4f} | Dense={chunk.dense_score:.4f} | Sparse={chunk.sparse_score:.4f}")
            print(f"        Text     : {chunk.text[:120]}...")

    # 4. Interactive evaluation loop
    print("\n" + "=" * 75)
    print(f"[4/4] INTERACTIVE MANUAL RAG EVALUATION CONSOLE (Namespace: '{target_namespace}')")
    print("Type any question to test live Hybrid Retrieval against Pinecone.")
    print("Type 'q' or 'exit' to stop.")
    print("=" * 75)

    while True:
        try:
            user_query = input("\n[QUERY] Enter RAG Query: ").strip()
            if not user_query:
                continue
            if user_query.lower() in ("q", "exit", "quit"):
                print("\nExiting manual evaluation console. Good job!")
                break

            ctx = await rag_pipeline.retrieve_context(
                query=user_query,
                top_k=3,
                candidate_pool_size=15,
                namespace=target_namespace
            )

            print(f"\n[RESULT] Retrieved {len(ctx.retrieved_chunks)} chunks [Total Tokens: {ctx.total_tokens}]:")
            for rank, chunk in enumerate(ctx.retrieved_chunks, 1):
                title = chunk.metadata.get("document_title", "Unknown Title")
                print(f"\n  Top #{rank} -> Score: {chunk.score:.4f} (Dense={chunk.dense_score:.4f}, Sparse={chunk.sparse_score:.4f})")
                print(f"  Source   : {title}")
                print(f"  Content  : {chunk.text}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting console.")
            break


if __name__ == "__main__":
    asyncio.run(run_manual_rag_test())
