# File: app/rag/context_builder.py
import logging
from typing import Any, Dict, List, Optional
from app.rag.schemas import RAGContext, RetrievedChunk

logger = logging.getLogger("rag.context_builder")


class ContextBuilder:
    """
    (`9.5 Context Builder`)
    Responsible for converting retrieved chunks into a clean, structured, deduplicated
    context block ready for injection into LangGraph / LLM prompts.
    
    Steps:
    1. Deduplicate retrieved chunks (by chunk_id and exact text).
    2. Sort ordered logically (by score descending or document continuity).
    3. Enforce token budget limits (`max_tokens`) to prevent prompt overflow.
    4. Format clean headers with source citations (`[Source: ... | Relevance: ...]`).
    """

    def __init__(self, max_tokens: int = 3000):
        self.max_tokens = max_tokens

    def build_context(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
        max_tokens: Optional[int] = None,
        sort_by_document_order: bool = False,
    ) -> RAGContext:
        """
        Builds a structured RAGContext from retrieved chunks (`Chunks -> Ready for LangGraph`).
        """
        budget = max_tokens if max_tokens is not None else self.max_tokens

        if not retrieved_chunks:
            return RAGContext(
                query=query,
                retrieved_chunks=[],
                formatted_context="No relevant background documents found.",
                total_tokens=0,
            )

        # 1. Deduplicate by chunk_id and exact text
        seen_ids = set()
        seen_texts = set()
        unique_chunks: List[RetrievedChunk] = []

        for chunk in retrieved_chunks:
            t_clean = chunk.text.strip()
            if chunk.chunk_id not in seen_ids and t_clean not in seen_texts:
                seen_ids.add(chunk.chunk_id)
                seen_texts.add(t_clean)
                unique_chunks.append(chunk)

        # 2. Sort candidates
        if sort_by_document_order:
            # Sort by doc id then chunk index
            unique_chunks.sort(
                key=lambda x: (
                    x.document_id,
                    int(x.metadata.get("chunk_index", 0)),
                )
            )
        else:
            # Sort by relevance score descending
            unique_chunks.sort(key=lambda x: x.score, reverse=True)

        # 3. Assemble formatted text block while respecting max_tokens budget
        formatted_blocks: List[str] = []
        selected_chunks: List[RetrievedChunk] = []
        total_tokens = 0

        for idx, c in enumerate(unique_chunks, start=1):
            c_words = len(c.text.split())
            if total_tokens + c_words > budget and selected_chunks:
                logger.info(f"Token budget ({budget}) reached after including {len(selected_chunks)} chunks.")
                break

            selected_chunks.append(c)
            total_tokens += c_words

            # Extract human-readable citation info from metadata
            source_name = c.metadata.get("source_name", c.metadata.get("source", "Knowledge Repository"))
            doc_title = c.metadata.get("document_title", c.metadata.get("title", c.document_id))
            url = c.metadata.get("url", "N/A")
            score_str = f"{c.score:.3f}"

            header = f"[Context {idx} | Source: {source_name} - {doc_title} | Score: {score_str}]"
            if url and url != "N/A":
                header += f"\nURL: {url}"

            block = f"{header}\n{c.text.strip()}"
            formatted_blocks.append(block)

        formatted_context = "\n\n---\n\n".join(formatted_blocks)

        logger.info(
            f"Built RAG context for query '{query[:30]}...' with {len(selected_chunks)} chunks ({total_tokens} tokens)."
        )
        return RAGContext(
            query=query,
            retrieved_chunks=selected_chunks,
            formatted_context=formatted_context,
            total_tokens=total_tokens,
        )


# Global singleton instance
context_builder = ContextBuilder()
