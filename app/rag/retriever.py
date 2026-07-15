# File: app/rag/retriever.py
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.rag.embedder import embedder
from app.rag.schemas import ChunkSchema, RetrievedChunk
from app.rag.vector_store import vector_store

logger = logging.getLogger("rag.retriever")

try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False

try:
    from sentence_transformers import CrossEncoder
    _CROSS_ENCODER_AVAILABLE = True
except ImportError:
    _CROSS_ENCODER_AVAILABLE = False


class BM25SparseRetriever:
    """
    (`9.4 Sparse BM25 Index`)
    In-memory / indexed sparse BM25 retrieval engine over known document chunks.
    """

    def __init__(self):
        self._chunks: Dict[str, ChunkSchema] = {}
        self._bm25: Optional[Any] = None
        self._tokenized_corpus: List[List[str]] = []
        self._chunk_ids: List[str] = []

    def index_chunks(self, chunks: List[ChunkSchema]) -> int:
        """Indexes or re-indexes a list of ChunkSchema instances into the BM25 Okapi model."""
        if not chunks:
            return 0

        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk

        self._chunk_ids = list(self._chunks.keys())
        self._tokenized_corpus = [
            self._tokenize(self._chunks[cid].text)
            for cid in self._chunk_ids
        ]

        if _BM25_AVAILABLE and self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)
            logger.info(f"BM25 sparse index built across {len(self._chunk_ids)} chunks.")
        else:
            logger.warning("rank_bm25 not available or corpus empty. Sparse search will use exact keyword matching.")

        return len(self._chunk_ids)

    def search(self, query: str, top_k: int = 20) -> List[Tuple[ChunkSchema, float]]:
        """Returns top matching chunks and their raw BM25 relevance scores."""
        if not self._chunk_ids or not query.strip():
            return []

        tokenized_query = self._tokenize(query)

        if self._bm25 and _BM25_AVAILABLE:
            scores = self._bm25.get_scores(tokenized_query)
            query_terms = set(tokenized_query)
            scored_indices = []
            for idx in range(len(scores)):
                cid = self._chunk_ids[idx]
                chunk = self._chunks[cid]
                chunk_terms = set(self._tokenize(chunk.text))
                overlap = len(query_terms.intersection(chunk_terms))
                if scores[idx] > 0:
                    scored_indices.append((idx, float(scores[idx])))
                elif overlap > 0:
                    scored_indices.append((idx, float(overlap)))

            scored_indices.sort(key=lambda x: x[1], reverse=True)

            results: List[Tuple[ChunkSchema, float]] = []
            for idx, score in scored_indices[:top_k]:
                cid = self._chunk_ids[idx]
                results.append((self._chunks[cid], score))
            return results
        else:
            # Fallback simple keyword frequency match if rank_bm25 missing
            results_fb: List[Tuple[ChunkSchema, float]] = []
            query_terms = set(tokenized_query)
            for cid in self._chunk_ids:
                chunk = self._chunks[cid]
                chunk_terms = set(self._tokenize(chunk.text))
                overlap = len(query_terms.intersection(chunk_terms))
                if overlap > 0:
                    results_fb.append((chunk, float(overlap)))
            results_fb.sort(key=lambda x: x[1], reverse=True)
            return results_fb[:top_k]

    def get_chunk(self, chunk_id: str) -> Optional[ChunkSchema]:
        return self._chunks.get(chunk_id)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Simple lowercase alphanumeric tokenization suitable for BM25
        import re
        return re.findall(r"\w+", text.lower())


