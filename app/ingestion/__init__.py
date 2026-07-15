# File: app/ingestion/__init__.py
"""
Milestone 8 — Knowledge Ingestion Pipeline.
Responsible for collecting information from curated sources, processing HTML into clean text,
validating quality, and storing clean, versioned documents in PostgreSQL (`Knowledge Repository`).
No chunking and no embeddings (those belong to Milestone 9).
"""
from app.ingestion.schemas import (
    TrustLevel,
    PriorityLevel,
    CrawlStatus,
    KnowledgeSourceSchema,
    RawDocument,
    DocumentMetadata,
    ProcessedDocument,
)
from app.ingestion.source_registry import SourceRegistry, source_registry
from app.ingestion.crawler import WebCrawler, web_crawler
from app.ingestion.processor import ContentProcessor, content_processor
from app.ingestion.document_manager import DocumentManager, document_manager
from app.ingestion.pipeline import IngestionPipeline, ingestion_pipeline

__all__ = [
    "TrustLevel",
    "PriorityLevel",
    "CrawlStatus",
    "KnowledgeSourceSchema",
    "RawDocument",
    "DocumentMetadata",
    "ProcessedDocument",
    "SourceRegistry",
    "source_registry",
    "WebCrawler",
    "web_crawler",
    "ContentProcessor",
    "content_processor",
    "DocumentManager",
    "document_manager",
    "IngestionPipeline",
    "ingestion_pipeline",
]
