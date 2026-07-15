# File: app/api/v1/retrieval.py
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from app.api.dependencies import get_document_repository, get_request_id
from app.core.exceptions import RepositoryNotFoundException
from app.rag import rag_pipeline
from app.rag.schemas import RAGContext
from app.repositories.postgres.document_repository import DocumentRepository
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Hybrid RAG Retrieval"])


class RetrievalQueryRequest(BaseModel):
    query: str = Field(..., description="User search query or question")
    top_k: int = Field(default=5, ge=1, le=50, description="Top K reranked chunks to return")
    candidate_pool_size: int = Field(default=25, ge=5, le=100, description="Initial candidate pool size before fusion/reranking")
    max_tokens: int = Field(default=3000, ge=100, le=32000, description="Token budget limit for context builder")
    namespace: Optional[str] = Field(default=None, description="Pinecone index namespace")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filter dict")


@router.post("/search", response_model=APIResponse[dict], summary="Execute Hybrid RAG Search & Build Context")
async def execute_hybrid_search(
    payload: RetrievalQueryRequest,
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 9 Hybrid RAG Pipeline`)
    Executes: Query -> Dense + BM25 Search -> Retrieval Fusion Engine -> Cross-Encoder Reranker -> Top K -> Context Builder.
    Returns structured RAGContext ready for injection into LangGraph / LLM prompts.
    Notice: Does NOT call the LLM!
    """
    context: RAGContext = await rag_pipeline.retrieve_context(
        query=payload.query,
        top_k=payload.top_k,
        candidate_pool_size=payload.candidate_pool_size,
        max_tokens=payload.max_tokens,
        namespace=payload.namespace,
        filter=payload.filter,
    )
    return success_response(
        data=context.model_dump(),
        message=f"Retrieved {len(context.retrieved_chunks)} chunks ({context.total_tokens} tokens)",
        request_id=request_id,
    )


@router.post("/index/{document_id}", response_model=APIResponse[dict], summary="Index Single Document into RAG")
async def index_single_document(
    document_id: str,
    namespace: Optional[str] = Query(None, description="Pinecone index namespace"),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 9 Indexing Pipeline`)
    Fetches clean document from PostgreSQL (`DocumentRepository`), chunks it, computes embeddings,
    and indexes into Pinecone and BM25 (`Document -> Chunks -> Embed -> Pinecone + BM25`).
    """
    doc = await doc_repo.get_by_id(document_id)
    if not doc:
        raise RepositoryNotFoundException("Document", document_id)

    result = await rag_pipeline.index_document(doc, namespace=namespace)
    return success_response(
        data=result,
        message=f"Indexed document '{document_id}' successfully",
        request_id=request_id,
    )


@router.post("/index-all", response_model=APIResponse[dict], summary="Batch Index All PostgreSQL Documents into RAG")
async def index_all_documents(
    namespace: Optional[str] = Query(None, description="Pinecone index namespace"),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 9 Batch Indexing Pipeline`)
    Fetches all stored documents from PostgreSQL and builds complete Pinecone dense + BM25 sparse indexes.
    """
    # Fetch top 500 documents from repo
    docs = await doc_repo.list_all(limit=500, offset=0)
    result = await rag_pipeline.index_documents(docs, namespace=namespace)
    return success_response(
        data=result,
        message=f"Batch indexing completed for {len(docs)} documents",
        request_id=request_id,
    )
