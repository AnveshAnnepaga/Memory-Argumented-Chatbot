# File: app/repositories/postgres/evaluation_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, DateTime, Float, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import RepositoryNotFoundException
from app.database.postgres import Base, postgres_manager
from app.domain.user import EvaluationResult
from app.repositories.base import BaseRepository, log_and_handle_errors


class EvaluationResultTable(Base):
    """SQLAlchemy ORM table definition for evaluation scores and reasoning (`7.2 Evaluation Repository`)."""
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, index=True, nullable=True)
    metric_name = Column(String, index=True, nullable=False)
    score = Column(Float, nullable=False)
    reasoning = Column(String, nullable=True)
    evaluator_version = Column(String, default="v1.0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class EvaluationRepository(BaseRepository[EvaluationResult]):
    """
    (`7.2 Evaluation Repository`)
    Stores Ragas/DeepEval benchmark scores, faithfulness metrics, and latency analytics.
    Responsibilities: Save evaluation metrics, Fetch evaluation history.
    """
    def __init__(self, session: Optional[AsyncSession] = None):
        super().__init__(domain_model_class=EvaluationResult, repository_name="EvaluationRepository")
        self.session = session
        self._memory_store: Dict[str, EvaluationResult] = self._load_mock_data()

    def _is_stub(self) -> bool:
        return self.session is None and (postgres_manager.stub_mode or postgres_manager.session_factory is None)

    @log_and_handle_errors("save_metrics")
    async def save_metrics(self, entity: EvaluationResult, session: Optional[AsyncSession] = None) -> EvaluationResult:
        """Save evaluation metrics (`Save evaluation metrics`)."""
        return await self.create(entity, session=session)

    @log_and_handle_errors("create")
    async def create(self, entity: EvaluationResult, session: Optional[AsyncSession] = None) -> EvaluationResult:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            self._memory_store[entity.id] = entity
            self._save_mock_data(self._memory_store)
            return entity

        row = EvaluationResultTable(
            id=entity.id,
            conversation_id=entity.conversation_id,
            metric_name=entity.metric_name,
            score=entity.score,
            reasoning=entity.reasoning,
            evaluator_version=entity.evaluator_version,
            created_at=entity.created_at,
        )
        active_session.add(row)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row) or entity

    @log_and_handle_errors("retrieve")
    async def retrieve(self, entity_id: str, session: Optional[AsyncSession] = None) -> Optional[EvaluationResult]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            return self._memory_store.get(entity_id)

        stmt = select(EvaluationResultTable).where(EvaluationResultTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row)

    @log_and_handle_errors("update")
    async def update(self, entity_id: str, data: Dict[str, Any], session: Optional[AsyncSession] = None) -> Optional[EvaluationResult]:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            existing = self._memory_store.get(entity_id)
            if not existing:
                raise RepositoryNotFoundException(f"EvaluationResult '{entity_id}' not found.")
            updated_dict = existing.model_dump()
            updated_dict.update(data)
            updated_eval = EvaluationResult.model_validate(updated_dict)
            self._memory_store[entity_id] = updated_eval
            self._save_mock_data(self._memory_store)
            return updated_eval

        stmt = select(EvaluationResultTable).where(EvaluationResultTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise RepositoryNotFoundException(f"EvaluationResult '{entity_id}' not found in database.")

        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        await active_session.commit()
        await active_session.refresh(row)
        return self._to_domain(row)

    @log_and_handle_errors("fetch_evaluation_history")
    async def fetch_evaluation_history(self, conversation_id: Optional[str] = None, metric_name: Optional[str] = None, skip: int = 0, limit: int = 50, session: Optional[AsyncSession] = None) -> List[EvaluationResult]:
        """Fetch evaluation history with optional filters (`Fetch evaluation history`)."""
        active_session = session or self.session
        if self._is_stub() or not active_session:
            items = list(self._memory_store.values())
            if conversation_id:
                items = [i for i in items if i.conversation_id == conversation_id]
            if metric_name:
                items = [i for i in items if i.metric_name == metric_name]
            return items[skip : skip + limit]

        stmt = select(EvaluationResultTable)
        if conversation_id:
            stmt = stmt.where(EvaluationResultTable.conversation_id == conversation_id)
        if metric_name:
            stmt = stmt.where(EvaluationResultTable.metric_name == metric_name)
        stmt = stmt.offset(skip).limit(limit)
        result = await active_session.execute(stmt)
        rows = result.scalars().all()
        return self._to_domain_list(list(rows))

    @log_and_handle_errors("delete")
    async def delete(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        active_session = session or self.session
        if self._is_stub() or not active_session:
            popped = self._memory_store.pop(entity_id, None)
            if popped:
                self._save_mock_data(self._memory_store)
            return popped is not None

        stmt = select(EvaluationResultTable).where(EvaluationResultTable.id == entity_id)
        result = await active_session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await active_session.delete(row)
        await active_session.commit()
        return True

    @log_and_handle_errors("exists")
    async def exists(self, entity_id: str, session: Optional[AsyncSession] = None) -> bool:
        return (await self.retrieve(entity_id, session=session)) is not None

    @log_and_handle_errors("list")
    async def list(self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> List[EvaluationResult]:
        return await self.fetch_evaluation_history(skip=skip, limit=limit, session=session)

    @log_and_handle_errors("count")
    async def count(self, filters: Optional[Dict[str, Any]] = None, session: Optional[AsyncSession] = None) -> int:
        if self._is_stub() or not (session or self.session):
            return len(self._memory_store)
        return len(await self.list(skip=0, limit=10000, filters=filters, session=session))
