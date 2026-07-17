from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_document_repository, get_request_id
from app.repositories.postgres.document_repository import DocumentRepository
from app.schemas.common import APIResponse, success_response
from app.utils.sanitizer import sanitize_payload

router = APIRouter(tags=["Knowledge"])


@router.get("/query", response_model=APIResponse[dict], summary="Query Knowledge Base")
async def query_knowledge(
    q: str = Query("", description="Search query"),
    top_k: int = Query(3, ge=1, le=20),
    request_id: str = Depends(get_request_id),
):
    """Search across the RAG knowledge base."""
    from app.rag import rag_pipeline
    if not q.strip():
        return success_response(data={"results": []}, message="No query provided", request_id=request_id)

    try:
        context = await rag_pipeline.retrieve_context(query=q, top_k=top_k)
        results = [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "text": c.text[:500],
                "score": c.score,
                "source": c.metadata.get("source_name", c.metadata.get("source", "unknown")),
            }
            for c in context.retrieved_chunks
        ]
        return success_response(data={"results": results, "query": q}, message=f"Found {len(results)} results", request_id=request_id)
    except Exception as e:
        return success_response(data={"results": [], "error": str(e)}, message="Knowledge query returned no results", request_id=request_id)


@router.get("/documents", response_model=APIResponse[dict], summary="List Ingested Knowledge Base Documents")
async def list_knowledge_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    Returns all ingested documents, chunk counts, and index status from PostgreSQL.
    """
    documents = await doc_repo.list(skip=skip, limit=limit)

    doc_list = []
    for doc in documents:
        doc_list.append({
            "id": doc.id,
            "title": doc.title,
            "source": doc.metadata.get("source", doc.source_id or "unknown"),
            "category": doc.metadata.get("category", "general"),
            "word_count": len(doc.content.split()),
            "updated_at": doc.metadata.get("updated_at", doc.created_at.isoformat() if hasattr(doc, "created_at") else ""),
            "chunks": doc.metadata.get("chunk_count", 0),
        })

    data = sanitize_payload({
        "documents": doc_list,
        "total_documents": len(doc_list),
        "vector_store": "Pinecone (1024-d embeddings) + BM25",
    })
    return success_response(
        data=data,
        message=f"Retrieved {len(doc_list)} knowledge base documents",
        request_id=request_id,
    )
