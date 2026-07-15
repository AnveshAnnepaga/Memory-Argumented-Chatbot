# File: app/graph/builder.py
"""
(`Milestone 10 Graph Builder & Graph Sync Pipeline with ⭐ Improvements 1, 2, 3, 6`)
Responsible for persisting extracted entities and relationships into Neo4j using MERGE
to guarantee zero duplicate nodes while accumulating weighted edge frequencies,
preserving provenance evidence, tracking confidence, and bumping graph semantic versions.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from app.database.neo4j import neo4j_manager
from app.graph.extractor import GraphExtractor, graph_extractor
from app.graph.schemas import Entity, ExtractionResult, Relationship, RelationshipType

logger = logging.getLogger("app.graph.builder")


class GraphBuilder:
    """
    (`2️⃣ builder.py`)
    Responsibilities:
    - MERGE nodes (`Never create duplicate nodes. Always use MERGE instead of CREATE`)
    - MERGE relationships with weighted frequencies and max confidence (`⭐ Improvement 1 & 3`)
    - Attach exact document/chunk/url provenance (`⭐ Improvement 2`)
    - Incremental Graph Sync Pipeline (`Document Version Check`)
    - Maintain and increment Graph Semantic Version (`⭐ Improvement 6: Graph Version`)
    """
    def __init__(self):
        self._document_versions: Dict[str, str] = {}
        self._stub_nodes: Dict[str, Entity] = {}
        # Stores (src, tgt, rel_type) -> Relationship object with accumulated frequency/confidence
        self._stub_rels: Dict[Tuple[str, str, str], Relationship] = {}
        # ⭐ Improvement 6: Graph Version
        self.graph_version: str = "1.0.0"

    def _is_stub(self) -> bool:
        """Checks if Neo4j is offline or in local stub mode."""
        return neo4j_manager.stub_mode or neo4j_manager.get_driver() is None

    def _bump_version(self) -> None:
        """Increments the minor/patch version of the Knowledge Graph when updates occur."""
        parts = [int(p) for p in self.graph_version.split(".") if p.isdigit()]
        if len(parts) == 3:
            parts[2] += 1
            if parts[2] >= 10:
                parts[2] = 0
                parts[1] += 1
            self.graph_version = f"{parts[0]}.{parts[1]}.{parts[2]}"

    async def merge_entity(self, entity: Entity, doc_id: str = "") -> Entity:
        """
        MERGEs a single node into Neo4j using its normalized name and label.
        """
        if self._is_stub():
            norm_key = entity.name.lower()
            props = {**entity.properties}
            if doc_id:
                props["last_doc_id"] = doc_id
            self._stub_nodes[norm_key] = Entity(
                name=entity.name,
                node_type=entity.node_type,
                properties=props
            )
            return self._stub_nodes[norm_key]

        label = entity.node_type.value
        query = f"""
        MERGE (n:{label} {{name: $name}})
        ON CREATE SET n.created_at = timestamp(), n.node_type = $node_type, n.last_doc_id = $doc_id
        ON MATCH SET n.updated_at = timestamp(), n.last_doc_id = $doc_id
        SET n += $properties
        RETURN n
        """
        try:
            await neo4j_manager.execute_query(query, {
                "name": entity.name,
                "node_type": entity.node_type.value,
                "doc_id": doc_id,
                "properties": entity.properties or {}
            })
        except Exception as exc:
            logger.debug(f"Neo4j MERGE node failed ({exc}). Updating local stub cache.")
            self._stub_nodes[entity.name.lower()] = entity

        return entity

    async def merge_relationship(self, rel: Relationship) -> Relationship:
        """
        MERGEs a directed relationship between two entities in Neo4j with frequency weighting and confidence.
        """
        key = (rel.source.lower(), rel.target.lower(), rel.rel_type.value)
        if self._is_stub():
            if key in self._stub_rels:
                existing = self._stub_rels[key]
                existing.frequency += rel.frequency
                existing.confidence = max(existing.confidence, rel.confidence)
                if rel.document_id and not existing.document_id:
                    existing.document_id = rel.document_id
                    existing.source_url = rel.source_url
            else:
                self._stub_rels[key] = rel
            return self._stub_rels[key]

        rel_type = rel.rel_type.value
        query = f"""
        MATCH (a WHERE a.name =~ (?i)$source_name), (b WHERE b.name =~ (?i)$target_name)
        MERGE (a)-[r:{rel_type}]->(b)
        ON CREATE SET 
            r.created_at = timestamp(),
            r.frequency = $frequency,
            r.confidence = $confidence,
            r.document_id = $doc_id,
            r.chunk_id = $chunk_id,
            r.source_url = $source_url
        ON MATCH SET 
            r.updated_at = timestamp(),
            r.frequency = coalesce(r.frequency, 0) + $frequency,
            r.confidence = case when $confidence > coalesce(r.confidence, 0.0) then $confidence else r.confidence end,
            r.document_id = case when r.document_id is null or r.document_id = '' then $doc_id else r.document_id end,
            r.source_url = case when r.source_url is null or r.source_url = '' then $source_url else r.source_url end
        SET r += $properties
        RETURN r
        """
        try:
            await neo4j_manager.execute_query(query, {
                "source_name": f"^{rel.source}$",
                "target_name": f"^{rel.target}$",
                "frequency": rel.frequency,
                "confidence": rel.confidence,
                "doc_id": rel.document_id,
                "chunk_id": rel.chunk_id,
                "source_url": rel.source_url,
                "properties": rel.properties or {}
            })
        except Exception as exc:
            logger.debug(f"Neo4j MERGE relationship failed ({exc}). Updating local stub cache.")
            if key in self._stub_rels:
                self._stub_rels[key].frequency += rel.frequency
                self._stub_rels[key].confidence = max(self._stub_rels[key].confidence, rel.confidence)
            else:
                self._stub_rels[key] = rel

        return rel

    async def merge_extraction_result(self, result: ExtractionResult) -> Dict[str, Any]:
        """
        MERGEs all entities and relationships from an ExtractionResult into Neo4j and increments version if modified.
        """
        nodes_created = 0
        rels_created = 0

        # MERGE all nodes first so relationship endpoints exist
        for entity in result.entities:
            await self.merge_entity(entity, doc_id=result.document_id)
            nodes_created += 1

        # MERGE all directed relationships
        for rel in result.relationships:
            await self.merge_relationship(rel)
            rels_created += 1

        # Update version trackers
        if result.document_id and result.document_hash:
            self._document_versions[result.document_id] = result.document_hash

        if nodes_created > 0 or rels_created > 0:
            self._bump_version()

        return {
            "status": "success",
            "document_id": result.document_id,
            "nodes_merged": nodes_created,
            "relationships_merged": rels_created,
            "graph_version": self.graph_version
        }

    async def sync_document(
        self,
        doc_id: str,
        content: str,
        doc_title: str = "",
        source_url: str = "",
        extractor: Optional[GraphExtractor] = None
    ) -> Dict[str, Any]:
        """
        (`⭐ One Important Improvement: Graph Sync Pipeline`)
        Incremental graph building directly from PostgreSQL document checks.
        If the document version (hash) matches what is already in our graph sync cache,
        the extraction is completely skipped to save time and compute.
        """
        import hashlib
        doc_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Check incremental check
        if doc_id in self._document_versions and self._document_versions[doc_id] == doc_hash:
            logger.info(f"Graph Sync: Document '{doc_id}' unchanged. Skipping extraction.")
            return {
                "status": "skipped_unchanged",
                "document_id": doc_id,
                "graph_version": self.graph_version,
                "message": "Document hash matches current version in Knowledge Graph."
            }

        logger.info(f"Graph Sync: Document '{doc_id}' updated or new. Re-extracting entities...")
        active_extractor = extractor or graph_extractor
        extraction_result = await active_extractor.extract_from_document(
            doc_input=content,
            document_id=doc_id,
            document_title=doc_title,
            source_url=source_url
        )

        build_result = await self.merge_extraction_result(extraction_result)
        build_result["status"] = "updated" if doc_id in self._document_versions else "created"
        return build_result

    def get_stub_graph_summary(self) -> Dict[str, Any]:
        """Returns statistics on in-memory nodes/rels for diagnostics/offline mode."""
        return {
            "graph_version": self.graph_version,
            "total_nodes": len(self._stub_nodes),
            "total_relationships": len(self._stub_rels),
            "nodes": [n.model_dump() for n in self._stub_nodes.values()],
            "relationships": [
                {
                    "source": r.source,
                    "target": r.target,
                    "rel_type": r.rel_type.value,
                    "confidence": r.confidence,
                    "frequency": r.frequency,
                    "document_id": r.document_id
                }
                for r in self._stub_rels.values()
            ]
        }


graph_builder = GraphBuilder()
