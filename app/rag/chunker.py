# File: app/rag/chunker.py
import logging
import re
from typing import Any, Dict, List, Optional, Union
from uuid import uuid5, NAMESPACE_URL
from app.domain.knowledge import Document
from app.ingestion.schemas import ProcessedDocument
from app.rag.schemas import ChunkSchema

logger = logging.getLogger("rag.chunker")


class SemanticRecursiveChunker:
    """
    (`9.1 Chunker`)
    Responsible for converting processed documents from the Knowledge Repository into structured,
    searchable chunks (`Document -> Chunks`).
    
    Features:
    - Recursive splitting by semantic boundaries (`\\n\\n`, `\\n`, `. `, ` `).
    - Full metadata inheritance from parent document.
    - Stable deterministic `chunk_id` generation using UUID5 (`doc_id` + `chunk_index`).
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 60):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Union[Document, ProcessedDocument]) -> List[ChunkSchema]:
        """
        Splits a single document into a list of ChunkSchema instances with inherited metadata.
        """
        doc_id = str(getattr(document, "id", getattr(document, "document_id", "")))
        doc_title = str(getattr(document, "title", ""))
        doc_text = str(getattr(document, "content", getattr(document, "clean_text", "")))
        doc_meta = getattr(document, "metadata", {})
        if hasattr(doc_meta, "model_dump"):
            doc_meta = doc_meta.model_dump()

        if not doc_text.strip():
            logger.warning(f"Document '{doc_id}' contains empty text. No chunks created.")
            return []

        # Perform recursive semantic splitting
        text_chunks = self._split_text_recursive(doc_text, self.chunk_size, self.chunk_overlap)
        
        chunks: List[ChunkSchema] = []
        for index, text_segment in enumerate(text_chunks):
            # Generate deterministic chunk_id
            chunk_id = str(uuid5(NAMESPACE_URL, f"{doc_id}::chunk::{index}"))
            token_count = len(text_segment.split())

            # Inherit and enrich metadata
            chunk_metadata = {
                **doc_meta,
                "document_id": doc_id,
                "document_title": doc_title,
                "chunk_index": index,
                "token_count": token_count,
            }

            chunk = ChunkSchema(
                chunk_id=chunk_id,
                document_id=doc_id,
                chunk_index=index,
                text=text_segment,
                token_count=token_count,
                metadata=chunk_metadata,
            )
            chunks.append(chunk)

        logger.info(f"Chunked document '{doc_id}' ({doc_title}) into {len(chunks)} chunks.")
        return chunks

    def chunk_documents(self, documents: List[Union[Document, ProcessedDocument]]) -> List[ChunkSchema]:
        """
        Batch chunks multiple documents into a single flattened list of ChunkSchema instances.
        """
        all_chunks: List[ChunkSchema] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

    def _split_text_recursive(self, text: str, max_length: int, overlap: int) -> List[str]:
        """
        Recursively splits text on semantic separators (`## headers`, `\\n\\n`, `\\n`, `. `).
        Preserves code blocks intact, respects markdown headings as chunk boundaries.
        """
        words = text.split()
        if len(words) <= max_length:
            return [text.strip()] if text.strip() else []

        chunks: List[str] = []
        # Phase 1: Try splitting on markdown headings first (strongest semantic boundary)
        heading_split = re.split(r'(?=^#{1,4}\s)', text, flags=re.MULTILINE)
        if len(heading_split) > 1:
            for section in heading_split:
                section = section.strip()
                if not section:
                    continue
                section_words = section.split()
                if len(section_words) <= max_length:
                    chunks.append(section)
                else:
                    # Phase 2: Split by code blocks (preserve them intact)
                    chunks.extend(self._split_by_code_blocks(section, max_length, overlap))
        else:
            chunks.extend(self._split_by_code_blocks(text, max_length, overlap))

        # Phase 3: Deduplicate identical chunks caused by overlap
        cleaned: List[str] = []
        for c in chunks:
            c_str = c.strip()
            if c_str and (not cleaned or cleaned[-1] != c_str):
                cleaned.append(c_str)
        return cleaned

    def _split_by_code_blocks(self, text: str, max_length: int, overlap: int) -> List[str]:
        """Split text while preserving code blocks (```...```) as atomic units."""
        parts = re.split(r'(```[\s\S]*?```)', text)
        chunks: List[str] = []
        current: List[str] = []

        def _flush():
            nonlocal current
            if current:
                chunk = "\n\n".join(current).strip()
                if chunk:
                    chunks.append(chunk)
                current = []

        for part in parts:
            if not part.strip():
                continue
            if part.startswith("```") and part.endswith("```"):
                # Code block is atomic — if it fits in current chunk, add it
                if sum(len(t.split()) for t in current) + len(part.split()) <= max_length:
                    current.append(part)
                else:
                    _flush()
                    if len(part.split()) <= max_length:
                        current.append(part)
                    else:
                        # Code block too large for a single chunk — still keep it whole
                        chunks.append(part.strip())
            else:
                # Regular text — split by paragraphs
                paragraphs = [p.strip() for p in re.split(r'\n\s*\n', part) if p.strip()]
                for para in paragraphs:
                    para_words = para.split()
                    cur_words = sum(len(t.split()) for t in current)
                    if cur_words + len(para_words) <= max_length:
                        current.append(para)
                    else:
                        _flush()
                        if len(para_words) <= max_length:
                            current.append(para)
                        else:
                            # Long paragraph — sentence-split
                            sentences = re.split(r'(?<=[.!?])\s+', para)
                            for sent in sentences:
                                sent_words = sent.split()
                                cur_w = sum(len(t.split()) for t in current)
                                if cur_w + len(sent_words) <= max_length:
                                    current.append(sent)
                                else:
                                    _flush()
                                    current.append(sent)
        _flush()

        # Handle overlap between adjacent chunks
        if overlap > 0 and len(chunks) > 1:
            overlapped: List[str] = []
            for i, ch in enumerate(chunks):
                if i > 0:
                    prev_words = chunks[i - 1].split()
                    overlap_words = prev_words[-overlap:] if len(prev_words) > overlap else prev_words
                    ch = " ".join(overlap_words) + " " + ch if overlap_words else ch
                overlapped.append(ch.strip())
            return overlapped
        return chunks


# Global singleton instance
chunker = SemanticRecursiveChunker()
