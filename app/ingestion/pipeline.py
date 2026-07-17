# File: app/ingestion/pipeline.py
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

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

    async def run_for_source(self, source_name: str, max_pages: Optional[int] = None, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes end-to-end ingestion workflow for a single registered knowledge source.
        Uses per-source config from sources.yaml if max_pages/max_depth not overridden.
        """
        source = self.registry.get_source(source_name)
        if not source:
            logger.error(f"Source '{source_name}' not found in Source Registry.")
            return {"status": "error", "message": f"Source '{source_name}' not found", "processed": 0, "saved": 0}

        if not source.enabled:
            logger.info(f"Source '{source_name}' is disabled.")
            return {"status": "skipped", "message": f"Source '{source_name}' is disabled", "processed": 0, "saved": 0}

        logger.info(f"=== Starting Ingestion Pipeline for Source: '{source.name}' ===")

        # Step 1: Crawler (`Collect raw HTML from websites`) — uses source.max_pages / source.max_depth from YAML
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

    async def run_all(self, category: Optional[str] = None, max_pages_per_source: Optional[int] = None, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """Runs the ingestion pipeline for all enabled sources (`run_all`). Uses per-source config from YAML when overrides are None."""
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




class RefreshScheduler:
    """
    Periodic re-crawling scheduler for knowledge sources.
    Runs `run_for_source` on a configurable interval for each registered source.
    Designed to be started as an asyncio background task on app startup.
    """

    def __init__(self, pipeline: IngestionPipeline, default_interval_hours: int = 24):
        self.pipeline = pipeline
        self.default_interval_hours = default_interval_hours
        self._tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._source_intervals: Dict[str, int] = {}

    def set_interval(self, source_name: str, interval_hours: int) -> None:
        """Override the default refresh interval for a specific source."""
        self._source_intervals[source_name] = interval_hours

    async def start(self) -> None:
        """Starts the background refresh loop for all enabled sources."""
        if self._running:
            logger.warning("RefreshScheduler already running")
            return
        self._running = True
        sources = self.pipeline.registry.list_sources(enabled_only=True)
        for source in sources:
            interval = self._source_intervals.get(source.name, self.default_interval_hours)
            task = asyncio.create_task(self._refresh_loop(source.name, interval))
            self._tasks[source.name] = task
            logger.info(f"Scheduled refresh for '{source.name}' every {interval}h")
        logger.info(f"RefreshScheduler started with {len(sources)} sources")

    async def stop(self) -> None:
        """Cancels all background refresh tasks."""
        self._running = False
        for name, task in self._tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        logger.info("RefreshScheduler stopped")

    async def _refresh_loop(self, source_name: str, interval_hours: int) -> None:
        """Continuous loop: refresh source, wait interval, repeat."""
        while self._running:
            try:
                logger.info(f"RefreshScheduler: refreshing '{source_name}'")
                result = await self.pipeline.run_for_source(source_name)
                saved = result.get("saved", 0)
                logger.info(f"RefreshScheduler: '{source_name}' saved {saved} new documents")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"RefreshScheduler: error refreshing '{source_name}': {e}")
            await asyncio.sleep(interval_hours * 3600)

    @property
    def active(self) -> bool:
        return self._running


ingestion_pipeline = IngestionPipeline()
refresh_scheduler = RefreshScheduler(ingestion_pipeline)
