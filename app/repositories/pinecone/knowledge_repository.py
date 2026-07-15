# File: app/repositories/pinecone/knowledge_repository.py
from typing import Any, Dict, List, Optional
from app.domain.knowledge import Chunk, KnowledgeVector
from app.repositories.base import BaseRepository, ISearchRepository, log_and_handle_errors
from app.repositories.pinecone.vector_repository import VectorRepository


class KnowledgeRepository(BaseRepository[Chunk], ISearchRepository[Chunk]):
    """
    (`7.4 Vector / Knowledge Repository`)
    High-level domain wrapper mapping text Chunks to Pinecone KnowledgeVectors.
    Responsibilities: Store chunks, Retrieve context, Filter chunks by source.
    """
    def __init__(self, vector_repo: Optional[VectorRepository] = None, namespace: str = "knowledge"):
        super().__init__(domain_model_class=Chunk, repository_name="KnowledgeRepository")
        self.vector_repo = vector_repo or VectorRepository()
        self.namespace = namespace
        self._chunk_store: Dict[str, Chunk] = {}

    @log_and_handle_errors("store_chunks")
    async def store_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> List[Chunk]:
        """Store chunks and their vector embeddings (`Store chunks`)."""
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            self._chunk_store[chunk.id] = chunk
            vectors.append(KnowledgeVector(
                id=chunk.id,
                chunk_id=chunk.id,
                values=embedding,
                metadata={
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "text_content": chunk.text_content,
                    **chunk.metadata,
                },
                namespace=self.namespace,
            ))
        await self.vector_repo.store_embeddings(vectors, namespace=self.namespace)
        return chunks

    @log_and_handle_errors("retrieve_context")
    async def retrieve_context(self, query_embedding: List[float], top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Retrieve relevant context chunks via vector search (`Retrieve context`)."""
        matched_vectors = await self.vector_repo.search_similar_vectors(
            query_vector=query_embedding,
            top_k=top_k,
            filter=filter_metadata,
            namespace=self.namespace,
        )
        chunks = []
        for mv in matched_vectors:
            if mv.id in self._chunk_store:
                chunks.append(self._chunk_store[mv.id])
            elif "text_content" in mv.metadata:
                chunks.append(Chunk(
                    id=mv.id,
                    document_id=str(mv.metadata.get("document_id", "")),
                    chunk_index=int(mv.metadata.get("chunk_index", 0)),
                    text_content=str(mv.metadata.get("text_content", "")),
                    metadata=mv.metadata,
                ))
        return chunks

    @log_and_handle_errors("filter_chunks_by_source")
    async def filter_chunks_by_source(self, document_id: str, skip: int = 0, limit: int = 50) -> List[Chunk]:
        """Filter chunks belonging to a specific document ID (`Filter chunks by source`)."""
        items = [c for c in self._chunk_store.values() if c.document_id == document_id]
        return items[skip : skip + limit]

    @log_and_handle_errors("search")
    async def search(self, query: Any, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        if isinstance(query, list):
            return await self.retrieve_context(query_embedding=query, top_k=top_k, filter_metadata=filters)
        return []

    @log_and_handle_errors("create")
    async def create(self, entity: Chunk) -> Chunk:
        self._chunk_store[entity.id] = entity
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[Chunk]:
        return self._chunk_store.get(entity_id)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Chunk]:
        existing = self._chunk_store.get(entity_id)
        if not existing:
            return None
        dump = existing.model_dump()
        dump.update(data)
        updated = Chunk.model_validate(dump)
        self._chunk_store[entity_id] = updated
        return updated

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        await self.vector_repo.delete_vectors([entity_id], namespace=self.namespace)
        return self._chunk_store.pop(entity_id, None) is not None

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return entity_id in self._chunk_store

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        return list(self._chunk_store.values())[skip : skip + limit]

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(self._chunk_store)
