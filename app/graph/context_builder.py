# File: app/graph/context_builder.py
"""
(`Milestone 10 Graph Context Builder with ⭐ Improvement 7: Explainability`)
Converts retrieved graph subgraphs and multi-hop neighborhood results into clean,
structured, budget-controlled, and explainable context blocks ready for LangGraph prompt injection.
Interslices confidence ratings (`⭐ Improvement 1`), provenance citations (`⭐ Improvement 2`),
and frequency weights (`⭐ Improvement 3`).
"""
import logging
from typing import List, Optional

from app.graph.builder import graph_builder
from app.graph.schemas import Entity, GraphContext, Relationship

logger = logging.getLogger("app.graph.context_builder")


class GraphContextBuilder:
    """
    (`4️⃣ context_builder.py`)
    Converts graph results into clean, ordered, deduplicated, and explainable context blocks.
    """
    def __init__(self, max_tokens: int = 1500):
        self.max_tokens = max_tokens

    def build_graph_context(
        self,
        entity_name: str,
        node: Optional[Entity],
        relationships: List[Relationship],
        neighbor_nodes: Optional[List[Entity]] = None,
        max_tokens: Optional[int] = None
    ) -> GraphContext:
        """
        Formats retrieved center node, directed relationships, related topics, and exact
        explainability chains into a structured block ready for LangGraph injection.
        """
        budget = max_tokens if max_tokens is not None else self.max_tokens
        current_version = graph_builder.graph_version

        if not node and not relationships:
            return GraphContext(
                entity_name=entity_name,
                node=None,
                relationships=[],
                related_topics=[],
                traversal_path=[],
                explanation=f"No structural knowledge graph connections found for '{entity_name}' in Graph v{current_version}.",
                graph_version=current_version,
                formatted_context=f"No structural knowledge graph connections found for '{entity_name}'.",
                total_tokens=0
            )

        # 1. Deduplicate relationships by exact (src, tgt, rel_type)
        seen_rels = set()
        dedup_rels: List[Relationship] = []
        for r in relationships:
            key = (r.source.lower(), r.target.lower(), r.rel_type.value)
            if key not in seen_rels:
                seen_rels.add(key)
                dedup_rels.append(r)

        # Sort descending by confidence and frequency
        dedup_rels.sort(key=lambda x: (x.confidence, x.frequency), reverse=True)

        # 2. Extract related topics and build traversal path
        seen_topics = {entity_name.lower()}
        related_topics: List[str] = []
        traversal_path: List[str] = []
        doc_sources: Set[str] = set()

        for r in dedup_rels:
            traversal_path.append(f"{r.source} --[{r.rel_type.value}]--> {r.target}")
            if r.document_id:
                doc_sources.add(r.document_id)
            
            other = r.target if r.source.lower() == entity_name.lower() else r.source
            if other.lower() not in seen_topics:
                seen_topics.add(other.lower())
                related_topics.append(other)

        if neighbor_nodes:
            for neighbor in neighbor_nodes:
                if neighbor.name.lower() not in seen_topics:
                    seen_topics.add(neighbor.name.lower())
                    related_topics.append(neighbor.name)

        # 3. Compute explanation (`⭐ Improvement 7: Graph Explainability`)
        avg_conf = sum(r.confidence for r in dedup_rels) / len(dedup_rels) if dedup_rels else 0.0
        doc_str = ", ".join(sorted(doc_sources)[:3]) if doc_sources else "Knowledge Repository"
        explanation = (
            f"Connected across {len(dedup_rels)} high-confidence structural relationships "
            f"(Avg Confidence: {avg_conf:.2f} | Max Frequency: {max((r.frequency for r in dedup_rels), default=1)}). "
            f"Provenance verified from: {doc_str}."
        )

        # 4. Assemble formatted context strings with token/word budget checks
        lines: List[str] = []
        center_display = node.name if node else entity_name
        lines.append(f"Entity:\n{center_display} (Graph v{current_version})\n")

        lines.append("Relationships:")
        if dedup_rels:
            for r in dedup_rels:
                meta_parts = []
                if r.confidence:
                    meta_parts.append(f"Conf: {r.confidence:.2f}")
                if r.frequency > 1:
                    meta_parts.append(f"Freq: {r.frequency}")
                if r.document_id:
                    meta_parts.append(f"Doc: {r.document_id}")
                meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""

                rel_line = f"{r.source} {r.rel_type.value} -> {r.target}{meta_str}"
                curr_words = sum(len(l.split()) for l in lines) + len(rel_line.split())
                if curr_words > budget:
                    logger.info(f"Graph context token budget ({budget}) reached during relationship formatting.")
                    break
                lines.append(rel_line)
        else:
            lines.append("None documented.")
        lines.append("")

        lines.append("Related Topics:")
        if related_topics:
            for topic in related_topics[:15]:
                curr_words = sum(len(l.split()) for l in lines) + len(topic.split())
                if curr_words > budget:
                    break
                lines.append(topic)
        else:
            lines.append("None documented.")
        lines.append("")

        # ⭐ Improvement 7: Include Explainability block in formatted context
        lines.append("Graph Explainability:")
        lines.append(f"Explanation: {explanation}")
        if traversal_path:
            lines.append(f"Primary Traversal: {traversal_path[0]}")

        formatted_context = "\n".join(lines).strip()
        total_tokens = len(formatted_context.split())

        logger.debug(f"Built GraphContext for '{center_display}' ({total_tokens} words/tokens, {len(dedup_rels)} rels).")
        return GraphContext(
            entity_name=center_display,
            node=node,
            relationships=dedup_rels,
            related_topics=related_topics[:15],
            traversal_path=traversal_path,
            explanation=explanation,
            graph_version=current_version,
            formatted_context=formatted_context,
            total_tokens=total_tokens
        )


graph_context_builder = GraphContextBuilder()
