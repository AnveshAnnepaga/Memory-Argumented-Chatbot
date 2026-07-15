# File: app/repositories/pinecone/vector_repository.py
from typing import Any, Dict, List, Optional
from app.core.exceptions import RepositoryNotFoundException
from app.database.pinecone import pinecone_manager
from app.domain.knowledge import KnowledgeVector
from app.repositories.base import BaseRepository, ISearchRepository, log_and_handle_errors


class VectorRepository(BaseRepository[KnowledgeVector], ISearchRepository[KnowledgeVector]):
    """
    (`7.4 Vector / Knowledge Repository`)
    Low-level interface for managing high-dimensional vector embeddings inside Pinecone indexes.
    Responsibilities: Store embeddings, Search similar vectors, Delete vectors, Update metadata.
    """
    def __init__(self, index_name: Optional[str] = None):
        super().__init__(domain_model_class=KnowledgeVector, repository_name="VectorRepository")
        self.index_name = index_name
        self._memory_vectors: Dict[str, KnowledgeVector] = {}

    def _get_index(self) -> Any:
        return pinecone_manager.get_index(self.index_name)

    @log_and_handle_errors("store_embeddings")
    async def store_embeddings(self, vectors: List[KnowledgeVector], namespace: str = "") -> List[KnowledgeVector]:
        """Bulk store embeddings (`Store embeddings`)."""
        index = self._get_index()
        if index is None:
            for v in vectors:
                v.namespace = namespace
                self._memory_vectors[v.id] = v
            return vectors

        payloads = []
        for v in vectors:
            payloads.append({
                "id": v.id,
                "values": v.values,
                "metadata": v.metadata,
            })
        if payloads:
            index.upsert(vectors=payloads, namespace=namespace)
        return vectors

    @log_and_handle_errors("create")
    async def create(self, entity: KnowledgeVector) -> KnowledgeVector:
        await self.store_embeddings([entity], namespace=entity.namespace or "")
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[KnowledgeVector]:
        index = self._get_index()
        if index is None:
            return self._memory_vectors.get(entity_id)

        response = index.fetch(ids=[entity_id])
        vectors_dict = getattr(response, "vectors", {}) or response.get("vectors", {})
        if entity_id not in vectors_dict:
            return None
        raw = vectors_dict[entity_id]
        return KnowledgeVector(
            id=entity_id,
            values=raw.get("values", []),
            metadata=raw.get("metadata", {}),
        )

    @log_and_handle_errors("search_similar_vectors")
    async def search_similar_vectors(self, query_vector: List[float], top_k: int = 10, filter: Optional[Dict[str, Any]] = None, namespace: str = "") -> List[KnowledgeVector]:
        """Search similar vectors (`Search similar vectors`)."""
        index = self._get_index()
        if index is None:
            items = list(self._memory_vectors.values())
            if namespace:
                items = [i for i in items if i.namespace == namespace]
            # Mock scoring based on order or top_k
            return items[:top_k]

        kwargs: Dict[str, Any] = {"vector": query_vector, "top_k": top_k, "include_metadata": True}
        if filter:
            kwargs["filter"] = filter
        if namespace:
            kwargs["namespace"] = namespace

        response = index.query(**kwargs)
        matches = getattr(response, "matches", []) or response.get("matches", [])
        results = []
        for m in matches:
            results.append(KnowledgeVector(
                id=m["id"],
                values=m.get("values", []),
                score=m.get("score"),
                metadata=m.get("metadata", {}),
                namespace=namespace,
            ))
        return results

    @log_and_handle_errors("search")
    async def search(self, query: Any, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeVector]:
        """Implementation of ISearchRepository.search using vector query."""
        if isinstance(query, list):
            return await self.search_similar_vectors(query, top_k=top_k, filter=filters)
        return []

    @log_and_handle_errors("update_metadata")
    async def update_metadata(self, vector_id: str, metadata: Dict[str, Any], namespace: str = "") -> KnowledgeVector:
        """Update vector metadata (`Update metadata`)."""
        index = self._get_index()
        if index is None:
            existing = self._memory_vectors.get(vector_id)
            if not existing:
                raise RepositoryNotFoundException(f"Vector '{vector_id}' not found.")
            existing.metadata.update(metadata)
            return existing

        index.update(id=vector_id, set_metadata=metadata, namespace=namespace)
        return await self.retrieve(vector_id) or KnowledgeVector(id=vector_id, metadata=metadata)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[KnowledgeVector]:
        if "metadata" in data:
            return await self.update_metadata(entity_id, data["metadata"], namespace=data.get("namespace", ""))
        existing = await self.retrieve(entity_id)
        if not existing:
            raise RepositoryNotFoundException(f"Vector '{entity_id}' not found.")
        return existing

    @log_and_handle_errors("delete_vectors")
    async def delete_vectors(self, vector_ids: List[str], namespace: str = "") -> int:
        """Delete vectors (`Delete vectors`)."""
        index = self._get_index()
        if index is None:
            count = 0
            for vid in vector_ids:
                if self._memory_vectors.pop(vid, None) is not None:
                    count += 1
            return count

        if vector_ids:
            index.delete(ids=vector_ids, namespace=namespace)
        return len(vector_ids)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        return (await self.delete_vectors([entity_id])) > 0

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[KnowledgeVector]:
        return list(self._memory_vectors.values())[skip : skip + limit]

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(self._memory_vectors)
