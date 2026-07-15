# File: app/repositories/mongodb/message_repository.py
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.exceptions import RepositoryNotFoundException
from app.database.mongodb import mongo_manager
from app.domain.conversation import Message
from app.repositories.base import BaseRepository, log_and_handle_errors


class MessageRepository(BaseRepository[Message]):
    """
    (`7.3 Message Repository`)
    Manages chat message history and token usage records in MongoDB (`messages` collection).
    Responsibilities: Store messages, Retrieve messages, Delete messages, Paginate messages.
    """
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        super().__init__(domain_model_class=Message, repository_name="MessageRepository")
        self.db = db
        self.collection_name = "messages"
        self._memory_store: Dict[str, Message] = {}

    def _get_coll(self) -> Any:
        active_db = self.db or mongo_manager.get_db()
        return active_db[self.collection_name] if active_db is not None else None

    @log_and_handle_errors("store_messages")
    async def store_messages(self, messages: List[Message]) -> List[Message]:
        """Bulk store messages (`Store messages`)."""
        coll = self._get_coll()
        if coll is None:
            for m in messages:
                self._memory_store[m.id] = m
            return messages

        payloads = []
        for m in messages:
            dump = m.model_dump()
            dump["_id"] = dump["id"]
            payloads.append(dump)
        if payloads:
            await coll.insert_many(payloads)
        return messages

    @log_and_handle_errors("create")
    async def create(self, entity: Message) -> Message:
        await self.store_messages([entity])
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[Message]:
        """Retrieve message by ID (`Retrieve messages`)."""
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.get(entity_id)

        raw = await coll.find_one({"_id": entity_id}) or await coll.find_one({"id": entity_id})
        return self._to_domain(raw)

    @log_and_handle_errors("retrieve_messages")
    async def retrieve_messages(self, conversation_id: str, skip: int = 0, limit: int = 100) -> List[Message]:
        """Retrieve messages for a conversation (`Retrieve messages`, `Paginate messages`)."""
        return await self.list(skip=skip, limit=limit, filters={"conversation_id": conversation_id})

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Message]:
        coll = self._get_coll()
        if coll is None:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"Message '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated = Message.model_validate(updated_dict)
            self._memory_store[entity_id] = updated
            return updated

        result = await coll.update_one(
            {"$or": [{"_id": entity_id}, {"id": entity_id}]},
            {"$set": data},
        )
        if result.matched_count == 0:
            raise RepositoryNotFoundException(f"Message '{entity_id}' not found in MongoDB.")
        return await self.retrieve(entity_id)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        """Delete message by ID (`Delete messages`)."""
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.pop(entity_id, None) is not None

        result = await coll.delete_one({"$or": [{"_id": entity_id}, {"id": entity_id}]})
        return result.deleted_count > 0

    @log_and_handle_errors("delete_by_conversation")
    async def delete_by_conversation(self, conversation_id: str) -> int:
        """Delete all messages inside a conversation (`Delete messages`)."""
        coll = self._get_coll()
        if coll is None:
            to_remove = [k for k, v in self._memory_store.items() if v.conversation_id == conversation_id]
            for k in to_remove:
                del self._memory_store[k]
            return len(to_remove)

        result = await coll.delete_many({"conversation_id": conversation_id})
        return result.deleted_count

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Message]:
        """List and paginate messages (`Paginate messages`)."""
        coll = self._get_coll()
        if coll is None:
            items = list(self._memory_store.values())
            if filters and "conversation_id" in filters:
                items = [i for i in items if i.conversation_id == filters["conversation_id"]]
            return items[skip : skip + limit]

        query = filters or {}
        cursor = coll.find(query).sort("created_at", 1).skip(skip).limit(limit)
        rows = await cursor.to_list(length=limit)
        return self._to_domain_list(rows)

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        coll = self._get_coll()
        if coll is None:
            if filters and "conversation_id" in filters:
                return len([i for i in self._memory_store.values() if i.conversation_id == filters["conversation_id"]])
            return len(self._memory_store)
        return await coll.count_documents(filters or {})
