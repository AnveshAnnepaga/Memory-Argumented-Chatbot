# File: app/repositories/pinecone/semantic_memory_repository.py
from typing import Any, Dict, List, Optional
from app.domain.knowledge import SemanticMemoryVector
from app.repositories.base import BaseRepository, ISearchRepository, log_and_handle_errors
from app.repositories.pinecone.vector_repository import VectorRepository


class SemanticMemoryRepository(BaseRepository[SemanticMemoryVector], ISearchRepository[SemanticMemoryVector]):
    """
    (`7.4 Semantic Memory Repository`)
    Manages long-term semantic user memory embeddings in Pinecone (`semantic_memory` namespace).
    Responsibilities: Store semantic memory, Search memory, Delete memory.
    """
    def __init__(self, vector_repo: Optional[VectorRepository] = None, namespace: str = "semantic_memory"):
        super().__init__(domain_model_class=SemanticMemoryVector, repository_name="SemanticMemoryRepository")
        self.vector_repo = vector_repo or VectorRepository()
        self.namespace = namespace
        self._memory_store: Dict[str, SemanticMemoryVector] = {}

    @log_and_handle_errors("store_semantic_memory")
    async def store_semantic_memory(self, memory: SemanticMemoryVector) -> SemanticMemoryVector:
        """Store long-term semantic memory (`Store semantic memory`)."""
        return await self.create(memory)

    @log_and_handle_errors("create")
    async def create(self, entity: SemanticMemoryVector) -> SemanticMemoryVector:
        self._memory_store[entity.id] = entity
        from app.domain.knowledge import KnowledgeVector
        kv = KnowledgeVector(
            id=entity.id,
            values=entity.values,
            metadata={
                "user_id": entity.user_id,
                "memory_text": entity.memory_text,
                **entity.metadata,
            },
            namespace=self.namespace,
        )
        await self.vector_repo.store_embeddings([kv], namespace=self.namespace)
        return entity

    @log_and_handle_errors("search_memory")
    async def search_memory(self, user_id: str, query_embedding: List[float], top_k: int = 5) -> List[SemanticMemoryVector]:
        """Search relevant semantic memories for a user (`Search memory`)."""
        matched_vectors = await self.vector_repo.search_similar_vectors(
            query_vector=query_embedding,
            top_k=top_k,
            filter={"user_id": user_id},
            namespace=self.namespace,
        )
        results = []
        for mv in matched_vectors:
            if mv.id in self._memory_store:
                results.append(self._memory_store[mv.id])
            elif "memory_text" in mv.metadata:
                results.append(SemanticMemoryVector(
                    id=mv.id,
                    user_id=str(mv.metadata.get("user_id", user_id)),
                    memory_text=str(mv.metadata.get("memory_text", "")),
                    values=mv.values,
                    score=mv.score,
                    metadata=mv.metadata,
                ))
        return results

    @log_and_handle_errors("search")
    async def search(self, query: Any, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SemanticMemoryVector]:
        if isinstance(query, list) and filters and "user_id" in filters:
            return await self.search_memory(user_id=filters["user_id"], query_embedding=query, top_k=top_k)
        return []

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[SemanticMemoryVector]:
        return self._memory_store.get(entity_id)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[SemanticMemoryVector]:
        existing = self._memory_store.get(entity_id)
        if not existing:
            return None
        dump = existing.model_dump()
        dump.update(data)
        updated = SemanticMemoryVector.model_validate(dump)
        self._memory_store[entity_id] = updated
        return updated

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        """Delete semantic memory (`Delete memory`)."""
        await self.vector_repo.delete_vectors([entity_id], namespace=self.namespace)
        return self._memory_store.pop(entity_id, None) is not None

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return entity_id in self._memory_store

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[SemanticMemoryVector]:
        items = list(self._memory_store.values())
        if filters and "user_id" in filters:
            items = [i for i in items if i.user_id == filters["user_id"]]
        return items[skip : skip + limit]

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        items = list(self._memory_store.values())
        if filters and "user_id" in filters:
            items = [i for i in items if i.user_id == filters["user_id"]]
        return len(items)
