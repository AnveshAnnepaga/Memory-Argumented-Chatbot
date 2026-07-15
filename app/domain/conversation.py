# File: app/domain/conversation.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(BaseModel):
    """Domain model representing a multi-turn chat interaction (`7.3 Conversation Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str = "New Conversation"
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """Domain model representing a single chat message (`7.3 Message Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySnapshot(BaseModel):
    """Domain model representing an episodic or summarized memory item (`7.3 Memory Snapshot Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    conversation_id: Optional[str] = None
    episodic_content: str
    importance_score: float = 0.5
    created_at: datetime = Field(default_factory=_utcnow)
    archived: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionHistory(BaseModel):
    """Domain model tracking a tool/function call execution (`7.3 Tool History Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: Optional[str] = None
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    execution_time_ms: float = 0.0
    success: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
    error_message: Optional[str] = None


class RouterDecisionHistory(BaseModel):
    """Domain model capturing routing agent decisions (`7.3 Router History Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: Optional[str] = None
    query: str
    chosen_route: str  # e.g., "vector_rag", "graph_rag", "hybrid", "direct_chat"
    confidence_score: float = 1.0
    reasoning: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)


class PromptHistoryItem(BaseModel):
    """Domain model logging prompt templates and rendered outputs (`7.3 Prompt History Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: Optional[str] = None
    prompt_template_name: str
    rendered_prompt: str
    model_name: str
    created_at: datetime = Field(default_factory=_utcnow)
