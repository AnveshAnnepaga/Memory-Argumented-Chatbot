# File: app/repositories/mongodb/router_history_repository.py
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.exceptions import RepositoryNotFoundException
from app.database.mongodb import mongo_manager
from app.domain.conversation import RouterDecisionHistory
from app.repositories.base import BaseRepository, log_and_handle_errors


class RouterHistoryRepository(BaseRepository[RouterDecisionHistory]):
    """
    (`7.3 Router History Repository`)
    Logs LangGraph semantic router decisions, selected models/skills, and confidences (`router_history` collection).
    Responsibilities: Save routing decisions, Retrieve routing analytics.
    """
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        super().__init__(domain_model_class=RouterDecisionHistory, repository_name="RouterHistoryRepository")
        self.db = db
        self.collection_name = "router_history"
        self._memory_store: Dict[str, RouterDecisionHistory] = {}

    def _get_coll(self) -> Any:
        active_db = self.db or mongo_manager.get_db()
        return active_db[self.collection_name] if active_db is not None else None

    @log_and_handle_errors("save_routing_decision")
    async def save_routing_decision(self, entity: RouterDecisionHistory) -> RouterDecisionHistory:
        """Save routing decision (`Save routing decisions`)."""
        return await self.create(entity)

    @log_and_handle_errors("create")
    async def create(self, entity: RouterDecisionHistory) -> RouterDecisionHistory:
        coll = self._get_coll()
        if coll is None:
            self._memory_store[entity.id] = entity
            return entity

        payload = entity.model_dump()
        payload["_id"] = payload["id"]
        await coll.insert_one(payload)
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[RouterDecisionHistory]:
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.get(entity_id)

        raw = await coll.find_one({"_id": entity_id}) or await coll.find_one({"id": entity_id})
        return self._to_domain(raw)

    @log_and_handle_errors("retrieve_routing_analytics")
    async def retrieve_routing_analytics(self, conversation_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[RouterDecisionHistory]:
        """Retrieve routing history and analytics (`Retrieve routing analytics`)."""
        filters: Dict[str, Any] = {}
        if conversation_id:
            filters["conversation_id"] = conversation_id
        return await self.list(skip=skip, limit=limit, filters=filters)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[RouterDecisionHistory]:
        coll = self._get_coll()
        if coll is None:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"RouterDecisionHistory '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated = RouterDecisionHistory.model_validate(updated_dict)
            self._memory_store[entity_id] = updated
            return updated

        result = await coll.update_one(
            {"$or": [{"_id": entity_id}, {"id": entity_id}]},
            {"$set": data},
        )
        if result.matched_count == 0:
            raise RepositoryNotFoundException(f"RouterDecisionHistory '{entity_id}' not found in MongoDB.")
        return await self.retrieve(entity_id)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.pop(entity_id, None) is not None

        result = await coll.delete_one({"$or": [{"_id": entity_id}, {"id": entity_id}]})
        return result.deleted_count > 0

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[RouterDecisionHistory]:
        coll = self._get_coll()
        if coll is None:
            items = list(self._memory_store.values())
            if filters:
                for k, v in filters.items():
                    items = [i for i in items if getattr(i, k, None) == v]
            return items[skip : skip + limit]

        query = filters or {}
        cursor = coll.find(query).skip(skip).limit(limit)
        rows = await cursor.to_list(length=limit)
        return self._to_domain_list(rows)

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        coll = self._get_coll()
        if coll is None:
            items = list(self._memory_store.values())
            if filters:
                for k, v in filters.items():
                    items = [i for i in items if getattr(i, k, None) == v]
            return len(items)
        return await coll.count_documents(filters or {})
