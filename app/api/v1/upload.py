import logging
import mimetypes
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Query
from fastapi.responses import Response
from app.api.dependencies import get_document_file_repository, get_document_repository, get_request_id
from app.domain.knowledge import DocumentFile
from app.ingestion import ingestion_pipeline
from app.ingestion.processor import content_processor
from app.repositories.postgres.document_file_repository import DocumentFileRepository
from app.repositories.postgres.document_repository import DocumentRepository
from app.schemas.common import APIResponse, error_response, success_response
from app.rag import rag_pipeline

logger = logging.getLogger("app.api.v1.upload")
router = APIRouter(tags=["File Upload"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


def _guess_mime(filename: str, content_type: Optional[str] = None) -> str:
    if content_type and content_type != "application/octet-stream":
        return content_type
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


@router.post("/file", response_model=APIResponse[dict],     summary="Upload a file (PDF, DOCX, Image)")
async def upload_file(
    file: UploadFile = File(..., description="File to upload (PDF, DOCX, or image)"),
    category: str = Form(default="upload", description="Document category"),
    auto_index: bool = Form(default=True, description="Automatically index into RAG after upload"),
    file_repo: DocumentFileRepository = Depends(get_document_file_repository),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    """
    Uploads a file, parses it (PDF text extraction, DOCX text extraction,
    image description via LLaVA),
    stores the file BLOB in PostgreSQL, and optionally indexes into the RAG pipeline.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")

    mime_type = _guess_mime(file.filename, file.content_type)
    if mime_type not in ALLOWED_MIME_TYPES and not mime_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{mime_type}'. Allowed: PDF, DOCX, images",
        )

    file_hash = await file_repo.compute_file_hash(file_bytes)
    existing = await file_repo.find_by_hash(file_hash)
    if existing:
        logger.info(f"Duplicate file upload detected (hash: {file_hash[:12]}...) for '{file.filename}'")
        return success_response(
            data={
                "file_id": existing.id,
                "filename": existing.filename,
                "duplicate": True,
                "extracted_text": existing.extracted_text[:500] + "..." if existing.extracted_text and len(existing.extracted_text) > 500 else existing.extracted_text,
            },
            message=f"Duplicate file (identical to '{existing.filename}')",
            request_id=request_id,
        )

    # Extract text content via file parsers
    ingestion_pipeline.inject_repository(doc_repo)
    processed_doc = await content_processor.process_file(
        file_bytes=file_bytes,
        filename=file.filename,
        mime_type=mime_type,
        source_name="File Upload",
        category=category,
    )

    # Save extracted text as a ProcessedDocument in PostgreSQL
    saved_doc = None
    if processed_doc.is_valid:
        saved_doc = await ingestion_pipeline.doc_manager.save_document(processed_doc)

    # Save file BLOB
    document_file = DocumentFile(
        filename=file.filename,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
        file_hash=file_hash,
        blob_data=file_bytes,
        extracted_text=processed_doc.clean_text[:100000] if processed_doc.clean_text else None,
        document_id=saved_doc.document_id if saved_doc else None,
    )
    saved_file = await file_repo.save(document_file)

    # Optionally auto-index into RAG
    rag_indexed = False
    if auto_index and saved_doc and saved_doc.is_valid:
        try:
            from app.domain.knowledge import Document as DomainDocument
            rag_doc = DomainDocument(
                id=saved_doc.document_id,
                source_id="File Upload",
                title=processed_doc.title or file.filename,
                content=processed_doc.clean_text,
                metadata={
                    "url": f"file:///{file.filename}",
                    "category": category,
                    "source": "File Upload",
                    "file_id": saved_file.id,
                    "file_type": mime_type,
                },
            )
            index_result = await rag_pipeline.index_document(rag_doc)
            rag_indexed = index_result.get("status") == "indexed"
            if rag_indexed:
                await file_repo.update_document_id(saved_file.id, saved_doc.document_id)
        except Exception as e:
            logger.warning(f"Auto-index into RAG failed for '{file.filename}': {e}")

    response_data = {
        "file_id": saved_file.id,
        "document_id": saved_doc.document_id if saved_doc else None,
        "filename": file.filename,
        "mime_type": mime_type,
        "size_bytes": len(file_bytes),
        "title": processed_doc.title or file.filename,
        "file_type": processed_doc.metadata.custom.get("file_type") if hasattr(processed_doc.metadata, "custom") else None,
        "word_count": processed_doc.metadata.word_count,
        "valid": processed_doc.is_valid,
        "duplicate": False,
        "rag_indexed": rag_indexed,
        "extracted_text_preview": processed_doc.clean_text[:500] + "..." if processed_doc.clean_text and len(processed_doc.clean_text) > 500 else processed_doc.clean_text,
    }

    logger.info(f"Uploaded '{file.filename}' ({mime_type}, {len(file_bytes)} bytes) -> file_id={saved_file.id}, indexed={rag_indexed}")
    return success_response(
        data=response_data,
        message=f"File '{file.filename}' uploaded and processed successfully",
        request_id=request_id,
    )


@router.get("/{file_id}", response_model=APIResponse[dict], summary="Get file metadata")
async def get_file(
    file_id: str,
    file_repo: DocumentFileRepository = Depends(get_document_file_repository),
    request_id: str = Depends(get_request_id),
):
    doc_file = await file_repo.get(file_id)
    if not doc_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_id}' not found")
    return success_response(
        data={
            "file_id": doc_file.id,
            "filename": doc_file.filename,
            "mime_type": doc_file.mime_type,
            "size_bytes": doc_file.size_bytes,
            "document_id": doc_file.document_id,
            "created_at": doc_file.created_at.isoformat(),
            "extracted_text_preview": doc_file.extracted_text[:500] + "..." if doc_file.extracted_text and len(doc_file.extracted_text) > 500 else doc_file.extracted_text,
        },
        request_id=request_id,
    )


@router.get("/{file_id}/download", summary="Download file blob")
async def download_file(
    file_id: str,
    file_repo: DocumentFileRepository = Depends(get_document_file_repository),
):
    doc_file = await file_repo.get(file_id)
    if not doc_file or not doc_file.blob_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or blob empty")
    return Response(
        content=doc_file.blob_data,
        media_type=doc_file.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc_file.filename}"'},
    )


@router.delete("/{file_id}", response_model=APIResponse[dict], summary="Delete uploaded file")
async def delete_file(
    file_id: str,
    file_repo: DocumentFileRepository = Depends(get_document_file_repository),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    request_id: str = Depends(get_request_id),
):
    doc_file = await file_repo.get(file_id)
    if not doc_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_id}' not found")

    if doc_file.document_id:
        try:
            await doc_repo.delete(doc_file.document_id)
        except Exception as e:
            logger.warning(f"Could not delete associated document {doc_file.document_id}: {e}")

    deleted = await file_repo.delete(file_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete file")

    return success_response(data={"file_id": file_id}, message="File deleted successfully", request_id=request_id)


@router.get("", response_model=APIResponse[List[Dict[str, Any]]], summary="List all uploaded files")
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    file_repo: DocumentFileRepository = Depends(get_document_file_repository),
    request_id: str = Depends(get_request_id),
):
    files = await file_repo.list(skip=skip, limit=limit)
    return success_response(
        data=[
            {
                "file_id": f.id,
                "filename": f.filename,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "document_id": f.document_id,
                "created_at": f.created_at.isoformat(),
            }
            for f in files
        ],
        message=f"Retrieved {len(files)} uploaded files",
        request_id=request_id,
    )
