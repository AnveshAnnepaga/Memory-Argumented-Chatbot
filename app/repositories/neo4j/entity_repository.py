# File: app/repositories/neo4j/entity_repository.py
from typing import Any, Dict, List, Optional
from app.domain.graph import Entity, GraphNode
from app.repositories.base import BaseRepository, log_and_handle_errors
from app.repositories.neo4j.graph_repository import GraphRepository


class EntityRepository(BaseRepository[Entity]):
    """
    (`7.5 Entity Repository`)
    High-level domain repository for storing and querying extracted entities (Concepts, Persons, Topics) in Neo4j.
    Responsibilities: Store extracted entity, Retrieve entity, Find entities by type.
    """
    def __init__(self, graph_repo: Optional[GraphRepository] = None):
        super().__init__(domain_model_class=Entity, repository_name="EntityRepository")
        self.graph_repo = graph_repo or GraphRepository()
        self._entity_store: Dict[str, Entity] = {}

    @log_and_handle_errors("store_extracted_entity")
    async def store_extracted_entity(self, entity: Entity) -> Entity:
        """Store extracted entity (`Store extracted entity`)."""
        return await self.create(entity)

    @log_and_handle_errors("create")
    async def create(self, entity: Entity) -> Entity:
        self._entity_store[entity.id] = entity
        node = GraphNode(
            id=entity.id,
            label=entity.entity_type or "Entity",
            properties={
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "description": entity.description or "",
                **entity.properties,
            },
        )
        await self.graph_repo.create_node(node)
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[Entity]:
        """Retrieve entity (`Retrieve entity`)."""
        if entity_id in self._entity_store:
            return self._entity_store[entity_id]

        node = await self.graph_repo.retrieve(entity_id)
        if not node:
            return None
        props = dict(node.properties)
        return Entity(
            id=props.get("id", entity_id),
            name=props.get("name", ""),
            entity_type=props.get("entity_type", node.label),
            description=props.get("description"),
            properties={k: v for k, v in props.items() if k not in ("id", "name", "entity_type", "description")},
        )

    @log_and_handle_errors("find_entities_by_type")
    async def find_entities_by_type(self, entity_type: str, skip: int = 0, limit: int = 50) -> List[Entity]:
        """Find entities by type (`Find entities by type`)."""
        if self.graph_repo._is_stub():
            items = [e for e in self._entity_store.values() if e.entity_type == entity_type]
            return items[skip : skip + limit]

        query = f"MATCH (n:{entity_type}) RETURN n, labels(n) as labels SKIP $skip LIMIT $limit"
        rows = await self.graph_repo.execute_cypher(query, {"skip": skip, "limit": limit})
        entities = []
        for row in rows:
            props = row.get("n", {})
            labels = row.get("labels", [entity_type])
            if isinstance(props, dict) and "id" in props:
                entities.append(Entity(
                    id=props["id"],
                    name=props.get("name", ""),
                    entity_type=props.get("entity_type", labels[0] if labels else entity_type),
                    description=props.get("description"),
                    properties={k: v for k, v in props.items() if k not in ("id", "name", "entity_type", "description")},
                ))
        return entities

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Entity]:
        existing = await self.retrieve(entity_id)
        if not existing:
            return None
        dump = existing.model_dump()
        dump.update(data)
        updated = Entity.model_validate(dump)
        self._entity_store[entity_id] = updated
        await self.graph_repo.update(entity_id, dump)
        return updated

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        await self.graph_repo.delete(entity_id)
        return self._entity_store.pop(entity_id, None) is not None

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Entity]:
        if filters and "entity_type" in filters:
            return await self.find_entities_by_type(filters["entity_type"], skip=skip, limit=limit)
        return list(self._entity_store.values())[skip : skip + limit]

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        if filters and "entity_type" in filters:
            return len(await self.find_entities_by_type(filters["entity_type"], skip=0, limit=10000))
        return len(self._entity_store)
