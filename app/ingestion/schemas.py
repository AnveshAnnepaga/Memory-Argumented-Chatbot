# File: app/ingestion/schemas.py
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TrustLevel(str, Enum):
    """Trust tier of the knowledge source (`8.1 Source Registry`)."""
    TIER_1 = "tier1"  # Official Documentation ⭐⭐⭐⭐⭐
    TIER_2 = "tier2"  # Trusted Organizations ⭐⭐⭐⭐
    TIER_3 = "tier3"  # Community Sources ⭐⭐⭐


class PriorityLevel(str, Enum):
    """Crawl priority (`8.1 Source Registry`)."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CrawlStatus(str, Enum):
    """Status of crawl execution (`8.2 Web Crawler`)."""
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeSourceSchema(BaseModel):
    """
    (`8.1 Source Registry`)
    Pydantic schema representing a curated, trusted knowledge source definition.
    """
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Unique name of the knowledge source")
    category: str = Field(..., description="Category group (e.g., 'programming', 'ai_ml')")
    base_url: str = Field(..., description="Base URL of the trusted site")
    trust_level: TrustLevel = Field(default=TrustLevel.TIER_1)
    priority: PriorityLevel = Field(default=PriorityLevel.HIGH)
    enabled: bool = Field(default=True)
    allowed_paths: List[str] = Field(default_factory=list, description="Allowed URL path prefixes/regex")
    excluded_paths: List[str] = Field(default_factory=list, description="Excluded URL path prefixes/regex")
    crawl_frequency_hours: int = Field(default=24, ge=1)
    max_pages: int = Field(default=30, ge=1, description="Max pages to crawl per run")
    max_depth: int = Field(default=2, ge=1, description="Max BFS crawl depth")
    use_sitemap: bool = Field(default=True, description="Attempt sitemap.xml discovery first")
    status: CrawlStatus = Field(default=CrawlStatus.PENDING)


class RawDocument(BaseModel):
    """
    (`8.2 Web Crawler`)
    Pydantic schema representing raw HTML downloaded from a knowledge source.
    """
    model_config = ConfigDict(from_attributes=True)

    url: str
    source_name: str
    category: str
    raw_html: str
    http_status: int = 200
    headers: Dict[str, str] = Field(default_factory=dict)
    downloaded_at: datetime = Field(default_factory=_utcnow)


class DocumentMetadata(BaseModel):
    """
    (`8.3 Content Processor`)
    Extracted structural and semantic metadata from processed HTML.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str = ""
    author: Optional[str] = None
    language: str = "en"
    word_count: int = 0
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    extracted_links_count: int = 0
    custom: Dict[str, Any] = Field(default_factory=dict)


class ProcessedDocument(BaseModel):
    """
    (`8.3 Content Processor` & `8.4 Document Manager`)
    Pydantic schema representing a clean, high-quality document ready for repository storage.
    Notice: No chunking and no vector embeddings here (those belong to Milestone 9).
    """
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    title: str
    source_name: str
    category: str
    clean_text: str
    metadata: DocumentMetadata
    content_hash: str = Field(..., description="SHA-256 hash of clean_text for deduplication")
    version: int = Field(default=1, ge=1)
    is_duplicate: bool = Field(default=False)
    validation_errors: List[str] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=_utcnow)

    @property
    def is_valid(self) -> bool:
        """Returns True if the document passed quality checks without errors and is not duplicate."""
        return len(self.validation_errors) == 0 and not self.is_duplicate and len(self.clean_text.strip()) > 0
