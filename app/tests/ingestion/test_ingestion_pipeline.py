# File: app/tests/ingestion/test_ingestion_pipeline.py
import pytest
from app.ingestion import (
    CrawlStatus,
    PriorityLevel,
    RawDocument,
    TrustLevel,
    content_processor,
    document_manager,
    ingestion_pipeline,
    source_registry,
    web_crawler,
)
from app.repositories.postgres.document_repository import DocumentRepository


@pytest.mark.asyncio
async def test_source_registry():
    """Verify that source registry loads configuration from YAML correctly and enforces allowed paths."""
    # Check that tier1 sources like Python Documentation were loaded
    py_source = source_registry.get_source("Python Documentation")
    assert py_source is not None
    assert py_source.trust_level == TrustLevel.TIER_1
    assert py_source.priority == PriorityLevel.HIGH
    assert py_source.enabled is True

    # Check path allowances/exclusions
    assert source_registry.is_url_allowed("Python Documentation", "https://docs.python.org/3/tutorial/index.html") is True
    assert source_registry.is_url_allowed("Python Documentation", "https://docs.python.org/3/whatsnew/changelog.html") is False


@pytest.mark.asyncio
async def test_content_processor():
    """Verify HTML cleaning, text extraction, noise removal, and metadata generation."""
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FastAPI Advanced Tutorial</title>
        <meta name="author" content="Sebastián Ramírez">
        <meta name="description" content="A detailed guide to building production-ready async web APIs with FastAPI and Pydantic.">
        <meta name="keywords" content="fastapi, python, async, pydantic, api">
    </head>
    <body>
        <nav class="navbar"><a href="/home">Home</a><a href="/docs">Docs</a></nav>
        <div id="sidebar" class="menu">Sidebar ads and links to remove</div>
        <main>
            <h1>FastAPI Advanced Tutorial</h1>
            <p>FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints.</p>
            <p>The key features are fast performance, fast to code, fewer bugs, intuitive IDE support, robust validation, and OpenAPI schema generation.</p>
            <p>Let's write some asynchronous dependencies and database repositories using clean architecture best practices.</p>
        </main>
        <footer id="footer">Copyright 2026 Antigravity Bot</footer>
        <script>console.log("This script tag should be removed completely.");</script>
    </body>
    </html>
    """

    raw_doc = RawDocument(
        url="https://fastapi.tiangolo.com/tutorial/advanced/",
        source_name="FastAPI Documentation",
        category="programming",
        raw_html=sample_html,
        http_status=200,
    )

    processed_doc = content_processor.process(raw_doc)
    assert processed_doc.title == "FastAPI Advanced Tutorial"
    assert processed_doc.metadata.author == "Sebastián Ramírez"
    assert "fastapi" in processed_doc.metadata.keywords
    assert "Copyright" not in processed_doc.clean_text
    assert "console.log" not in processed_doc.clean_text
    assert "Sidebar ads" not in processed_doc.clean_text
    assert "modern, fast" in processed_doc.clean_text
    assert processed_doc.is_valid is True
    assert len(processed_doc.content_hash) == 64


@pytest.mark.asyncio
async def test_document_manager_and_deduplication():
    """Verify document manager versioning (v1 -> v2) and exact checksum duplicate detection."""
    # Use stub mode repository
    stub_repo = DocumentRepository(session=None)
    document_manager.set_repository(stub_repo)

    # 1. Save initial v1 document
    html_v1 = """
    <html><title>Python GIL Overview</title>
    <body><main>The Global Interpreter Lock (GIL) is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once.</main></body>
    </html>
    """
    raw_v1 = RawDocument(
        url="https://docs.python.org/3/c-api/init.html",
        source_name="Python Documentation",
        category="programming",
        raw_html=html_v1,
    )
    processed_v1 = content_processor.process(raw_v1)
    saved_v1 = await document_manager.save_document(processed_v1)

    assert saved_v1.version == 1
    assert saved_v1.is_duplicate is False

    # 2. Re-upload exact same HTML -> should be detected as duplicate without bumping version
    processed_v1_dup = content_processor.process(raw_v1)
    saved_dup = await document_manager.save_document(processed_v1_dup)

    assert saved_dup.is_duplicate is True
    assert saved_dup.version == 1
    assert await stub_repo.count() == 1

    # 3. Upload modified HTML (v2) -> should bump version to 2
    html_v2 = """
    <html><title>Python GIL Overview (Updated)</title>
    <body><main>In Python 3.13+, subinterpreters and experimental no-GIL builds allow true multi-threaded parallel execution across CPU cores without locking bytecodes.</main></body>
    </html>
    """
    raw_v2 = RawDocument(
        url="https://docs.python.org/3/c-api/init.html",
        source_name="Python Documentation",
        category="programming",
        raw_html=html_v2,
    )
    processed_v2 = content_processor.process(raw_v2)
    saved_v2 = await document_manager.save_document(processed_v2)

    assert saved_v2.version == 2
    assert saved_v2.is_duplicate is False
    assert (await stub_repo.find_by_url("https://docs.python.org/3/c-api/init.html")).metadata["version"] == 2


@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    """Verify end-to-end ingestion pipeline via ingest_raw_html."""
    stub_repo = DocumentRepository(session=None)
    ingestion_pipeline.inject_repository(stub_repo)

    doc = await ingestion_pipeline.ingest_raw_html(
        url="https://docs.sqlalchemy.org/en/20/orm/quickstart.html",
        raw_html="<html><title>SQLAlchemy Quickstart</title><main>SQLAlchemy ORM allows mapping Python classes to database tables using DeclarativeBase and async engine sessions.</main></html>",
        source_name="SQLAlchemy Documentation",
        category="programming",
    )

    assert doc.title == "SQLAlchemy Quickstart"
    assert doc.version == 1
    assert doc.is_valid is True
    assert await stub_repo.count() == 1
