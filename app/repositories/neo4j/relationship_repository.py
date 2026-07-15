# File: app/repositories/neo4j/relationship_repository.py
from typing import Any, Dict, List, Optional
from app.domain.graph import Entity, GraphRelationship, Relationship
from app.repositories.base import BaseRepository, log_and_handle_errors
from app.repositories.neo4j.entity_repository import EntityRepository
from app.repositories.neo4j.graph_repository import GraphRepository


class RelationshipRepository(BaseRepository[Relationship]):
    """
    (`7.5 Relationship Repository`)
    High-level domain repository for managing typed edges and multi-hop entity connections in Neo4j.
    Responsibilities: Store relationship between entities, Find connected entities, Get subgraph.
    """
    def __init__(self, graph_repo: Optional[GraphRepository] = None, entity_repo: Optional[EntityRepository] = None):
        super().__init__(domain_model_class=Relationship, repository_name="RelationshipRepository")
        self.graph_repo = graph_repo or GraphRepository()
        self.entity_repo = entity_repo or EntityRepository(graph_repo=self.graph_repo)
        self._rel_store: Dict[str, Relationship] = {}

    @log_and_handle_errors("store_relationship")
    async def store_relationship(self, relationship: Relationship) -> Relationship:
        """Store relationship between entities (`Store relationship between entities`)."""
        return await self.create(relationship)

    @log_and_handle_errors("create")
    async def create(self, entity: Relationship) -> Relationship:
        self._rel_store[entity.id] = entity
        g_rel = GraphRelationship(
            id=entity.id,
            source_node_id=entity.source_entity_id,
            target_node_id=entity.target_entity_id,
            relationship_type=entity.relation_type,
            properties={
                "id": entity.id,
                "weight": entity.weight,
                **entity.properties,
            },
        )
        await self.graph_repo.create_relationship(g_rel)
        return entity

    @log_and_handle_errors("find_connected_entities")
    async def find_connected_entities(self, entity_id: str, relation_type: Optional[str] = None, max_depth: int = 2) -> List[Entity]:
        """Find connected entities via graph traversal (`Find connected entities`)."""
        nodes = await self.graph_repo.traverse_relationships(
            start_node_id=entity_id,
            relationship_type=relation_type,
            max_depth=max_depth,
        )
        entities = []
        for n in nodes:
            e = await self.entity_repo.retrieve(n.id)
            if e:
                entities.append(e)
            else:
                entities.append(Entity(
                    id=n.id,
                    name=str(n.properties.get("name", n.id)),
                    entity_type=n.label,
                    properties=n.properties,
                ))
        return entities

    @log_and_handle_errors("get_subgraph")
    async def get_subgraph(self, center_entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """Retrieve local knowledge subgraph around a central entity (`Get subgraph`)."""
        if self.graph_repo._is_stub():
            nodes = [await self.entity_repo.retrieve(center_entity_id)]
            connected = await self.find_connected_entities(center_entity_id, max_depth=depth)
            nodes.extend(connected)
            nodes = [n for n in nodes if n is not None]
            node_ids = {n.id for n in nodes}
            edges = [r for r in self._rel_store.values() if r.source_entity_id in node_ids and r.target_entity_id in node_ids]
            return {"nodes": [n.model_dump() for n in nodes], "relationships": [r.model_dump() for r in edges]}

        query = f"""
        MATCH (a {{id: $id}})-[r*1..{depth}]-(b)
        RETURN DISTINCT a, r, b
        """
        rows = await self.graph_repo.execute_cypher(query, {"id": center_entity_id})
        nodes_dict: Dict[str, Any] = {}
        rels_list: List[Any] = []
        for row in rows:
            for n_key in ("a", "b"):
                node_props = row.get(n_key, {})
                if isinstance(node_props, dict) and "id" in node_props:
                    nodes_dict[node_props["id"]] = node_props
            r_list = row.get("r", [])
            if isinstance(r_list, list):
                for rel_props in r_list:
                    if isinstance(rel_props, dict) and "id" in rel_props:
                        rels_list.append(rel_props)
        return {"nodes": list(nodes_dict.values()), "relationships": rels_list}

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[Relationship]:
        return self._rel_store.get(entity_id)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Relationship]:
        existing = self._rel_store.get(entity_id)
        if not existing:
            return None
        dump = existing.model_dump()
        dump.update(data)
        updated = Relationship.model_validate(dump)
        self._rel_store[entity_id] = updated
        return updated

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        return self._rel_store.pop(entity_id, None) is not None

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return entity_id in self._rel_store

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Relationship]:
        items = list(self._rel_store.values())
        if filters:
            for k, v in filters.items():
                items = [i for i in items if getattr(i, k, None) == v]
        return items[skip : skip + limit]

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(await self.list(skip=0, limit=10000, filters=filters))
