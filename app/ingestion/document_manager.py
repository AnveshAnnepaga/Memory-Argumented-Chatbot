# File: app/ingestion/document_manager.py
from datetime import datetime, timezone
import logging
from typing import Optional
from app.domain.knowledge import Document
from app.ingestion.schemas import ProcessedDocument
from app.repositories.postgres.document_repository import DocumentRepository

logger = logging.getLogger("app.ingestion.document_manager")


class DocumentManager:
    """
    (`8.4 Document Manager`)
    Manages processed documents, versioning, checksum verification, and repository persistence.
    Responsibilities: Versioning, Checksum generation, Save clean documents, Update existing documents,
    Interface with Repository Layer (`Knowledge Repository` / `DocumentRepository`).
    """

    def __init__(self, repository: Optional[DocumentRepository] = None):
        if not repository:
            repository = DocumentRepository(session=None)  # Stub fallback if session not provided explicitly
        self.repository = repository

    def set_repository(self, repository: DocumentRepository) -> None:
        """Dynamically injects active DocumentRepository session."""
        self.repository = repository

    async def save_document(self, processed_doc: ProcessedDocument) -> ProcessedDocument:
        """
        Saves a clean document to PostgreSQL (`Save clean documents` / `Update existing documents`).
        Handles deduplication (`Checksum generation`) and versioning (`Versioning`).
        """
        if not processed_doc.is_valid:
            logger.warning(
                f"Skipping storage for invalid/duplicate document '{processed_doc.url}': {processed_doc.validation_errors}"
            )
            return processed_doc

        # 1. Check if document exists by URL
        existing = await self.repository.find_by_url(processed_doc.url)
        if existing:
            existing_checksum = str(existing.metadata.get("checksum", ""))
            existing_version = int(existing.metadata.get("version", 1))

            # 2. Checksum validation (`Duplicate check`)
            if existing_checksum == processed_doc.content_hash:
                logger.info(f"Document '{processed_doc.url}' is unchanged (Checksum match). Skipping update.")
                processed_doc.is_duplicate = True
                processed_doc.version = existing_version
                processed_doc.document_id = existing.id
                return processed_doc

            # 3. Versioning (`Updated content creates a new document version`)
            processed_doc.version = existing_version + 1
            logger.info(f"Document '{processed_doc.url}' modified. Bumping version {existing_version} -> {processed_doc.version}")
        else:
            processed_doc.version = 1
            logger.info(f"New document '{processed_doc.url}' saving as v1.")

        # 4. Interface with Repository Layer (`PostgreSQL Storage`)
        domain_doc = Document(
            id=processed_doc.document_id,
            source_id=processed_doc.source_name,
            title=processed_doc.title,
            content=processed_doc.clean_text,
            metadata={
                "url": processed_doc.url,
                "category": processed_doc.category,
                "source": processed_doc.source_name,
                "version": processed_doc.version,
                "checksum": processed_doc.content_hash,
                "author": processed_doc.metadata.author,
                "language": processed_doc.metadata.language,
                "word_count": processed_doc.metadata.word_count,
                "description": processed_doc.metadata.description,
                "keywords": processed_doc.metadata.keywords,
                "extracted_links_count": processed_doc.metadata.extracted_links_count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Save via repository
        saved_entity = await self.repository.create(domain_doc)
        processed_doc.document_id = saved_entity.id
        logger.info(
            f"Successfully stored clean document '{processed_doc.title}' (v{processed_doc.version}) in PostgreSQL Repository."
        )
        return processed_doc

    async def get_latest_version(self, url: str) -> Optional[ProcessedDocument]:
        """Retrieves the latest processed document version for a URL."""
        existing = await self.repository.find_by_url(url)
        if not existing:
            return None

        meta = existing.metadata
        from app.ingestion.schemas import DocumentMetadata
        doc_meta = DocumentMetadata(
            title=existing.title,
            author=meta.get("author"),
            language=meta.get("language", "en"),
            word_count=int(meta.get("word_count", len(existing.content.split()))),
            description=meta.get("description"),
            keywords=meta.get("keywords", []),
            extracted_links_count=int(meta.get("extracted_links_count", 0)),
        )
        return ProcessedDocument(
            document_id=existing.id,
            url=str(meta.get("url", url)),
            title=existing.title,
            source_name=str(meta.get("source", existing.source_id or "unknown")),
            category=str(meta.get("category", "general")),
            clean_text=existing.content,
            metadata=doc_meta,
            content_hash=str(meta.get("checksum", "")),
            version=int(meta.get("version", 1)),
            is_duplicate=False,
            validation_errors=[],
        )


document_manager = DocumentManager()
