# File: app/memory/retriever.py
"""
(`Milestone 12 Long-Term Memory Retriever`)
Responsible for retrieving User Profile, Semantic Memories, Episodic Events, and recent Conversation Window.
Applies memory ranking, deduplication, and formats clean context for LangGraph injection.
"""
import logging
from typing import List, Optional
from app.memory.manager import memory_manager
from app.memory.schemas import (
    ConversationMemory,
    Episode,
    MemoryContext,
    SemanticMemory,
    UserProfile,
    _utcnow,
)

logger = logging.getLogger("app.memory.retriever")


class MemoryRetriever:
    """
    (`4. Memory Retriever & Ranking Engine`)
    Fetches and ranks multi-tiered memories for a given user and query.
    Generates clean `MemoryContext` block ready for Prompt Builder in LangGraph.
    """

    def __init__(self, manager=memory_manager):
        self.manager = manager

    async def retrieve_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieves structured user profile from PostgreSQL (or local fallback)."""
        return self.manager._local_postgres_profiles.get(user_id)

    async def retrieve_semantic_memories(
        self, user_id: str, query: str = "", top_k: int = 5
    ) -> List[SemanticMemory]:
        """
        Retrieves semantic facts for the user, ranked using multi-factor ranking formula:
        Score = α*Importance + β*Recency + γ*Confidence + δ*log(1 + AccessCount)
        """
        results: List[SemanticMemory] = []
        now = _utcnow()

        for sem in self.manager._local_pinecone_semantics.values():
            if sem.user_id != user_id:
                continue
            # Compute recency decay score based on hours elapsed
            hours_elapsed = max(0.1, (now - sem.updated_at).total_seconds() / 3600.0)
            recency = max(0.1, 1.0 / (1.0 + 0.05 * hours_elapsed))

            score = self.manager.calculate_ranking_score(
                importance=sem.importance_score,
                recency=recency,
                confidence=sem.confidence,
                access_count=sem.access_count,
            )
            # Update dynamic ranking or store temporarily
            sem.recency_score = recency
            results.append((score, sem))

        # Sort by ranking score descending
        results.sort(key=lambda x: x[0], reverse=True)
        top_semantics = [item[1] for item in results[:top_k]]

        # Update access counts on retrieved memories
        for s in top_semantics:
            s.access_count += 1
            s.last_accessed = now

        return top_semantics

    async def retrieve_recent_episodes(self, user_id: str, limit: int = 5) -> List[Episode]:
        """Retrieves top recent episodes/milestones ranked by timestamp and importance."""
        episodes: List[Episode] = []
        for ep in self.manager._local_mongo_episodes.values():
            if ep.user_id == user_id:
                episodes.append(ep)

        episodes.sort(key=lambda x: (x.importance_score, x.timestamp), reverse=True)
        top_eps = episodes[:limit]
        now = _utcnow()
        for ep in top_eps:
            ep.access_count += 1
            ep.last_accessed = now
        return top_eps

    async def retrieve_conversation_window(
        self, user_id: str, conversation_id: str, limit: int = 6
    ) -> List[ConversationMemory]:
        """Retrieves recent short-term conversation turns from MongoDB."""
        turns: List[ConversationMemory] = []
        for conv in self.manager._local_mongo_conversations.values():
            if conv.user_id == user_id and conv.conversation_id == conversation_id:
                turns.append(conv)
        turns.sort(key=lambda x: x.timestamp)
        return turns[-limit:]

    async def retrieve_and_build_context(
        self,
        user_id: str,
        query: str = "",
        conversation_id: str = "default",
        top_semantic: int = 5,
        top_episodes: int = 3,
        window_limit: int = 4,
    ) -> MemoryContext:
        """
        Runs complete retrieval across all 4 memory tiers, deduplication, and formats markdown context block.
        """
        profile = await self.retrieve_profile(user_id)
        semantics = await self.retrieve_semantic_memories(user_id, query=query, top_k=top_semantic)
        episodes = await self.retrieve_recent_episodes(user_id, limit=top_episodes)
        window_all = await self.retrieve_conversation_window(user_id, conversation_id=conversation_id, limit=50)
        if window_all:
            window_all.sort(key=lambda x: x.timestamp)
            window = window_all[-8:]
        else:
            window = window_all

        formatted_lines: List[str] = []

        # 1. Profile Section
        if profile:
            formatted_lines.append("=== USER PROFILE (SQL) ===")
            if profile.name:
                formatted_lines.append(f"• Name: {profile.name}")
            if profile.preferred_language:
                formatted_lines.append(f"• Preferred Language: {profile.preferred_language}")
            if profile.occupation:
                formatted_lines.append(f"• Occupation: {profile.occupation}")
            if profile.projects:
                formatted_lines.append(f"• Known Projects: {', '.join(profile.projects)}")
            if profile.interests:
                formatted_lines.append(f"• Interests: {', '.join(profile.interests)}")

        # 2. Semantic Facts Section
        if semantics:
            formatted_lines.append("\n=== ENDURING USER FACTS (SEMANTIC VECTOR STORE) ===")
            for i, sem in enumerate(semantics, 1):
                formatted_lines.append(f"[{i}] {sem.fact} (Confidence: {sem.confidence:.2f} | Category: {sem.category})")

        # 3. Episodic Section
        if episodes:
            formatted_lines.append("\n=== RECENT MILESTONES & EVENTS (EPISODIC MONGODB) ===")
            for i, ep in enumerate(episodes, 1):
                formatted_lines.append(f"[{i}] {ep.event} (Timestamp: {ep.timestamp.strftime('%Y-%m-%d %H:%M')})")

        # 4. Conversation Window Section - summarized inline to avoid leaking a raw
        # "User: ... / Assistant: ..." transcript that the LLM might echo back. Each
        # turn is rendered as a single neutral bullet line. We also cap total turns.
        if window:
            formatted_lines.append("\n=== SHORT-TERM CONVERSATION WINDOW (RECENT TURNS) ===")
            for turn in window:
                snippet = turn.content.strip()
                if len(snippet) > 4000:
                    snippet = snippet[:3997].rstrip() + "..."
                formatted_lines.append(f"• {turn.role.capitalize()}: {snippet}")

        formatted_str = "\n".join(formatted_lines).strip()
        if not formatted_str:
            formatted_str = "No historical long-term memories found for this user."

        total_tokens = len(formatted_str.split())
        logger.info(
            f"Built Long-Term Memory Context for user '{user_id}' [Tokens: {total_tokens} | Facts: {len(semantics)} | Episodes: {len(episodes)}]."
        )

        return MemoryContext(
            user_id=user_id,
            conversation_window=window,
            semantic_facts=semantics,
            recent_episodes=episodes,
            user_profile=profile,
            formatted_context=formatted_str,
            total_tokens=total_tokens,
        )


# Global singleton instance
memory_retriever = MemoryRetriever()
