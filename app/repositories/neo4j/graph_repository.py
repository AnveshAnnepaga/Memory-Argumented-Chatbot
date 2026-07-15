# File: app/repositories/neo4j/graph_repository.py
from typing import Any, Dict, List, Optional
from app.database.neo4j import neo4j_manager
from app.domain.graph import GraphNode, GraphRelationship
from app.repositories.base import BaseRepository, log_and_handle_errors


class GraphRepository(BaseRepository[GraphNode]):
    """
    (`7.5 Graph Repository`)
    Low-level graph database interface executing Cypher queries and managing generic nodes & relationships.
    Responsibilities: Create node, Create relationship, Execute Cypher query, Traverse relationships.
    """
    def __init__(self):
        super().__init__(domain_model_class=GraphNode, repository_name="GraphRepository")
        self._nodes: Dict[str, GraphNode] = {}
        self._relationships: Dict[str, GraphRelationship] = {}

    def _is_stub(self) -> bool:
        return neo4j_manager.stub_mode or neo4j_manager.get_driver() is None

    @log_and_handle_errors("execute_cypher")
    async def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query (`Execute Cypher query`)."""
        if self._is_stub():
            return []
        return await neo4j_manager.execute_query(query, parameters or {})

    @log_and_handle_errors("create_node")
    async def create_node(self, node: GraphNode) -> GraphNode:
        """Create node (`Create node`)."""
        if self._is_stub():
            self._nodes[node.id] = node
            return node

        query = f"""
        MERGE (n:{node.label} {{id: $id}})
        SET n += $properties
        RETURN n
        """
        await self.execute_cypher(query, {"id": node.id, "properties": node.properties})
        return node

    @log_and_handle_errors("create_relationship")
    async def create_relationship(self, rel: GraphRelationship) -> GraphRelationship:
        """Create relationship (`Create relationship`)."""
        if self._is_stub():
            self._relationships[rel.id] = rel
            return rel

        query = f"""
        MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
        MERGE (a)-[r:{rel.relationship_type} {{id: $id}}]->(b)
        SET r += $properties
        RETURN r
        """
        await self.execute_cypher(query, {
            "source_id": rel.source_node_id,
            "target_id": rel.target_node_id,
            "id": rel.id,
            "properties": rel.properties,
        })
        return rel

    @log_and_handle_errors("traverse_relationships")
    async def traverse_relationships(self, start_node_id: str, relationship_type: Optional[str] = None, max_depth: int = 2) -> List[GraphNode]:
        """Traverse relationships (`Traverse relationships`)."""
        if self._is_stub():
            visited = []
            rel_filter = relationship_type
            for r in self._relationships.values():
                if r.source_node_id == start_node_id and (not rel_filter or r.relationship_type == rel_filter):
                    if r.target_node_id in self._nodes:
                        visited.append(self._nodes[r.target_node_id])
            return visited

        rel_clause = f"[:{relationship_type}*1..{max_depth}]" if relationship_type else f"[*1..{max_depth}]"
        query = f"""
        MATCH (a {{id: $start_id}})-{rel_clause}->(b)
        RETURN DISTINCT b
        """
        rows = await self.execute_cypher(query, {"start_id": start_node_id})
        nodes = []
        for row in rows:
            node_data = row.get("b", {})
            if isinstance(node_data, dict) and "id" in node_data:
                nodes.append(GraphNode(
                    id=node_data["id"],
                    label="Node",
                    properties=node_data,
                ))
        return nodes

    @log_and_handle_errors("create")
    async def create(self, entity: GraphNode) -> GraphNode:
        return await self.create_node(entity)

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[GraphNode]:
        if self._is_stub():
            return self._nodes.get(entity_id)

        query = "MATCH (n {id: $id}) RETURN n, labels(n) as labels"
        rows = await self.execute_cypher(query, {"id": entity_id})
        if not rows:
            return None
        row = rows[0]
        node_data = row.get("n", {})
        labels = row.get("labels", ["Node"])
        if isinstance(node_data, dict):
            return GraphNode(
                id=entity_id,
                label=labels[0] if labels else "Node",
                properties=node_data,
            )
        return None

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[GraphNode]:
        if self._is_stub():
            existing = self._nodes.get(entity_id)
            if not existing:
                return None
            existing.properties.update(data)
            return existing

        query = "MATCH (n {id: $id}) SET n += $data RETURN n"
        await self.execute_cypher(query, {"id": entity_id, "data": data})
        return await self.retrieve(entity_id)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        if self._is_stub():
            return self._nodes.pop(entity_id, None) is not None

        query = "MATCH (n {id: $id}) DETACH DELETE n"
        await self.execute_cypher(query, {"id": entity_id})
        return True

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[GraphNode]:
        if self._is_stub():
            return list(self._nodes.values())[skip : skip + limit]

        query = "MATCH (n) RETURN n, labels(n) as labels SKIP $skip LIMIT $limit"
        rows = await self.execute_cypher(query, {"skip": skip, "limit": limit})
        nodes = []
        for row in rows:
            node_data = row.get("n", {})
            labels = row.get("labels", ["Node"])
            if isinstance(node_data, dict) and "id" in node_data:
                nodes.append(GraphNode(
                    id=node_data["id"],
                    label=labels[0] if labels else "Node",
                    properties=node_data,
                ))
        return nodes

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        if self._is_stub():
            return len(self._nodes)
        rows = await self.execute_cypher("MATCH (n) RETURN count(n) as c", {})
        return rows[0]["c"] if rows else 0
