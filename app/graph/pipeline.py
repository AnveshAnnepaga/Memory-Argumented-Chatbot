# File: app/graph/pipeline.py
"""
(`Milestone 10 GraphRAG Pipeline Orchestrator`)
Orchestrates the two main data flows of the Knowledge Graph:
1. Graph Building (`PostgreSQL -> Extractor -> Builder -> Neo4j`) with Incremental Graph Sync.
2. Graph Retrieval (`User Question -> Entity Detection -> Neo4j -> Subgraph -> Context Builder -> Graph Context`).
"""
import logging
import re
from typing import Any, Dict, List, Optional

from app.database.neo4j import neo4j_manager
from app.database.postgres import postgres_manager
from app.graph.builder import GraphBuilder, graph_builder
from app.graph.context_builder import GraphContextBuilder, graph_context_builder
from app.graph.extractor import GraphExtractor, graph_extractor
from app.graph.retriever import GraphRetriever, graph_retriever
from app.graph.schemas import GraphContext, NodeType

logger = logging.getLogger("app.graph.pipeline")


class GraphPipeline:
    """
    (`5️⃣ pipeline.py`)
    Orchestrates ingestion synchronization (`sync_from_postgres`) and
    multi-hop graph querying (`query_graph`).
    """
    def __init__(
        self,
        extractor: Optional[GraphExtractor] = None,
        builder: Optional[GraphBuilder] = None,
        retriever: Optional[GraphRetriever] = None,
        context_builder: Optional[GraphContextBuilder] = None
    ):
        self.extractor = extractor or graph_extractor
        self.builder = builder or graph_builder
        self.retriever = retriever or graph_retriever
        self.context_builder = context_builder or graph_context_builder

    async def sync_from_postgres(self, limit: int = 200, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        (`Graph Building & Graph Sync Pipeline`)
        Reads documents stored in PostgreSQL (`documents` or `chunks` table),
        performs incremental version checks, extracts entities and relationships,
        and MERGEs them cleanly into Neo4j.
        """
        logger.info(f"Starting Graph Sync Pipeline from PostgreSQL (limit={limit}, force_rebuild={force_rebuild})...")
        
        if force_rebuild:
            self.builder._document_versions.clear()

        # Try fetching real documents from PostgreSQL
        docs_rows = []
        try:
            if postgres_manager.pool:
                async with postgres_manager.pool.acquire() as conn:
                    # Fetch from documents or chunks
                    rows = await conn.fetch("""
                        SELECT id, title, content, content_hash
                        FROM documents
                        ORDER BY updated_at DESC
                        LIMIT $1
                    """, limit)
                    docs_rows = [dict(r) for r in rows]
        except Exception as exc:
            logger.debug(f"PostgreSQL graph sync query fallback check ({exc}).")

        # If PostgreSQL table is empty or offline during dev/test, fallback to sample technical chunks
        if not docs_rows:
            logger.info("No documents retrieved from PostgreSQL DB connection. Using built-in technical knowledge seed.")
            docs_rows = [
                {
                    "id": "doc-fastapi-deps",
                    "title": "Dependencies - FastAPI",
                    "content": "FastAPI uses Pydantic for request and response data validation. FastAPI depends on Starlette for async web routing and HTTP handling. Uvicorn is an ASGI server that supports FastAPI."
                },
                {
                    "id": "doc-langgraph-flow",
                    "title": "LangGraph Overview",
                    "content": "LangGraph extends LangChain by introducing cyclic stateful agent graphs using StateGraph. LangGraph uses LangChain core components and connects to Groq LLM providers for ultra-fast reasoning."
                },
                {
                    "id": "doc-postgres-mvcc",
                    "title": "PostgreSQL MVCC Architecture",
                    "content": "PostgreSQL implements Multi-Version Concurrency Control (MVCC) to maintain data consistency. PostgreSQL connects to Neo4j using Python drivers for hybrid search architectures."
                }
            ]

        stats = {
            "total_documents_checked": len(docs_rows),
            "created": 0,
            "updated": 0,
            "skipped_unchanged": 0,
            "failed": 0,
            "total_nodes_merged": 0,
            "total_relationships_merged": 0
        }

        for doc in docs_rows:
            doc_id = str(doc.get("id") or "")
            doc_title = str(doc.get("title") or "")
            content = str(doc.get("content") or "")
            if not doc_id or not content:
                continue

            try:
                res = await self.builder.sync_document(
                    doc_id=doc_id,
                    content=content,
                    doc_title=doc_title,
                    extractor=self.extractor
                )
                status = res.get("status", "failed")
                if status in stats:
                    stats[status] += 1
                stats["total_nodes_merged"] += res.get("nodes_merged", 0)
                stats["total_relationships_merged"] += res.get("relationships_merged", 0)
            except Exception as exc:
                logger.error(f"Error syncing document '{doc_id}' to Knowledge Graph: {exc}")
                stats["failed"] += 1

        logger.info(f"Graph Sync Pipeline finished: {stats}")
        return stats

    def _detect_entities_in_question(self, question: str) -> List[str]:
        """Detects candidate entity names mentioned in a user question."""
        detected = []
        q_lower = question.lower()

        # Check against known vocabulary first
        from app.graph.extractor import _KNOWN_ENTITIES
        for key, (norm_name, _) in _KNOWN_ENTITIES.items():
            if re.search(rf"\b{re.escape(key)}\b", q_lower):
                if norm_name not in detected:
                    detected.append(norm_name)

        # Also extract capitalized terms
        words = re.findall(r"\b([A-Z][a-zA-Z0-9_]{2,25})\b", question)
        for w in words:
            if w not in detected and w not in ("What", "How", "Why", "Where", "Which", "Does", "Can", "Is", "Are", "Tell", "Explain"):
                detected.append(w)

        return detected

    async def query_graph(self, question: str, max_depth: int = 2) -> GraphContext:
        """
        (`Graph Retrieval & Context Builder Flow`)
        Takes a user question, detects relevant entities, queries Neo4j for structural
        subgraph paths, and returns a clean GraphContext ready for LangGraph.
        """
        logger.info(f"Executing GraphRAG query for: '{question}'")
        detected_entities = self._detect_entities_in_question(question)

        if not detected_entities:
            return GraphContext(
                entity_name="Unknown",
                node=None,
                relationships=[],
                related_topics=[],
                formatted_context="No specific technical concepts or entities detected in question for GraphRAG traversal.",
                total_tokens=0
            )

        primary_entity = detected_entities[0]

        # If two entities are asked about together (e.g. "How is LangGraph related to LangChain?"), check shortest path
        if len(detected_entities) >= 2:
            src = detected_entities[0]
            tgt = detected_entities[1]
            path_rels = await self.retriever.find_shortest_path(src, tgt, max_depth=max_depth + 1)
            if path_rels:
                center_node = await self.retriever.find_entity(src)
                return self.context_builder.build_graph_context(
                    entity_name=f"{src} <-> {tgt}",
                    node=center_node,
                    relationships=path_rels,
                    max_tokens=1500
                )

        # Standard neighborhood traversal
        center_node, rels, neighbors = await self.retriever.get_neighborhood(
            entity_name=primary_entity,
            max_depth=max_depth
        )

        return self.context_builder.build_graph_context(
            entity_name=primary_entity,
            node=center_node,
            relationships=rels,
            neighbor_nodes=neighbors,
            max_tokens=1500
        )


graph_pipeline = GraphPipeline()
