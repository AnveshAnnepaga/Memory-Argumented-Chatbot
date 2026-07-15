# File: app/repositories/mongodb/conversation_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.exceptions import RepositoryNotFoundException
from app.database.mongodb import mongo_manager
from app.domain.conversation import Conversation
from app.repositories.base import BaseRepository, log_and_handle_errors


class ConversationRepository(BaseRepository[Conversation]):
    """
    (`7.3 Conversation Repository`)
    Manages chat conversation documents and metadata in MongoDB (`conversations` collection).
    Responsibilities: Create conversation, Retrieve conversation, Update summary, Delete conversation, List conversations.
    """
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        super().__init__(domain_model_class=Conversation, repository_name="ConversationRepository")
        self.db = db
        self.collection_name = "conversations"
        self._memory_store: Dict[str, Conversation] = {}

    def _get_coll(self) -> Any:
        active_db = self.db or mongo_manager.get_db()
        return active_db[self.collection_name] if active_db is not None else None

    @log_and_handle_errors("create")
    async def create(self, entity: Conversation) -> Conversation:
        """Create conversation (`Create conversation`)."""
        coll = self._get_coll()
        if coll is None:
            self._memory_store[entity.id] = entity
            return entity

        payload = entity.model_dump()
        payload["_id"] = payload["id"]
        await coll.insert_one(payload)
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[Conversation]:
        """Retrieve conversation (`Retrieve conversation`)."""
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.get(entity_id)

        raw = await coll.find_one({"_id": entity_id}) or await coll.find_one({"id": entity_id})
        return self._to_domain(raw)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Conversation]:
        coll = self._get_coll()
        if coll is None:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"Conversation '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated_dict["updated_at"] = datetime.now(timezone.utc)
            updated = Conversation.model_validate(updated_dict)
            self._memory_store[entity_id] = updated
            return updated

        data["updated_at"] = datetime.now(timezone.utc)
        result = await coll.update_one(
            {"$or": [{"_id": entity_id}, {"id": entity_id}]},
            {"$set": data},
        )
        if result.matched_count == 0:
            raise RepositoryNotFoundException(f"Conversation '{entity_id}' not found in MongoDB.")
        return await self.retrieve(entity_id)

    @log_and_handle_errors("update_summary")
    async def update_summary(self, conversation_id: str, summary: str) -> Optional[Conversation]:
        """Update conversation summary (`Update summary`)."""
        return await self.update(conversation_id, {"summary": summary})

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        """Delete conversation (`Delete conversation`)."""
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.pop(entity_id, None) is not None

        result = await coll.delete_one({"$or": [{"_id": entity_id}, {"id": entity_id}]})
        return result.deleted_count > 0

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Conversation]:
        """List conversations (`List conversations`)."""
        coll = self._get_coll()
        if coll is None:
            items = list(self._memory_store.values())
            if filters and "user_id" in filters:
                items = [i for i in items if i.user_id == filters["user_id"]]
            return items[skip : skip + limit]

        query = filters or {}
        cursor = coll.find(query).skip(skip).limit(limit)
        rows = await cursor.to_list(length=limit)
        return self._to_domain_list(rows)

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        coll = self._get_coll()
        if coll is None:
            if filters and "user_id" in filters:
                return len([i for i in self._memory_store.values() if i.user_id == filters["user_id"]])
            return len(self._memory_store)
        return await coll.count_documents(filters or {})
