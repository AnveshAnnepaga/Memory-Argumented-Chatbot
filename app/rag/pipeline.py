# File: app/rag/pipeline.py
import logging
from typing import Any, Dict, List, Optional, Union
from app.domain.knowledge import Document
from app.ingestion.schemas import ProcessedDocument
from app.rag.chunker import chunker
from app.rag.context_builder import context_builder
from app.rag.embedder import embedder
from app.rag.retriever import hybrid_retriever
from app.rag.schemas import ChunkSchema, RAGContext
from app.rag.vector_store import vector_store

logger = logging.getLogger("rag.pipeline")


class RAGPipeline:
    """
    (`9.6 RAG Pipeline`)
    Complete end-to-end orchestration of Milestone 9 Hybrid RAG:
    
    1. Ingestion / Indexing Pipeline:
       `Document` -> `Chunker` -> `Embedder` -> `Pinecone Vector Store (Dense)` + `BM25 (Sparse)` -> Done
       
    2. Retrieval Pipeline:
       `User Query` -> `Embedder` -> `Dense Search + BM25 Search` -> `Retrieval Fusion Engine` ->
       `Cross-Encoder Reranker` -> `Top K` -> `Context Builder` -> `Ready for LangGraph`
    """

    def __init__(self):
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.retriever = hybrid_retriever
        self.context_builder = context_builder
        self._all_indexed_chunks: List[ChunkSchema] = []
        self.doc_repository = None

    def inject_document_repository(self, repository: Any) -> None:
        """Injects the active PostgreSQL DocumentRepository instance."""
        self.doc_repository = repository

    async def index_document(
        self,
        document: Union[Document, ProcessedDocument],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs the complete RAG indexing pipeline for a single clean document from PostgreSQL.
        """
        doc_id = str(getattr(document, "id", getattr(document, "document_id", "")))
        logger.info(f"Starting RAG indexing pipeline for document '{doc_id}'...")

        # Step 1: Chunking (`Document -> Chunks`)
        chunks = self.chunker.chunk_document(document)
        if not chunks:
            return {
                "document_id": doc_id,
                "status": "skipped",
                "reason": "No text chunks generated",
                "chunks_created": 0,
            }

        # Step 2: Embedding Generation (`Chunks -> Vectors`)
        vectors = self.embedder.embed_chunks(chunks)

        # Step 3: Dense Vector Indexing (`Pinecone Upsert`)
        upsert_count = self.vector_store.upsert(vectors, namespace=namespace)

        # Step 4: Sparse BM25 Indexing (`BM25 Index`)
        self._all_indexed_chunks.extend(chunks)
        bm25_count = self.retriever.index_chunks(self._all_indexed_chunks)

        logger.info(
            f"Successfully indexed document '{doc_id}' [Chunks: {len(chunks)} | Vectors Upserted: {upsert_count} | Total BM25 Chunks: {bm25_count}]."
        )
        return {
            "document_id": doc_id,
            "status": "indexed",
            "chunks_created": len(chunks),
            "vectors_upserted": upsert_count,
            "total_bm25_chunks": bm25_count,
        }

    async def index_documents(
        self,
        documents: List[Union[Document, ProcessedDocument]],
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Batch runs the complete RAG indexing pipeline for multiple documents (`PostgreSQL -> Chunks -> Embeddings -> Pinecone + BM25`).
        """
        logger.info(f"Starting batch RAG indexing pipeline for {len(documents)} documents...")
        all_chunks: List[ChunkSchema] = []
        indexed_docs = 0

        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            if chunks:
                all_chunks.extend(chunks)
                indexed_docs += 1

        if not all_chunks:
            return {"status": "skipped", "reason": "No valid text across documents", "indexed_documents": 0}

        # Batch embed all chunks
        vectors = self.embedder.embed_chunks(all_chunks)

        # Batch upsert to Pinecone vector store
        upsert_count = self.vector_store.upsert(vectors, namespace=namespace)

        # Batch build sparse BM25 index
        self._all_indexed_chunks.extend(all_chunks)
        bm25_count = self.retriever.index_chunks(self._all_indexed_chunks)

        logger.info(f"Batch RAG indexing completed [Docs: {indexed_docs} | Chunks: {len(all_chunks)} | Vectors: {upsert_count}].")
        return {
            "status": "indexed",
            "indexed_documents": indexed_docs,
            "chunks_created": len(all_chunks),
            "vectors_upserted": upsert_count,
            "total_bm25_chunks": bm25_count,
        }

    async def index_all_documents(
        self,
        batch_size: int = 32,
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetches all clean documents from injected PostgreSQL repository and indexes them into Pinecone + BM25.
        """
        if not self.doc_repository:
            logger.error("DocumentRepository not injected into RAGPipeline.")
            return {"status": "error", "reason": "No repository injected"}

        docs = await self.doc_repository.list(skip=0, limit=10000)
        logger.info(f"Retrieved {len(docs)} documents from PostgreSQL repository for RAG indexing...")
        return await self.index_documents(docs, namespace=namespace)

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        candidate_pool_size: int = 25,
        max_tokens: int = 3000,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None,
    ) -> RAGContext:
        """
        Runs the complete Hybrid Retrieval and Context Assembly pipeline ready for LangGraph:
        Query -> Dense + BM25 Search -> Retrieval Fusion Engine -> Cross-Encoder Reranker -> Top K -> Context Builder.
        Notice: Does NOT call the LLM!
        """
        logger.info(f"Executing RAG retrieval pipeline for query: '{query[:40]}...'")

        # Apply configured similarity threshold by default.
        if similarity_threshold is None:
            try:
                from app.core.config import settings
                cfg_threshold = float(getattr(settings.retrieval, "similarity_threshold", 0.55))
                similarity_threshold = min(cfg_threshold, 0.55) if cfg_threshold < 0.55 else (
                    0.55 if cfg_threshold > 0.7 else cfg_threshold
                )
            except Exception:
                similarity_threshold = 0.55

        # Step 1: Hybrid Retrieval + Fusion Engine + Cross-Encoder Reranker
        top_chunks = self.retriever.retrieve(
            query=query,
            top_k=top_k,
            candidate_pool_size=candidate_pool_size,
            namespace=namespace,
            filter=filter,
            similarity_threshold=similarity_threshold,
        )

        # Step 2: Context Assembly & Token Budgeting
        context = self.context_builder.build_context(
            query=query,
            retrieved_chunks=top_chunks,
            max_tokens=max_tokens,
        )

        return context


# Global singleton instance
rag_pipeline = RAGPipeline()
