# File: app/memory/summarizer.py
"""
(`Milestone 12 Long-Term Memory Summarizer`)
Responsible for Conversation Summaries, memory compression, and context budgeting.
When a conversation exceeds a turn threshold, generates a condensed summary, stores it in MongoDB,
and archives the granular raw message turns to preserve token headroom.
"""
import logging
import uuid
from typing import List, Optional
from app.ai.llm.llm_manager import llm_manager
from app.memory.manager import memory_manager
from app.memory.schemas import (
    ConversationMemory,
    MemoryAction,
    MemoryExtractionItem,
    MemoryType,
    _utcnow,
)

logger = logging.getLogger("app.memory.summarizer")


class MemorySummarizer:
    """
    (`5. Conversation Summarizer & Compression Engine`)
    Monitors short-term conversation length (`ConversationMemory`) and compresses historical
    turns into an enduring `SUMMARY` record when exceeding `max_threshold`.
    """

    def __init__(self, manager=memory_manager):
        self.manager = manager

    async def summarize_if_needed(
        self, user_id: str, conversation_id: str, max_threshold: int = 8
    ) -> Optional[ConversationMemory]:
        """
        Checks if current conversation turns exceed `max_threshold`. If so, summarizes existing turns,
        stores the summary in MongoDB (`SUMMARY` type), and archives raw detailed history.
        """
        turns: List[ConversationMemory] = []
        for conv in list(self.manager._local_mongo_conversations.values()):
            if conv.user_id == user_id and conv.conversation_id == conversation_id:
                turns.append(conv)

        turns.sort(key=lambda x: x.timestamp)
        if len(turns) <= max_threshold:
            return None

        logger.info(f"Conversation '{conversation_id}' exceeded {max_threshold} turns ({len(turns)} turns). Compressing...")

        # Build raw dialogue transcript for summarization
        transcript = "\n".join([f"{'User' if t.role == 'user' else 'Assistant'}: {t.content}" for t in turns[:-2]])

        summary_text = await self._generate_summary(transcript)
        now = _utcnow()
        summary_id = f"sum-{uuid.uuid4().hex[:12]}"

        # Create SUMMARY record
        summary_record = ConversationMemory(
            id=summary_id,
            conversation_id=conversation_id,
            user_id=user_id,
            role="system_summary",
            content=summary_text,
            timestamp=now,
            importance_score=0.85,
            access_count=1,
        )

        # Store summary inside local store and MongoDB
        self.manager._local_mongo_conversations[summary_id] = summary_record
        try:
            coll = self.manager.get_collection("conversation_summaries") if hasattr(self.manager, "get_collection") else None
            if coll:
                await coll.insert_one(summary_record.model_dump(mode="json"))
        except Exception as exc:
            logger.debug(f"MongoDB summary insert skipped ({exc}). Stored in memory.")

        # Archive/remove old detailed turns that were summarized (keep latest 2 turns for active context)
        turns_to_archive = turns[:-2]
        for old_t in turns_to_archive:
            if old_t.id in self.manager._local_mongo_conversations:
                del self.manager._local_mongo_conversations[old_t.id]

        logger.info(f"Compressed {len(turns_to_archive)} historical turns into summary: '{summary_text[:60]}...'")
        return summary_record

    async def _generate_summary(self, transcript: str) -> str:
        """Invokes Groq LLM to summarize previous dialogue turns."""
        prompt = f"""Summarize the key discussion points, technical context, and decisions from this conversation window concisely in 2-3 sentences.
TRANSCRIPT:
{transcript}

SUMMARY:"""
        try:
            full_prompt = f"System: You are a helpful conversation summarizer. Keep summaries factual and under 60 words.\n\nUser: {prompt}"
            resp = await llm_manager.generate(
                messages=full_prompt,
                max_tokens=120,
                temperature=0.2,
            )
            summary = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            return summary.strip()
        except Exception as exc:
            logger.warning(f"LLM summarization failed ({exc}). Using fallback extractive summary.")
            first_line = transcript.split("\n")[0] if transcript else "Historical conversation session"
            return f"Summary of session discussing: {first_line[:80]}..."


# Global singleton instance
memory_summarizer = MemorySummarizer()
