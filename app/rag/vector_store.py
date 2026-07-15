# File: app/rag/vector_store.py
import logging
from typing import Any, Dict, List, Optional
from app.database.pinecone import pinecone_manager
from app.rag.schemas import EmbeddingVector

logger = logging.getLogger("rag.vector_store")


class PineconeVectorStore:
    """
    (`9.3 Vector Store`)
    Dedicated wrapper around Pinecone for dense vector operations:
    - Upsert
    - Delete
    - Namespace Management
    - Similarity Search
    
    Nothing else (no chunking, no embedding, no LLM calls).
    Includes full in-memory stub fallback when Pinecone API key/index is stubbed or offline.
    """

    def __init__(self):
        self._stub_store: Dict[str, Dict[str, EmbeddingVector]] = {}

    def get_namespace(self, custom_namespace: Optional[str] = None) -> str:
        """Returns target namespace or falls back to configured default."""
        return pinecone_manager.get_namespace(custom_namespace)

    def _sanitize_metadata(self, meta: dict) -> dict:
        """Sanitizes metadata dictionary to satisfy Pinecone constraints (str, int, float, bool, or list of str)."""
        clean = {}
        for k, v in meta.items():
            if v is None:
                continue
            elif isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, list):
                clean[k] = [str(item) for item in v if item is not None]
            elif isinstance(v, dict):
                if v:
                    import json
                    clean[k] = json.dumps(v)
            else:
                clean[k] = str(v)
        return clean

    def upsert(self, vectors: List[EmbeddingVector], namespace: Optional[str] = None) -> int:
        """
        Upserts vector embeddings into the vector store (`Vectors -> Pinecone`).
        Returns number of vectors upserted.
        """
        if not vectors:
            return 0

        target_ns = self.get_namespace(namespace)

        if pinecone_manager.stub_mode or not pinecone_manager.get_index():
            if target_ns not in self._stub_store:
                self._stub_store[target_ns] = {}
            for v in vectors:
                self._stub_store[target_ns][v.chunk_id] = v
            logger.info(f"[Stub] Upserted {len(vectors)} vectors into namespace '{target_ns}'.")
            return len(vectors)

        try:
            index = pinecone_manager.get_index()
            # Prepare format for Pinecone: list of (id, values, metadata) tuples or dicts
            batch_data = [
                (v.chunk_id, v.values, self._sanitize_metadata(v.metadata))
                for v in vectors
            ]
            # Upsert in batches of 100
            total_upserted = 0
            for i in range(0, len(batch_data), 100):
                chunk_batch = batch_data[i : i + 100]
                index.upsert(vectors=chunk_batch, namespace=target_ns)
                total_upserted += len(chunk_batch)

            logger.info(f"Upserted {total_upserted} vectors into Pinecone namespace '{target_ns}'.")
            return total_upserted
        except Exception as exc:
            logger.warning(f"Pinecone upsert error ({exc}). Saving vectors to local stub store.")
            if target_ns not in self._stub_store:
                self._stub_store[target_ns] = {}
            for v in vectors:
                self._stub_store[target_ns][v.chunk_id] = v
            return len(vectors)

    def delete(
        self,
        ids: Optional[List[str]] = None,
        delete_all: bool = False,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Deletes vector IDs or clears namespace from Pinecone.
        """
        target_ns = self.get_namespace(namespace)

        if pinecone_manager.stub_mode or not pinecone_manager.get_index():
            if target_ns in self._stub_store:
                if delete_all:
                    self._stub_store[target_ns].clear()
                elif ids:
                    for v_id in ids:
                        self._stub_store[target_ns].pop(v_id, None)
            logger.info(f"[Stub] Deleted vectors from namespace '{target_ns}' (delete_all={delete_all}).")
            return True

        try:
            index = pinecone_manager.get_index()
            if delete_all:
                index.delete(delete_all=True, namespace=target_ns)
            elif ids:
                index.delete(ids=ids, namespace=target_ns)
            elif filter:
                index.delete(filter=filter, namespace=target_ns)
            logger.info(f"Deleted vectors from Pinecone namespace '{target_ns}'.")
            return True
        except Exception as exc:
            logger.warning(f"Pinecone delete error ({exc}). Executing on stub store.")
            if target_ns in self._stub_store:
                if delete_all:
                    self._stub_store[target_ns].clear()
                elif ids:
                    for v_id in ids:
                        self._stub_store[target_ns].pop(v_id, None)
            return True

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes dense vector similarity search against Pinecone or local stub store (`Vector -> Top K Matches`).
        Returns list of dicts with `id`, `score`, and `metadata`.
        """
        target_ns = self.get_namespace(namespace)

        if pinecone_manager.stub_mode or not pinecone_manager.get_index():
            return self._stub_similarity_search(query_vector, top_k, target_ns, filter)

        try:
            index = pinecone_manager.get_index()
            response = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                namespace=target_ns,
                filter=filter,
            )
            matches: List[Dict[str, Any]] = []
            for match in getattr(response, "matches", []):
                matches.append({
                    "id": getattr(match, "id", str(match.get("id", ""))),
                    "score": float(getattr(match, "score", match.get("score", 0.0))),
                    "metadata": dict(getattr(match, "metadata", match.get("metadata", {}))),
                })
            if not matches and namespace is None:
                # If default namespace returned 0 matches, check other active namespaces in Pinecone index
                try:
                    stats = index.describe_index_stats()
                    for ns in getattr(stats, "namespaces", {}).keys():
                        if ns and ns != target_ns:
                            resp_ns = index.query(
                                vector=query_vector,
                                top_k=top_k,
                                include_metadata=True,
                                namespace=ns,
                                filter=filter,
                            )
                            for match in getattr(resp_ns, "matches", []):
                                matches.append({
                                    "id": getattr(match, "id", str(match.get("id", ""))),
                                    "score": float(getattr(match, "score", match.get("score", 0.0))),
                                    "metadata": dict(getattr(match, "metadata", match.get("metadata", {}))),
                                })
                            if matches:
                                break
                except Exception as ns_exc:
                    logger.debug(f"Fallback namespace search error: {ns_exc}")
            return matches
        except Exception as exc:
            logger.warning(f"Pinecone query error ({exc}). Falling back to local stub search.")
            return self._stub_similarity_search(query_vector, top_k, target_ns, filter, check_all=(namespace is None))

    def _stub_similarity_search(
        self,
        query_vector: List[float],
        top_k: int,
        namespace: str,
        filter: Optional[Dict[str, Any]],
        check_all: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Performs exact cosine similarity across local stub vectors.
        """
        ns_store = self._stub_store.get(namespace, {})
        if not ns_store and check_all:
            for other_ns, store in self._stub_store.items():
                if store:
                    ns_store = store
                    break
        if not ns_store:
            return []

        scored_items: List[Dict[str, Any]] = []
        for v_id, vec_obj in ns_store.items():
            # Apply metadata filter if specified
            if filter:
                match = True
                for k, v in filter.items():
                    if vec_obj.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            score = self._cosine_similarity(query_vector, vec_obj.values)
            scored_items.append({
                "id": v_id,
                "score": score,
                "metadata": vec_obj.metadata,
            })

        # Sort descending by score
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        return scored_items[:top_k]

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


# Global singleton instance
vector_store = PineconeVectorStore()