class CrossEncoderReranker:
    """
    (`9.4 Cross-Encoder Reranker`)
    Evaluates (query, passage) pairs using `BAAI/bge-reranker-large` to compute exact contextual relevance.
    Includes fast local stub/fallback behavior when offline or during unit testing.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-large", use_stub: bool = False):
        self.model_name = model_name
        self.use_stub = use_stub
        self._model: Optional[Any] = None

    def _get_model(self) -> Any:
        if self.use_stub or not _CROSS_ENCODER_AVAILABLE:
            self.use_stub = True
            return None
        if self._model is None:
            try:
                logger.info(f"Loading Cross-Encoder reranker '{self.model_name}'...")
                self._model = CrossEncoder(self.model_name)
                logger.info(f"Cross-Encoder reranker '{self.model_name}' loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load Cross-Encoder '{self.model_name}': {e}. Using local overlap reranking.")
                self.use_stub = True
                self._model = None
        return self._model

    def rerank(self, query: str, candidates: List[RetrievedChunk], top_k: int = 10) -> List[RetrievedChunk]:
        """
        Reranks candidates by exact contextual relevance score (`Candidates -> Top K Reranked`).
        """
        if not candidates:
            return []
        if len(candidates) <= 1:
            return candidates[:top_k]

        # Try high-speed Pinecone Cloud Inference Reranker (bge-reranker-v2-m3)
        try:
            from app.database.pinecone import pinecone_manager
            if pinecone_manager.client is not None and hasattr(pinecone_manager.client, "inference"):
                docs_payload = [
                    {
                        "id": str(getattr(c, "chunk_id", getattr(c, "id", idx))),
                        "text": (c.text if c.text and c.text.strip() else "Empty document content")
                    }
                    for idx, c in enumerate(candidates)
                ]
                res = pinecone_manager.client.inference.rerank(
                    model="bge-reranker-v2-m3",
                    query=query,
                    documents=docs_payload,
                    top_n=min(top_k, len(candidates)),
                    return_documents=False,
                    parameters={"truncate": "END"}
                )
                scored_candidates = []
                for item in getattr(res, "data", []):
                    idx = getattr(item, "index", -1)
                    if 0 <= idx < len(candidates):
                        c = candidates[idx]
                        s = float(getattr(item, "score", 0.0))
                        c.rerank_score = s
                        c.score = s
                        scored_candidates.append(c)
                if scored_candidates:
                    return scored_candidates[:top_k]
        except Exception as exc:
            logger.warning(f"Pinecone Cloud rerank fallback: {exc}")

        model = self._get_model()

        if not self.use_stub and model is not None:
            try:
                pairs = [[query, c.text] for c in candidates]
                raw_scores = model.predict(pairs)
                for c, s in zip(candidates, raw_scores):
                    c.rerank_score = float(s)
                    c.score = float(s)
                candidates.sort(key=lambda x: x.score, reverse=True)
                return candidates[:top_k]
            except Exception as exc:
                logger.warning(f"Cross-Encoder prediction error ({exc}). Using local heuristic reranking.")
                self.use_stub = True

        # Heuristic / stub reranking: combine candidate fused score with exact word/phrase overlap
        q_words = set(BM25SparseRetriever._tokenize(query))
        for c in candidates:
            c_words = set(BM25SparseRetriever._tokenize(c.text))
            overlap_ratio = len(q_words.intersection(c_words)) / max(1, len(q_words))
            # Fused rerank heuristic
            s = c.score * 0.65 + overlap_ratio * 0.35
            c.rerank_score = s
            c.score = s

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]


class RetrievalFusionEngine:
    """
    ⭐ `Retrieval Fusion Engine` (Architectural Improvement)
    Responsible for:
    1. Merging dense (Pinecone) and sparse (BM25) results.
    2. Removing duplicate chunks across retrieval streams.
    3. Normalizing scores (`min-max scaling` & `Reciprocal Rank Fusion RRF`).
    4. Selecting the best candidate pool (`candidate_pool_size`) to pass to the Cross-Encoder Reranker.
    """

    def __init__(self, alpha: float = 0.5, rrf_k: int = 60):
        self.alpha = alpha  # Weight balance between dense (0.5) and sparse (0.5)
        self.rrf_k = rrf_k  # Reciprocal Rank Fusion constant

    def fuse_results(
        self,
        dense_matches: List[Dict[str, Any]],
        sparse_matches: List[Tuple[ChunkSchema, float]],
        candidate_pool_size: int = 30,
    ) -> List[RetrievedChunk]:
        """
        Fuses dense and sparse search outputs into deduplicated, normalized candidates.
        """
        # 1. Normalize Dense Scores (typically cosine [0, 1] or [-1, 1])
        dense_norm = self._min_max_scale_dense([m["score"] for m in dense_matches])
        dense_ranks = {m["id"]: idx + 1 for idx, m in enumerate(dense_matches)}

        # 2. Normalize Sparse Scores (BM25 [0, inf))
        sparse_norm = self._min_max_scale([s for _, s in sparse_matches])
        sparse_ranks = {chunk.chunk_id: idx + 1 for idx, (chunk, _) in enumerate(sparse_matches)}

        # Map to store unique merged candidates by chunk_id
        merged_candidates: Dict[str, RetrievedChunk] = {}

        # Process Dense Matches
        for idx, match in enumerate(dense_matches):
            cid = match["id"]
            meta = match.get("metadata", {})
            text = str(meta.get("text", ""))
            doc_id = str(meta.get("document_id", ""))
            d_score = dense_norm[idx] if idx < len(dense_norm) else 0.0

            if cid not in merged_candidates:
                merged_candidates[cid] = RetrievedChunk(
                    chunk_id=cid,
                    document_id=doc_id,
                    text=text,
                    score=0.0,
                    dense_score=d_score,
                    sparse_score=0.0,
                    metadata=meta,
                )
            else:
                merged_candidates[cid].dense_score = d_score

        # Process Sparse Matches
        for idx, (chunk, raw_s) in enumerate(sparse_matches):
            cid = chunk.chunk_id
            s_score = sparse_norm[idx] if idx < len(sparse_norm) else 0.0

            if cid not in merged_candidates:
                merged_candidates[cid] = RetrievedChunk(
                    chunk_id=cid,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    score=0.0,
                    dense_score=0.0,
                    sparse_score=s_score,
                    metadata=chunk.metadata,
                )
            else:
                merged_candidates[cid].sparse_score = s_score
                # Ensure text and metadata are populated if dense match missed full text
                if not merged_candidates[cid].text:
                    merged_candidates[cid].text = chunk.text
                    merged_candidates[cid].document_id = chunk.document_id
                    merged_candidates[cid].metadata = chunk.metadata

        # 3. Compute final fused score using balanced Linear Combination + Reciprocal Rank Fusion (RRF)
        for cid, candidate in merged_candidates.items():
            d_score = candidate.dense_score or 0.0
            s_score = candidate.sparse_score or 0.0

            # Linear normalized combination
            linear_score = (self.alpha * d_score) + ((1.0 - self.alpha) * s_score)

            # RRF boost
            rank_d = dense_ranks.get(cid, 999)
            rank_s = sparse_ranks.get(cid, 999)
            rrf_score = (1.0 / (self.rrf_k + rank_d)) + (1.0 / (self.rrf_k + rank_s))

            # Combined fused metric
            candidate.score = round(linear_score + (rrf_score * 10.0), 6)

        # 4. Sort and select top candidates for reranking
        fused_list = list(merged_candidates.values())
        fused_list.sort(key=lambda x: x.score, reverse=True)
        return fused_list[:candidate_pool_size]

    @staticmethod
    def _min_max_scale(scores: List[float]) -> List[float]:
        if not scores:
            return []
        min_s = min(scores)
        max_s = max(scores)
        if max_s == min_s:
            return [1.0 if s > 0 else 0.0 for s in scores]
        return [(s - min_s) / (max_s - min_s) for s in scores]

    @staticmethod
    def _min_max_scale_dense(scores: List[float]) -> List[float]:
        if not scores:
            return []
        # For cosine similarity already in around [0, 1] or [-1, 1]
        min_s = min(scores)
        max_s = max(scores)
        if max_s == min_s:
            return [max(0.0, min(1.0, s)) for s in scores]
        return [max(0.0, min(1.0, (s - min_s) / (max_s - min_s))) for s in scores]


class HybridRetriever:
    """
    (`9.4 Hybrid Retriever`)
    Orchestrates the complete Retrieval Pipeline without calling the LLM:
    User Query -> Query Embedding -> Dense + BM25 Search -> Retrieval Fusion Engine -> Cross-Encoder Reranker -> Top K.
    """

    def __init__(
        self,
        sparse_retriever: Optional[BM25SparseRetriever] = None,
        fusion_engine: Optional[RetrievalFusionEngine] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ):
        self.sparse_retriever = sparse_retriever or BM25SparseRetriever()
        self.fusion_engine = fusion_engine or RetrievalFusionEngine()
        self.reranker = reranker or CrossEncoderReranker()

    def index_chunks(self, chunks: List[ChunkSchema]) -> int:
        """Indexes chunks into the sparse BM25 index (dense indexing is handled via vector_store)."""
        return self.sparse_retriever.index_chunks(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_pool_size: int = 25,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        """
        Executes hybrid retrieval and returns the top_k reranked chunks.
        Notice: Does NOT call the LLM!
        """
        if not query.strip():
            return []

        # 1. Query Embedding & Dense Search (Pinecone / Local Vector Store)
        query_vector = embedder.embed_text(query)
        dense_matches = vector_store.similarity_search(
            query_vector=query_vector,
            top_k=candidate_pool_size,
            filter=filter,
            namespace=namespace,
        )

        # 2. Sparse BM25 Search
        sparse_matches = self.sparse_retriever.search(query=query, top_k=candidate_pool_size)

        # 3. Retrieval Fusion Engine (Merge, deduplicate, normalize, RRF)
        fused_candidates = self.fusion_engine.fuse_results(
            dense_matches=dense_matches,
            sparse_matches=sparse_matches,
            candidate_pool_size=candidate_pool_size,
        )

        # 4. Cross-Encoder Reranking
        reranked_top_k = self.reranker.rerank(
            query=query,
            candidates=fused_candidates,
            top_k=top_k,
        )

        logger.info(
            f"Hybrid retrieval completed for query '{query[:30]}...'. "
            f"[Dense: {len(dense_matches)} | Sparse: {len(sparse_matches)} | Fused: {len(fused_candidates)} -> Top K: {len(reranked_top_k)}]"
        )
        return reranked_top_k


# Global singleton instances
sparse_retriever = BM25SparseRetriever()
fusion_engine = RetrievalFusionEngine()
reranker = CrossEncoderReranker()
hybrid_retriever = HybridRetriever(sparse_retriever=sparse_retriever, fusion_engine=fusion_engine, reranker=reranker)
