# File: app/rag/embedder.py
import hashlib
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional
from app.rag.schemas import ChunkSchema, EmbeddingVector
from app.core.config import settings

logger = logging.getLogger("rag.embedder")

# Avoid importing TensorFlow via transformers during test collection.
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except Exception as exc:
    logger.warning(f"sentence_transformers unavailable; using stub embeddings instead ({exc}).")
    _ST_AVAILABLE = False


class BGEEmbedder:
    """
    (`9.2 Embedder`)
    Responsible for generating high-quality dense vector embeddings from chunks.
    Model: `BAAI/bge-large-en-v1.5` (1024 dimensions).
    
    Features:
    - Lazy loading of Hugging Face `SentenceTransformer` model (`BAAI/bge-large-en-v1.5`).
    - Batch embedding generation for high throughput.
    - Automatic caching of computed embeddings (`text_hash -> vector`) to prevent redundant computation.
    - Offline/stub fallback mode (`1024-dim` deterministic pseudo-vectors) for fast CI/local testing.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-large-en-v1.5",
        dimension: int = 1024,
        use_stub: bool = False,
    ):
        self.model_name = model_name
        self.dimension = dimension
        
        # Override use_stub if explicitly disabled via settings
        if settings.ai and settings.ai.embeddings.disable_local:
            logger.info("Local embeddings explicitly disabled via settings. Using stub/cloud only.")
            self.use_stub = True
        else:
            self.use_stub = use_stub
            
        self._model: Optional[Any] = None
        self._cache: Dict[str, List[float]] = {}

    def _get_model(self) -> Any:
        """Lazy loads SentenceTransformer model when first needed unless stub mode is active."""
        if self.use_stub or not _ST_AVAILABLE:
            if not self.use_stub:
                logger.warning("sentence_transformers not available or offline. Using deterministic 1024-dim stub embeddings.")
                self.use_stub = True
            return None

        if self._model is None:
            try:
                logger.info(f"Loading embedding model '{self.model_name}'...")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Embedding model '{self.model_name}' loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load Hugging Face model '{self.model_name}': {e}. Falling back to stub embedding mode.")
                self.use_stub = True
                self._model = None
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """
        Generates a 1024-dimensional vector for a single text string, checking the cache first.
        """
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in self._cache:
            return self._cache[text_hash]

        if not self.use_stub:
            try:
                from app.database.pinecone import pinecone_manager
                if pinecone_manager.client is not None:
                    res = pinecone_manager.client.inference.embed(
                        model="multilingual-e5-large",
                        inputs=[text],
                        parameters={"input_type": "query", "truncate": "END"}
                    )
                    vals = getattr(res[0], "values", res[0]["values"] if hasattr(res[0], "__getitem__") else [])
                    vector = [float(v) for v in vals]
                    self._cache[text_hash] = vector
                    return vector
            except Exception as e:
                logger.debug(f"Pinecone cloud single embed check failed ({e}), falling back to local/stub.")

        model = self._get_model()
        if self.use_stub or model is None:
            vector = self._generate_stub_vector(text)
        else:
            vector_np = model.encode(text, normalize_embeddings=True)
            vector = [float(v) for v in vector_np]

        self._cache[text_hash] = vector
        return vector

    def embed_chunk(self, chunk: ChunkSchema) -> EmbeddingVector:
        """
        Converts a ChunkSchema into an EmbeddingVector with all metadata preserved.
        """
        vector = self.embed_text(chunk.text)
        metadata = {
            **chunk.metadata,
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
        }
        return EmbeddingVector(
            chunk_id=chunk.chunk_id,
            values=vector,
            metadata=metadata,
        )

    def embed_chunks(self, chunks: List[ChunkSchema], batch_size: int = 32) -> List[EmbeddingVector]:
        """
        Batch embeds multiple chunks efficiently (`Chunks -> Vectors`).
        """
        if not chunks:
            return []

        results: List[EmbeddingVector] = []

        # Check which chunks need computation versus what is cached
        uncached_texts: List[str] = []
        uncached_indices: List[int] = []

        for idx, chunk in enumerate(chunks):
            t_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
            if t_hash not in self._cache:
                uncached_texts.append(chunk.text)
                uncached_indices.append(idx)

        # First prioritize Pinecone Cloud Inference API (ultra-fast 1024-dim cloud embedding)
        if uncached_texts and not self.use_stub:
            try:
                from app.database.pinecone import pinecone_manager
                if pinecone_manager.client is not None:
                    logger.info(f"Using high-speed Pinecone Cloud Inference (multilingual-e5-large) for {len(uncached_texts)} chunks...")
                    for i in range(0, len(uncached_texts), 64):
                        batch_texts = uncached_texts[i : i + 64]
                        res = pinecone_manager.client.inference.embed(
                            model="multilingual-e5-large",
                            inputs=batch_texts,
                            parameters={"input_type": "passage", "truncate": "END"}
                        )
                        for item_idx, item in enumerate(res):
                            text = batch_texts[item_idx]
                            t_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                            vals = getattr(item, "values", item["values"] if hasattr(item, "__getitem__") else [])
                            self._cache[t_hash] = [float(v) for v in vals]
                    uncached_texts = [t for t in uncached_texts if hashlib.sha256(t.encode("utf-8")).hexdigest() not in self._cache]
            except Exception as e:
                logger.warning(f"Pinecone Cloud Inference batch embedding failed: {e}. Falling back to local/stub embedding.")

        # Batch compute any remaining uncached texts via local model if active
        if uncached_texts and not self.use_stub:
            model = self._get_model()
            if model is not None:
                try:
                    for i in range(0, len(uncached_texts), batch_size):
                        batch_texts = uncached_texts[i : i + batch_size]
                        batch_vectors = model.encode(batch_texts, normalize_embeddings=True)
                        for text, vec_np in zip(batch_texts, batch_vectors):
                            t_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                            self._cache[t_hash] = [float(v) for v in vec_np]
                except Exception as e:
                    logger.warning(f"Batch embedding failed: {e}. Using stub generator for remaining items.")
                    self.use_stub = True

        # Build final EmbeddingVector list
        for chunk in chunks:
            results.append(self.embed_chunk(chunk))

        logger.info(f"Generated {len(results)} embedding vectors (dim={self.dimension}).")
        return results

    def _generate_stub_vector(self, text: str) -> List[float]:
        """
        Generates deterministic, unit-normalized 1024-dim mock vector derived from text SHA-256 seed.
        Ensures identical text always yields identical vectors and similar texts can be searched locally.
        """
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
        import math
        vector: List[float] = []
        # Generate pseudo-random deterministic numbers
        val = seed
        for i in range(self.dimension):
            val = (val * 1103515245 + 12345) & 0x7FFFFFFF
            # Map to [-1, 1]
            float_val = (val / 0x7FFFFFFF) * 2.0 - 1.0
            vector.append(float_val)

        # Unit sphere normalization (L2 norm = 1.0)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


# Global singleton instance
embedder = BGEEmbedder()
