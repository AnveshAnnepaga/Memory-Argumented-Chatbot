import logging
import io
from typing import Optional

logger = logging.getLogger("app.ingestion.parsers.pdf")

try:
    import fitz
    _FITZ_AVAILABLE = True
except ImportError:
    _FITZ_AVAILABLE = False
    logger.info("PyMuPDF not installed. PDF parsing will be unavailable.")


class PDFParser:
    """Extracts text and metadata from PDF files using PyMuPDF (fitz)."""

    def parse(self, file_bytes: bytes, filename: str = "") -> Optional["FileParseResult"]:
        from app.ingestion.parsers import FileParseResult

        if not _FITZ_AVAILABLE:
            logger.warning("Cannot parse PDF: PyMuPDF (fitz) not installed. Run: pip install PyMuPDF")
            return None

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF '{filename}': {e}")
            return None

        pages_text = []
        full_metadata = {}

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            pages_text.append(text)

        # Extract PDF metadata
        pdf_meta = doc.metadata or {}
        title = pdf_meta.get("title", "") or filename.replace(".pdf", "").replace("_", " ").replace("-", " ").title()
        author = pdf_meta.get("author", "")
        subject = pdf_meta.get("subject", "")
        page_count = len(doc)

        full_metadata = {
            "author": author,
            "subject": subject,
            "page_count": page_count,
            "pdf_version": pdf_meta.get("format", ""),
        }
        doc.close()

        text = "\n\n".join(pages_text).strip()
        if not text:
            logger.warning(f"No text extracted from PDF '{filename}'")
            return None

        logger.info(f"Parsed PDF '{filename}': {page_count} pages, {len(text.split())} words")
        return FileParseResult(
            text=text,
            title=title,
            file_type="pdf",
            metadata=full_metadata,
            raw_bytes=file_bytes,
        )


pdf_parser = PDFParser()
