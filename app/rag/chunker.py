# File: app/rag/chunker.py
import logging
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
        Recursively splits text on semantic separators (`\\n\\n`, `\\n`, `. `, ` `) up to max_length words.
        """
        words = text.split()
        if len(words) <= max_length:
            return [text.strip()] if text.strip() else []

        # Split by paragraph first if possible
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_chunk_words: List[str] = []

        for para in paragraphs:
            para_words = para.split()
            if len(current_chunk_words) + len(para_words) <= max_length:
                current_chunk_words.extend(para_words)
            else:
                if current_chunk_words:
                    chunks.append(" ".join(current_chunk_words))
                    # Handle overlap
                    overlap_words = current_chunk_words[-overlap:] if overlap > 0 else []
                    current_chunk_words = overlap_words + para_words
                else:
                    # Paragraph itself exceeds max_length, split sentences/words sliding window
                    step = max(1, max_length - overlap)
                    for i in range(0, len(para_words), step):
                        slice_words = para_words[i : i + max_length]
                        if slice_words:
                            chunks.append(" ".join(slice_words))
                    current_chunk_words = []

        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))

        # Deduplicate identical chunks caused by overlap
        cleaned_chunks: List[str] = []
        for c in chunks:
            c_str = c.strip()
            if c_str and (not cleaned_chunks or cleaned_chunks[-1] != c_str):
                cleaned_chunks.append(c_str)

        return cleaned_chunks


# Global singleton instance
chunker = SemanticRecursiveChunker()
