# File: app/repositories/mongodb/memory_snapshot_repository.py
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.exceptions import RepositoryNotFoundException
from app.database.mongodb import mongo_manager
from app.domain.conversation import MemorySnapshot
from app.repositories.base import BaseRepository, log_and_handle_errors


class MemorySnapshotRepository(BaseRepository[MemorySnapshot]):
    """
    (`7.3 Memory Snapshot Repository`)
    Manages episodic memory items, summaries, and archived states (`memory_snapshots` collection).
    Responsibilities: Store episodic memory, Retrieve snapshots, Archive snapshots.
    """
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        super().__init__(domain_model_class=MemorySnapshot, repository_name="MemorySnapshotRepository")
        self.db = db
        self.collection_name = "memory_snapshots"
        self._memory_store: Dict[str, MemorySnapshot] = self._load_mock_data()

    def _get_coll(self) -> Any:
        active_db = self.db or mongo_manager.get_db()
        return active_db[self.collection_name] if active_db is not None else None

    @log_and_handle_errors("store_episodic_memory")
    async def store_episodic_memory(self, snapshot: MemorySnapshot) -> MemorySnapshot:
        """Store episodic memory (`Store episodic memory`)."""
        return await self.create(snapshot)

    @log_and_handle_errors("create")
    async def create(self, entity: MemorySnapshot) -> MemorySnapshot:
        coll = self._get_coll()
        if coll is None:
            self._memory_store[entity.id] = entity
            self._save_mock_data(self._memory_store)
            return entity

        payload = entity.model_dump()
        payload["_id"] = payload["id"]
        await coll.insert_one(payload)
        return entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str) -> Optional[MemorySnapshot]:
        """Retrieve snapshot by ID (`Retrieve snapshots`)."""
        coll = self._get_coll()
        if coll is None:
            return self._memory_store.get(entity_id)

        raw = await coll.find_one({"_id": entity_id}) or await coll.find_one({"id": entity_id})
        return self._to_domain(raw)

    @log_and_handle_errors("retrieve_snapshots")
    async def retrieve_snapshots(self, user_id: str, include_archived: bool = False, skip: int = 0, limit: int = 50) -> List[MemorySnapshot]:
        """Retrieve snapshots for a user (`Retrieve snapshots`)."""
        filters: Dict[str, Any] = {"user_id": user_id}
        if not include_archived:
            filters["archived"] = False
        return await self.list(skip=skip, limit=limit, filters=filters)

    @log_and_handle_errors("archive_snapshot")
    async def archive_snapshot(self, snapshot_id: str) -> Optional[MemorySnapshot]:
        """Archive snapshot by setting archived = True (`Archive snapshots`)."""
        return await self.update(snapshot_id, {"archived": True})

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[MemorySnapshot]:
        coll = self._get_coll()
        if coll is None:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"MemorySnapshot '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated = MemorySnapshot.model_validate(updated_dict)
            self._memory_store[entity_id] = updated
            self._save_mock_data(self._memory_store)
            return updated

        result = await coll.update_one(
            {"$or": [{"_id": entity_id}, {"id": entity_id}]},
            {"$set": data},
        )
        if result.matched_count == 0:
            raise RepositoryNotFoundException(f"MemorySnapshot '{entity_id}' not found in MongoDB.")
        return await self.retrieve(entity_id)

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str) -> bool:
        coll = self._get_coll()
        if coll is None:
            popped = self._memory_store.pop(entity_id, None)
            if popped:
                self._save_mock_data(self._memory_store)
            return popped is not None

        result = await coll.delete_one({"$or": [{"_id": entity_id}, {"id": entity_id}]})
        return result.deleted_count > 0

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str) -> bool:
        return (await self.retrieve(entity_id)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[MemorySnapshot]:
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
