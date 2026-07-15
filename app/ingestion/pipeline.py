# File: app/ingestion/pipeline.py
import logging
from typing import Any, Dict, List, Optional
from app.ingestion.crawler import web_crawler
from app.ingestion.document_manager import document_manager
from app.ingestion.processor import content_processor
from app.ingestion.schemas import CrawlStatus, ProcessedDocument, RawDocument
from app.ingestion.source_registry import source_registry
from app.repositories.postgres.document_repository import DocumentRepository

logger = logging.getLogger("app.ingestion.pipeline")


class IngestionPipeline:
    """
    (`8.5 Pipeline`)
    Orchestrates the complete knowledge ingestion workflow without chunking or embeddings (`Milestone 8`).
    Flow: Source -> Crawler -> Processor -> Document Manager -> Repository (PostgreSQL).
    """

    def __init__(self):
        self.registry = source_registry
        self.crawler = web_crawler
        self.processor = content_processor
        self.doc_manager = document_manager

    def inject_repository(self, repository: DocumentRepository) -> None:
        """Injects active PostgreSQL repository session into Document Manager."""
        self.doc_manager.set_repository(repository)

    async def run_for_source(self, source_name: str, max_pages: int = 5, max_depth: int = 2) -> Dict[str, Any]:
        """
        Executes end-to-end ingestion workflow for a single registered knowledge source.
        """
        source = self.registry.get_source(source_name)
        if not source:
            logger.error(f"Source '{source_name}' not found in Source Registry.")
            return {"status": "error", "message": f"Source '{source_name}' not found", "processed": 0, "saved": 0}

        if not source.enabled:
            logger.info(f"Source '{source_name}' is disabled.")
            return {"status": "skipped", "message": f"Source '{source_name}' is disabled", "processed": 0, "saved": 0}

        logger.info(f"=== Starting Ingestion Pipeline for Source: '{source.name}' ===")

        # Step 1: Crawler (`Collect raw HTML from websites`)
        raw_docs = await self.crawler.crawl_source(source, max_pages=max_pages, max_depth=max_depth)
        if not raw_docs:
            return {"status": "completed", "message": "No pages crawled or robots.txt blocked", "processed": 0, "saved": 0}

        processed_count = 0
        saved_count = 0
        duplicate_count = 0
        error_count = 0
        saved_documents: List[ProcessedDocument] = []

        # Step 2: Content Processor & Step 3: Document Manager -> Repository
        for raw_doc in raw_docs:
            processed_doc = self.processor.process(raw_doc)
            processed_count += 1

            if not processed_doc.is_valid:
                if processed_doc.is_duplicate:
                    duplicate_count += 1
                else:
                    error_count += 1
                continue

            saved_doc = await self.doc_manager.save_document(processed_doc)
            if saved_doc.is_valid and not saved_doc.is_duplicate:
                saved_count += 1
                saved_documents.append(saved_doc)
            elif saved_doc.is_duplicate:
                duplicate_count += 1

        logger.info(
            f"=== Completed Ingestion for '{source.name}': "
            f"{processed_count} Processed | {saved_count} Saved | {duplicate_count} Duplicates | {error_count} Errors ==="
        )

        return {
            "status": "completed",
            "source": source.name,
            "crawled_pages": len(raw_docs),
            "processed": processed_count,
            "saved": saved_count,
            "duplicates": duplicate_count,
            "errors": error_count,
            "documents": [d.model_dump() for d in saved_documents],
        }

    async def run_all(self, category: Optional[str] = None, max_pages_per_source: int = 30, max_depth: int = 2) -> Dict[str, Any]:
        """Runs the ingestion pipeline for all enabled sources (`run_all`)."""
        sources = self.registry.list_sources(category=category, enabled_only=True)
        logger.info(f"Running Ingestion Pipeline across {len(sources)} enabled knowledge sources...")

        results = []
        total_saved = 0
        for source in sources:
            res = await self.run_for_source(source.name, max_pages=max_pages_per_source, max_depth=max_depth)
            results.append(res)
            total_saved += res.get("saved", 0)

        return {
            "status": "completed",
            "sources_processed": len(sources),
            "total_documents_saved": total_saved,
            "details": results,
        }

    async def ingest_raw_html(
        self,
        url: str,
        raw_html: str,
        source_name: str = "Manual Upload",
        category: str = "general",
    ) -> ProcessedDocument:
        """Directly processes and saves a raw HTML payload (useful for webhook or manual ingestion)."""
        raw_doc = RawDocument(
            url=url,
            source_name=source_name,
            category=category,
            raw_html=raw_html,
            http_status=200,
        )
        processed_doc = self.processor.process(raw_doc)
        return await self.doc_manager.save_document(processed_doc)


ingestion_pipeline = IngestionPipeline()
