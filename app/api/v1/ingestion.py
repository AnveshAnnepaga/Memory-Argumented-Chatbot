# File: app/api/v1/ingestion.py
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from app.api.dependencies import get_document_repository, get_request_id
from app.ingestion import ingestion_pipeline, source_registry
from app.ingestion.schemas import KnowledgeSourceSchema
from app.repositories.postgres.document_repository import DocumentRepository
from app.schemas.common import APIResponse, success_response

router = APIRouter(tags=["Knowledge Ingestion"])


class RawHtmlUploadRequest(BaseModel):
    url: str = Field(..., description="Target URL of the document")
    raw_html: str = Field(..., description="Raw HTML string content")
    source_name: str = Field(default="Manual Upload", description="Name of the source")
    category: str = Field(default="general", description="Category grouping")


@router.get("/sources", response_model=APIResponse[List[Dict[str, Any]]], summary="List Trusted Knowledge Sources")
async def list_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled_only: bool = Query(True, description="Only return enabled sources"),
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 8 Source Registry`) Returns registered trusted knowledge sources.
    """
    sources = source_registry.list_sources(category=category, enabled_only=enabled_only)
    return success_response(
        data=[s.model_dump() for s in sources],
        message=f"Retrieved {len(sources)} knowledge sources",
        request_id=request_id,
    )


@router.post("/sources/{source_name}/crawl", response_model=APIResponse[dict], summary="Crawl Single Source")
async def crawl_source(
    source_name: str,
    max_pages: int = Query(5, ge=1, le=50, description="Max pages to crawl"),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 8 Pipeline`) Executes end-to-end knowledge ingestion for a single registered source.
    Stores clean, versioned documents in PostgreSQL without chunking or embeddings.
    """
    ingestion_pipeline.inject_repository(doc_repo)
    result = await ingestion_pipeline.run_for_source(source_name=source_name, max_pages=max_pages)
    return success_response(
        data=result,
        message=f"Completed ingestion for source '{source_name}'",
        request_id=request_id,
    )


@router.post("/crawl-all", response_model=APIResponse[dict], summary="Crawl All Enabled Sources")
async def crawl_all_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    max_pages_per_source: int = Query(3, ge=1, le=20, description="Max pages per source"),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 8 Pipeline`) Executes knowledge ingestion across all enabled trusted sources.
    """
    ingestion_pipeline.inject_repository(doc_repo)
    result = await ingestion_pipeline.run_all(category=category, max_pages_per_source=max_pages_per_source)
    return success_response(
        data=result,
        message="Completed bulk ingestion across enabled sources",
        request_id=request_id,
    )


@router.post("/upload-html", response_model=APIResponse[dict], summary="Upload Raw HTML for Ingestion")
async def upload_raw_html(
    payload: RawHtmlUploadRequest,
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    (`Milestone 8 Processor & Manager`) Processes and stores clean document from raw HTML payload.
    """
    ingestion_pipeline.inject_repository(doc_repo)
    saved_doc = await ingestion_pipeline.ingest_raw_html(
        url=payload.url,
        raw_html=payload.raw_html,
        source_name=payload.source_name,
        category=payload.category,
    )
    return success_response(
        data=saved_doc.model_dump(),
        message="Raw HTML processed and stored successfully",
        request_id=request_id,
    )
