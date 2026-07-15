# File: app/memory/pipeline.py
"""
(`Milestone 12 Long-Term Memory Pipeline Facade`)
Single unified orchestration layer coordinating Extractor, Manager, Retriever, and Summarizer.
Plugs directly into LangGraph (`memory_retrieval_node`) without autonomous side-effects.
"""
import logging
from typing import Optional
from app.memory.extractor import MemoryExtractor
from app.memory.manager import memory_manager, MemoryManager
from app.memory.retriever import memory_retriever, MemoryRetriever
from app.memory.summarizer import memory_summarizer, MemorySummarizer
from app.memory.schemas import (
    MemoryAction,
    MemoryContext,
    MemoryExtractionItem,
    MemoryExtractionResult,
    MemoryType,
)

logger = logging.getLogger("app.memory.pipeline")


class MemoryPipeline:
    """
    (`6. Memory Orchestration Pipeline`)
    Provides clean facade methods for LangGraph integration:
    • `retrieve_context(user_id, query, conversation_id)` -> `MemoryContext`
    • `process_turn(user_query, ai_response, user_id, conversation_id)` -> `MemoryExtractionResult`
    """

    def __init__(
        self,
        manager: MemoryManager = memory_manager,
        retriever: MemoryRetriever = memory_retriever,
        summarizer: MemorySummarizer = memory_summarizer,
    ):
        self.manager = manager
        self.retriever = retriever
        self.summarizer = summarizer
        self.extractor = MemoryExtractor()

    async def retrieve_context(
        self, user_id: str, query: str = "", conversation_id: str = "default"
    ) -> MemoryContext:
        """
        Called by LangGraph `memory_retrieval_node` when requested by the Intelligent Router.
        Retrieves User Profile, Semantic Facts, Episodes, and Conversation Window.
        """
        logger.info(f"MemoryPipeline retrieving context for user '{user_id}' on query '{query[:30]}...'")
        return await self.retriever.retrieve_and_build_context(
            user_id=user_id,
            query=query,
            conversation_id=conversation_id,
        )

    async def process_turn(
        self,
        user_query: str,
        ai_response: Optional[str] = None,
        user_id: str = "default-user",
        conversation_id: str = "default-session",
    ) -> MemoryExtractionResult:
        """
        Called after LangGraph completes generation (or during turn ingestion) to extract and persist memories.
        Handles conflict resolution, deduplication, and summarization checks.
        """
        # Step 1: Retrieve existing profile and semantics for conflict checking
        profile = await self.retriever.retrieve_profile(user_id)
        semantics = await self.retriever.retrieve_semantic_memories(user_id, top_k=20)

        # Step 2: Run extraction intelligence
        result = await self.extractor.extract(
            user_query=user_query,
            ai_response=ai_response,
            existing_profile=profile,
            existing_semantic=semantics,
        )

        # Step 3: Process extracted items with conflict resolution
        if result.should_remember and result.extracted_items:
            for item in result.extracted_items:
                if item.action == MemoryAction.IGNORE:
                    continue

                # Check conflict resolution for semantic overrides
                if item.memory_type == MemoryType.SEMANTIC and item.action in (MemoryAction.CREATE, MemoryAction.UPDATE):
                    resolved = await self.manager.resolve_conflict(user_id, item, semantics)
                    if resolved:
                        continue

                # Persist new or updated memory
                await self.manager.create_memory(item, user_id)

        # Step 4: Always record conversation turn
        turn_item = MemoryExtractionItem(
            action=MemoryAction.CREATE,
            memory_type=MemoryType.CONVERSATION,
            content=user_query,
            key=conversation_id,
            value="user",
            importance_score=0.3,
        )
        await self.manager.create_memory(turn_item, user_id)

        if ai_response:
            ai_item = MemoryExtractionItem(
                action=MemoryAction.CREATE,
                memory_type=MemoryType.CONVERSATION,
                content=ai_response,
                key=conversation_id,
                value="assistant",
                importance_score=0.3,
            )
            await self.manager.create_memory(ai_item, user_id)

        # Step 5: Check if summarization is needed
        await self.summarizer.summarize_if_needed(user_id, conversation_id, max_threshold=8)

        return result


# Global singleton instance
memory_pipeline = MemoryPipeline()
