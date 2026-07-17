# File: app/ingestion/processor.py
import hashlib
import logging
import re
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup
from app.ingestion.schemas import DocumentMetadata, ProcessedDocument, RawDocument
from app.ingestion.parsers import file_parser_registry

logger = logging.getLogger("app.ingestion.processor")


class ContentProcessor:
    """
    (`8.3 Content Processor`)
    Unified processor converting raw HTML into clean, high-quality documents.
    Responsibilities: HTML parsing, Remove navigation/footer/ads, Clean text, Normalize formatting,
    Language detection, Metadata generation, Quality validation, Duplicate detection.
    """

    def __init__(self, min_word_count: int = 10, max_word_count: int = 500000):
        self.min_word_count = min_word_count
        self.max_word_count = max_word_count
        self._seen_content_hashes: Set[str] = set()

    def _clean_html(self, soup: BeautifulSoup) -> None:
        """Removes noise tags (`Remove navigation/footer/ads`)."""
        # Remove script, style, navigation, footer, header, aside, iframe, noscript, svg, form
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "svg", "form"]):
            element.decompose()

        # Remove elements by class or id matching common ad/nav patterns
        noise_patterns = re.compile(r"(sidebar|menu|nav|footer|header|advert|banner|cookie|popup|share|comment|breadcrumb)", re.I)
        for tag in soup.find_all(attrs={"class": noise_patterns}):
            tag.decompose()
        for tag in soup.find_all(attrs={"id": noise_patterns}):
            tag.decompose()

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extracts and normalizes text (`Clean text` / `Normalize formatting`)."""
        # Prefer main article or role=main if present
        main_content = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"}) or soup.body or soup
        text = main_content.get_text(separator="\n", strip=True)

        # Normalize line breaks and extra whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        # Remove consecutive repeated lines (common in menus)
        deduped_lines = []
        last_line = ""
        for line in lines:
            if line != last_line:
                deduped_lines.append(line)
                last_line = line

        return "\n".join(deduped_lines)

    def _detect_language(self, text: str) -> str:
        """Detects content language (`Language detection`)."""
        if not text or len(text.strip()) < 10:
            return "en"
        try:
            from langdetect import detect
            # Pass a sample of text for fast and reliable detection
            sample = text[:1000]
            return str(detect(sample))
        except Exception:
            return "en"

    def _generate_metadata(self, soup: BeautifulSoup, text: str, url: str) -> DocumentMetadata:
        """Extracts structural and semantic metadata (`Metadata generation`)."""
        # 1. Title
        title = ""
        title_tag = soup.find("title") or soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)
        if not title:
            title = url.split("/")[-1] or url

        # 2. Author & Description from meta tags
        author = None
        description = None
        keywords: List[str] = []

        meta_author = soup.find("meta", attrs={"name": re.compile(r"^author$", re.I)})
        if meta_author and meta_author.get("content"):
            author = str(meta_author["content"]).strip()

        meta_desc = soup.find("meta", attrs={"name": re.compile(r"^(description|og:description)$", re.I)})
        if meta_desc and meta_desc.get("content"):
            description = str(meta_desc["content"]).strip()

        meta_kw = soup.find("meta", attrs={"name": re.compile(r"^keywords$", re.I)})
        if meta_kw and meta_kw.get("content"):
            keywords = [k.strip() for k in str(meta_kw["content"]).split(",") if k.strip()]

        # 3. Word count & Links count
        words = text.split()
        word_count = len(words)
        links_count = len(soup.find_all("a", href=True))

        # 4. Language
        language = self._detect_language(text)

        return DocumentMetadata(
            title=title,
            author=author,
            language=language,
            word_count=word_count,
            description=description,
            keywords=keywords,
            extracted_links_count=links_count,
        )

    def _compute_content_hash(self, text: str) -> str:
        """Generates SHA-256 hash of clean text (`SHA-256 + Content Hash`)."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def process(self, raw_doc: RawDocument) -> ProcessedDocument:
        """
        Main entry point processing a raw HTML document into a ProcessedDocument.
        Performs validation and duplicate detection.
        """
        logger.debug(f"Processing raw document from '{raw_doc.url}'...")
        soup = BeautifulSoup(raw_doc.raw_html, "lxml")

        # 1. Clean noise elements
        self._clean_html(soup)

        # 2. Extract and normalize clean text
        clean_text = self._extract_text(soup)

        # 3. Compute content hash (`Duplicate detection`)
        content_hash = self._compute_content_hash(clean_text)
        is_dup = content_hash in self._seen_content_hashes
        if not is_dup:
            self._seen_content_hashes.add(content_hash)

        # 4. Generate metadata
        metadata = self._generate_metadata(soup, clean_text, raw_doc.url)

        # 5. Quality validation (`Quality validation`)
        validation_errors = []
        if metadata.word_count < self.min_word_count:
            validation_errors.append(f"Document word count ({metadata.word_count}) below minimum threshold ({self.min_word_count}).")
        if metadata.word_count > self.max_word_count:
            validation_errors.append(f"Document word count ({metadata.word_count}) exceeds maximum threshold ({self.max_word_count}).")
        if not clean_text.strip():
            validation_errors.append("Document extracted text is empty.")

        processed_doc = ProcessedDocument(
            url=raw_doc.url,
            title=metadata.title,
            source_name=raw_doc.source_name,
            category=raw_doc.category,
            clean_text=clean_text,
            metadata=metadata,
            content_hash=content_hash,
            version=1,
            is_duplicate=is_dup,
            validation_errors=validation_errors,
        )

        logger.info(
            f"Processed '{raw_doc.url}' -> Title: '{processed_doc.title}' | "
            f"Words: {metadata.word_count} | Valid: {processed_doc.is_valid} | Duplicate: {is_dup}"
        )
        return processed_doc

    async def process_file(self, file_bytes: bytes, filename: str, mime_type: str, source_name: str = "File Upload", category: str = "upload") -> ProcessedDocument:
        """
        Processes a binary file upload (PDF, DOCX, Image, Audio) using the appropriate parser
        and returns a ProcessedDocument compatible with the existing ingestion pipeline.
        """
        result = await file_parser_registry.parse(file_bytes, filename, mime_type)
        if result is None:
            return ProcessedDocument(
                url=f"file:///{filename}",
                title=filename,
                source_name=source_name,
                category=category,
                clean_text="",
                metadata=DocumentMetadata(title=filename, word_count=0),
                content_hash=self._compute_content_hash(""),
                version=1,
                is_duplicate=False,
                validation_errors=[f"No parser found for MIME type '{mime_type}'"],
            )

        text = result.text
        content_hash = self._compute_content_hash(text)
        is_dup = content_hash in self._seen_content_hashes
        if not is_dup:
            self._seen_content_hashes.add(content_hash)

        word_count = len(text.split())
        validation_errors = []
        if word_count < self.min_word_count and result.file_type not in ("image_description",):
            validation_errors.append(f"Extracted text word count ({word_count}) below minimum threshold ({self.min_word_count}).")
        if word_count > self.max_word_count:
            validation_errors.append(f"Extracted text word count ({word_count}) exceeds maximum threshold ({self.max_word_count}).")
        if not text.strip():
            validation_errors.append("Extracted text is empty.")

        meta = DocumentMetadata(
            title=result.title,
            word_count=word_count,
            description=f"Parsed from {filename} ({result.file_type})",
            keywords=[result.file_type, mime_type],
            custom=result.metadata,
        )

        return ProcessedDocument(
            url=f"file:///{filename}",
            title=result.title,
            source_name=source_name,
            category=category,
            clean_text=text,
            metadata=meta,
            content_hash=content_hash,
            version=1,
            is_duplicate=is_dup,
            validation_errors=validation_errors,
        )

    def reset_duplicate_tracker(self) -> None:
        """Clears in-memory duplicate tracker."""
        self._seen_content_hashes.clear()


content_processor = ContentProcessor()
