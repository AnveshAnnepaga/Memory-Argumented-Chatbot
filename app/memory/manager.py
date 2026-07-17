# File: app/memory/manager.py
"""
(`Milestone 12 Long-Term Memory Manager`)
Central CRUD, conflict resolution, ranking scoring, and storage dispatch layer.
Routes memories to MongoDB (Conversation/Episodic/Summary via ConversationRepository),
PostgreSQL (Profile via UserProfileRepository), Pinecone (Semantic embeddings),
and Neo4j (Knowledge Graph relationships).
"""
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database.mongodb import mongo_manager
from app.database.postgres import postgres_manager
from app.database.pinecone import pinecone_manager
from app.database.neo4j import neo4j_manager
from app.rag.embedder import embedder
from app.repositories.mongodb.conversation_repository import ConversationRepository
from app.repositories.postgres.profile_repository import UserProfileRepository
from app.domain.conversation import Conversation, Message
from app.memory.schemas import (
    ConversationMemory,
    Episode,
    MemoryAction,
    MemoryExtractionItem,
    MemoryType,
    SemanticMemory,
    UserProfile as MemoryUserProfile,
    _utcnow,
)

logger = logging.getLogger("app.memory.manager")


class MemoryManager:
    """
    (`3. Memory Manager CRUD & Scoring Layer`)
    Coordinates memory persistence across NoSQL, SQL, Vector, and Graph storage engines.
    Maintains memory importance, freshness (recency), confidence scores, and access statistics.
    """

    def __init__(self):
        # Repository-backed persistence with in-memory fallback
        self.conversation_repo = ConversationRepository()
        self.profile_repo = UserProfileRepository()
        self._local_mongo_episodes: Dict[str, Episode] = {}
        self._local_mongo_conversations: Dict[str, ConversationMemory] = {}
        self._local_postgres_profiles: Dict[str, MemoryUserProfile] = {}
        self._local_pinecone_semantics: Dict[str, SemanticMemory] = {}

    @property
    def _local_pinecone_vectors(self) -> Dict[str, SemanticMemory]:
        return self._local_pinecone_semantics

    def calculate_ranking_score(
        self,
        importance: float,
        confidence: float,
        access_count: int,
        recency: Optional[float] = None,
        timestamp_dt: Optional[datetime] = None,
        alpha: float = 0.35,
        beta: float = 0.30,
        gamma: float = 0.25,
        delta: float = 0.10,
        **kwargs: Any,
    ) -> float:
        """
        (`Memory Ranking Formula`)
        Computes composite ranking score across importance, recency, confidence, and access frequency.
        Score = α*Importance + β*Recency + γ*Confidence + δ*log(1 + AccessCount)
        """
        if recency is None:
            if timestamp_dt:
                now = _utcnow()
                hours_ago = max(0.0, (now - timestamp_dt).total_seconds() / 3600.0)
                recency = max(0.1, 1.0 / (1.0 + hours_ago / 168.0))
            else:
                recency = 1.0

        access_boost = min(1.0, math.log1p(max(0, access_count)) / 3.0)
        score = (alpha * importance) + (beta * recency) + (gamma * confidence) + (delta * access_boost)
        return round(min(1.0, max(0.0, score)), 4)

    compute_ranking_score = calculate_ranking_score

    async def create_memory(self, item: MemoryExtractionItem, user_id: str) -> Any:
        """Dispatches validated extraction item to appropriate storage tier."""
        mem_id = f"mem-{uuid.uuid4().hex[:12]}"
        now = _utcnow()

        if item.memory_type == MemoryType.PROFILE:
            return await self._store_profile_attribute(user_id, item)
        elif item.memory_type == MemoryType.SEMANTIC:
            return await self._store_semantic_memory(mem_id, user_id, item, now)
        elif item.memory_type == MemoryType.EPISODIC:
            return await self._store_episodic_memory(mem_id, user_id, item, now)
        elif item.memory_type == MemoryType.CONVERSATION:
            return await self._store_conversation_memory(mem_id, user_id, item, now)
        else:
            logger.warning(f"Unsupported memory type '{item.memory_type}' for creation.")
            return None

    async def _store_profile_attribute(self, user_id: str, item: MemoryExtractionItem) -> MemoryUserProfile:
        """Stores or updates structured profile attribute in PostgreSQL via UserProfileRepository."""
        profile = self._local_postgres_profiles.get(user_id) or MemoryUserProfile(user_id=user_id)
        key = item.key or "occupation"
        val = item.value or item.content

        if hasattr(profile, key) and key not in ("interests", "projects"):
            setattr(profile, key, val)
        elif key in ("interests", "projects") or "project" in item.content.lower():
            target_list = getattr(profile, "projects" if "project" in key.lower() else "interests")
            if val not in target_list:
                target_list.append(val)
        elif key == "preferred_language":
            profile.preferred_language = val
        elif key == "name":
            profile.name = val

        profile.updated_at = _utcnow()
        profile.access_count += 1
        self._local_postgres_profiles[user_id] = profile

        # Persist to PostgreSQL via UserProfileRepository
        try:
            from app.domain.user import UserProfile as DomainUserProfile
            domain_profile = DomainUserProfile(
                user_id=user_id,
                full_name=profile.name or profile.full_name,
                preferences={
                    "name": profile.name,
                    "occupation": profile.occupation,
                    "preferred_language": profile.preferred_language,
                    "timezone": profile.timezone,
                    "interests": profile.interests,
                    "projects": profile.projects,
                },
            )
            async for session in postgres_manager.get_session():
                if session is not None:
                    existing = await self.profile_repo.retrieve(user_id, session=session)
                    if existing:
                        await self.profile_repo.update(user_id, {
                            "full_name": domain_profile.full_name,
                            "preferences": domain_profile.preferences,
                        }, session=session)
                    else:
                        await self.profile_repo.create(domain_profile, session=session)
                break
        except Exception as exc:
            logger.debug(f"UserProfileRepository live sync skipped ({exc}). Using in-memory profile store.")

        logger.info(f"Updated UserProfile for user '{user_id}': {key} -> {val}")
        return profile

    async def _store_semantic_memory(
        self, mem_id: str, user_id: str, item: MemoryExtractionItem, now: datetime
    ) -> SemanticMemory:
        """Stores permanent user fact embedded in Pinecone and Neo4j relationship."""
        category = item.key if item.key and item.key in ("preferred_language", "occupation", "stack", "skill") else "preference"
        sem = SemanticMemory(
            id=mem_id,
            user_id=user_id,
            fact=item.content,
            category=category,
            confidence=item.confidence,
            importance_score=item.importance_score,
            recency_score=1.0,
            access_count=1,
            created_at=now,
            updated_at=now,
            last_accessed=now,
        )
        self._local_pinecone_semantics[mem_id] = sem

        # Attempt vector embedding & Pinecone index upsert if live
        try:
            if not pinecone_manager.stub_mode and pinecone_manager.index:
                vectors = embedder.embed_chunks([sem.fact])
                if vectors and len(vectors) > 0:
                    payload = [
                        {
                            "id": mem_id,
                            "values": vectors[0].values,
                            "metadata": {
                                "user_id": user_id,
                                "fact": sem.fact,
                                "category": sem.category,
                                "confidence": sem.confidence,
                                "importance_score": sem.importance_score,
                                "type": "SEMANTIC",
                            },
                        }
                    ]
                    pinecone_manager.index.upsert(vectors=payload, namespace="long-term-memory")
        except Exception as exc:
            logger.debug(f"Pinecone live vector upsert skipped ({exc}). Using in-memory semantic store.")

        # Store relationship in Neo4j Knowledge Graph
        try:
            driver = neo4j_manager.get_client()
            if driver is not None:
                async with driver.session() as neo4j_session:
                    fact_text = sem.fact
                    concept = self._extract_concept_from_fact(fact_text, category, item.value)
                    await neo4j_session.run(
                        """
                        MERGE (u:User {id: $user_id})
                        MERGE (c:Concept {name: $concept, category: $category})
                        MERGE (u)-[r:KNOWS {fact_id: $fact_id}]->(c)
                        SET r.confidence = $confidence,
                            r.importance = $importance,
                            r.fact = $fact,
                            r.updated_at = datetime()
                        """,
                        user_id=user_id,
                        concept=concept,
                        category=category,
                        fact_id=mem_id,
                        confidence=sem.confidence,
                        importance=sem.importance_score,
                        fact=sem.fact,
                    )
                    logger.info(f"Stored Neo4j relationship: User[{user_id}] -> Concept[{concept}]")
        except Exception as exc:
            logger.debug(f"Neo4j relationship storage skipped ({exc}).")

        logger.info(f"Created SemanticMemory [ID: {mem_id}] for user '{user_id}': {sem.fact}")
        return sem

    def _extract_concept_from_fact(self, fact: str, category: str, val: Optional[str] = None) -> str:
        """Extracts the main concept from a fact for Neo4j node naming."""
        if val and val != "Project":
            return val
        prefixes = ["User prefers ", "User fact: ", "User ", "prefers "]
        text = fact
        for p in prefixes:
            if text.startswith(p):
                text = text[len(p):]
                break
        # Take first meaningful word pair
        words = text.split()
        if len(words) >= 2:
            return " ".join(words[:2]).rstrip(".,!?")
        return words[0].rstrip(".,!?") if words else fact[:20]

    async def _store_episodic_memory(
        self, mem_id: str, user_id: str, item: MemoryExtractionItem, now: datetime
    ) -> Episode:
        """Stores significant milestone or event inside MongoDB (`Episode`)."""
        ep = Episode(
            id=mem_id,
            user_id=user_id,
            event=item.content,
            context={"key": item.key, "value": item.value, "reasoning": item.reasoning},
            confidence=item.confidence,
            importance_score=item.importance_score,
            recency_score=1.0,
            access_count=1,
            timestamp=now,
            last_accessed=now,
        )
        self._local_mongo_episodes[mem_id] = ep

        # Attempt live MongoDB document insert
        try:
            coll = mongo_manager.get_collection("episodic_memories")
            if coll is not None:
                await coll.insert_one(ep.model_dump(mode="json"))
        except Exception as exc:
            logger.debug(f"MongoDB live insert skipped ({exc}). Using local episode store.")

        logger.info(f"Created Episode [ID: {mem_id}] for user '{user_id}': {ep.event}")
        return ep

    async def _store_conversation_memory(
        self, mem_id: str, user_id: str, item: MemoryExtractionItem, now: datetime
    ) -> ConversationMemory:
        """Stores conversation turn in MongoDB via ConversationRepository."""
        conversation_id = item.key or f"sess-{user_id}"
        role = "user" if item.value != "assistant" else "assistant"

        conv = ConversationMemory(
            id=mem_id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=item.content,
            timestamp=now,
            importance_score=item.importance_score,
            access_count=1,
        )
        self._local_mongo_conversations[mem_id] = conv

        # Persist to MongoDB via ConversationRepository + Message
        try:
            message = Message(
                id=mem_id,
                conversation_id=conversation_id,
                role=role,
                content=item.content,
                created_at=now,
            )
            coll = mongo_manager.get_collection("messages")
            if coll is not None:
                await coll.insert_one(message.model_dump(mode="json"))

            # Ensure conversation document exists
            conv_coll = mongo_manager.get_collection("conversations")
            if conv_coll is not None:
                existing = await conv_coll.find_one({"id": conversation_id})
                if existing is None:
                    conversation = Conversation(
                        id=conversation_id,
                        user_id=user_id,
                        title=f"Conversation {conversation_id[:8]}",
                    )
                    await conv_coll.insert_one(conversation.model_dump(mode="json"))
                else:
                    await conv_coll.update_one(
                        {"id": conversation_id},
                        {"$set": {"updated_at": now, "last_active": now},
                         "$inc": {"message_count": 1}},
                    )
        except Exception as exc:
            logger.debug(f"MongoDB conversation storage skipped ({exc}). Using local store.")

        return conv

    async def search_semantic_memories(
        self, user_id: str, query: str = "", top_k: int = 5
    ) -> List[SemanticMemory]:
        """Convenience query across semantic memories for a user ranked by composite score."""
        results: List[Tuple[float, SemanticMemory]] = []
        now = _utcnow()
        for sem in self._local_pinecone_semantics.values():
            if sem.user_id != user_id:
                continue
            if query and query.lower() not in sem.fact.lower() and query.lower() not in sem.category.lower():
                pass # Still include if query is broad or let score rank
            score = self.calculate_ranking_score(
                importance=sem.importance_score,
                confidence=sem.confidence,
                access_count=sem.access_count,
                timestamp_dt=sem.updated_at,
            )
            results.append((score, sem))
        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:top_k]]

    async def search_episodic_memories(
        self, user_id: str, query: str = "", top_k: int = 5
    ) -> List[Episode]:
        """Convenience query across episodic memories for a user ranked by composite score."""
        results: List[Tuple[float, Episode]] = []
        for ep in self._local_mongo_episodes.values():
            if ep.user_id != user_id:
                continue
            score = self.calculate_ranking_score(
                importance=ep.importance_score,
                confidence=ep.confidence,
                access_count=ep.access_count,
                timestamp_dt=ep.timestamp,
            )
            results.append((score, ep))
        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:top_k]]

    async def update_memory(self, memory_id: str, memory_type: MemoryType, updates: Dict[str, Any]) -> bool:
        """Updates fields on an existing memory and refreshes updated_at/last_accessed timestamps."""
        now = _utcnow()
        if memory_type == MemoryType.SEMANTIC and memory_id in self._local_pinecone_semantics:
            sem = self._local_pinecone_semantics[memory_id]
            for k, v in updates.items():
                if hasattr(sem, k):
                    setattr(sem, k, v)
            sem.updated_at = now
            sem.last_accessed = now
            sem.access_count += 1
            return True
        elif memory_type == MemoryType.EPISODIC and memory_id in self._local_mongo_episodes:
            ep = self._local_mongo_episodes[memory_id]
            for k, v in updates.items():
                if hasattr(ep, k):
                    setattr(ep, k, v)
            ep.last_accessed = now
            ep.access_count += 1
            return True
        return False

    async def delete_memory(self, memory_id: str, memory_type: MemoryType) -> bool:
        """Deletes a memory by ID across target storage engine."""
        if memory_type == MemoryType.SEMANTIC and memory_id in self._local_pinecone_semantics:
            del self._local_pinecone_semantics[memory_id]
            return True
        elif memory_type == MemoryType.EPISODIC and memory_id in self._local_mongo_episodes:
            del self._local_mongo_episodes[memory_id]
            return True
        return False

    async def resolve_conflict(
        self, user_id: str, new_item: MemoryExtractionItem, existing_semantics: List[SemanticMemory]
    ) -> Optional[SemanticMemory]:
        """
        (`Conflict Resolution Strategy`)
        If user previously stated `preferred_language = Python` and now states `I mostly work with Go`,
        updates existing semantic memory in-place rather than inserting duplicate conflicting records.
        """
        target_category = new_item.key or "preference"
        for sem in existing_semantics:
            # Check if category or keywords collide
            if sem.category == target_category or (
                target_category == "preferred_language" and "prefer" in sem.fact.lower()
            ):
                logger.info(f"Conflict detected for category '{target_category}'. Updating memory [{sem.id}] in-place.")
                sem.fact = new_item.content
                sem.confidence = new_item.confidence
                sem.importance_score = max(sem.importance_score, new_item.importance_score)
                sem.updated_at = _utcnow()
                sem.access_count += 1
                return sem
        return None

    async def merge_duplicate_memories(self, user_id: str, memory_type: MemoryType) -> int:
        """Deduplicates memories sharing identical facts/events for a user."""
        merged_count = 0
        if memory_type == MemoryType.SEMANTIC:
            seen_facts: Dict[str, str] = {}
            to_delete: List[str] = []
            for m_id, sem in list(self._local_pinecone_semantics.items()):
                if sem.user_id != user_id:
                    continue
                norm_fact = sem.fact.lower().strip()
                if norm_fact in seen_facts:
                    to_delete.append(m_id)
                    merged_count += 1
                else:
                    seen_facts[norm_fact] = m_id
            for d_id in to_delete:
                await self.delete_memory(d_id, MemoryType.SEMANTIC)
        return merged_count


# Global singleton instance
memory_manager = MemoryManager()
