# File: app/domain/user.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(BaseModel):
    """Domain model representing an authenticated user (`7.2 User Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class UserProfile(BaseModel):
    """Domain model representing user preferences and profile attributes (`7.2 User Profile Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=_utcnow)


class Session(BaseModel):
    """Domain model representing an active user login or WebSocket session (`7.2 Session Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: Optional[datetime] = None


class KnowledgeSource(BaseModel):
    """Domain model representing an external knowledge crawl or ingestion source (`7.2 Knowledge Source Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: str  # e.g., "url", "pdf", "confluence", "s3"
    uri: str
    name: str
    status: str = "pending"  # "pending", "crawling", "completed", "failed"
    crawl_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class EvaluationResult(BaseModel):
    """Domain model representing RAG/LLM evaluation metrics (`7.2 Evaluation Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: Optional[str] = None
    metric_name: str  # e.g., "faithfulness", "answer_relevance", "context_precision"
    score: float
    reasoning: Optional[str] = None
    evaluator_version: str = "v1.0"
    created_at: datetime = Field(default_factory=_utcnow)


class ConfigurationItem(BaseModel):
    """Domain model representing dynamic system runtime configuration (`7.2 Configuration Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: Any
    description: Optional[str] = None
    is_sensitive: bool = False
    updated_at: datetime = Field(default_factory=_utcnow)
