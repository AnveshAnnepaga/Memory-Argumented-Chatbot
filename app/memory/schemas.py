# File: app/memory/schemas.py
"""
(`Milestone 12 Long-Term Memory System Schemas`)
Pydantic schemas governing the 4 independent memory types (Conversation, Semantic, Episodic, Profile),
memory extraction decisions, ranking scores, and consolidated memory context for LangGraph.
Strictly adheres to Single Responsibility Principle and strong typing.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MemoryType(str, Enum):
    """The four independent memory storage types managed by Milestone 12."""
    CONVERSATION = "CONVERSATION"  # Short-term recent window -> MongoDB
    SEMANTIC = "SEMANTIC"          # Long-term user facts/preferences -> Pinecone vector index
    EPISODIC = "EPISODIC"          # Significant events/milestones -> MongoDB
    PROFILE = "PROFILE"            # Structured user profile attributes -> PostgreSQL
    SUMMARY = "SUMMARY"            # Compressed conversation archival -> MongoDB


class MemoryAction(str, Enum):
    """Action determined by the Memory Extractor for each candidate information piece."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    IGNORE = "IGNORE"
    MERGE = "MERGE"


class ConversationMemory(BaseModel):
    """
    (`1. Conversation Memory`)
    Short-term contextual conversation turn stored in MongoDB NoSQL store.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique record ID")
    conversation_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    role: str = Field(..., description="Turn role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    timestamp: datetime = Field(default_factory=_utcnow)
    importance_score: float = Field(default=0.3, ge=0.0, le=1.0)
    access_count: int = Field(default=1, ge=0)


class SemanticMemory(BaseModel):
    """
    (`2. Semantic Memory`)
    Enduring user facts and technical preferences embedded (`embedder.embed_query`) and indexed into Pinecone.
    Survives indefinitely until explicitly updated or superseded.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique semantic fact ID (UUID or hash)")
    user_id: str = Field(..., description="User identifier")
    fact: str = Field(..., description="Natural language fact description (e.g. 'User prefers Python')")
    category: str = Field(default="preference", description="Fact category: preference, occupation, stack, skill, hobby")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.8, ge=0.0, le=1.0)
    recency_score: float = Field(default=1.0, ge=0.0, le=1.0)
    access_count: int = Field(default=1, ge=0)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    last_accessed: datetime = Field(default_factory=_utcnow)

    @property
    def timestamp(self) -> datetime:
        return self.updated_at


class Episode(BaseModel):
    """
    (`3. Episodic Memory`)
    Significant milestones, completed tasks, or deployment events stored in MongoDB.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique episode ID")
    user_id: str = Field(..., description="User identifier")
    event: str = Field(default="", description="Description of the event or accomplishment")
    event_type: Optional[str] = Field(default="milestone", description="Type of episodic event")
    description: Optional[str] = Field(default=None, description="Detailed description of event")
    context: Dict[str, Any] = Field(default_factory=dict, description="Metadata or tags associated with the episode")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.9, ge=0.0, le=1.0)
    recency_score: float = Field(default=1.0, ge=0.0, le=1.0)
    access_count: int = Field(default=1, ge=0)
    timestamp: datetime = Field(default_factory=_utcnow)
    last_accessed: datetime = Field(default_factory=_utcnow)

    def __init__(self, **data: Any):
        if "description" in data and not data.get("event"):
            data["event"] = data["description"]
        elif "event" in data and not data.get("description"):
            data["description"] = data["event"]
        super().__init__(**data)


class UserProfile(BaseModel):
    """
    (`4. Profile Memory`)
    Structured core demographic and professional attributes stored in PostgreSQL.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(..., description="Unique user identifier")
    name: Optional[str] = Field(default=None, description="User full or first name")
    full_name: Optional[str] = Field(default=None, description="Full name alias")
    role: Optional[str] = Field(default=None, description="Professional title or role")
    occupation: Optional[str] = Field(default=None, description="Professional occupation alias")
    preferred_language: Optional[str] = Field(default=None, description="Primary programming or spoken language")
    timezone: Optional[str] = Field(default=None, description="User geographic timezone")
    experience: Optional[str] = Field(default=None, description="Experience level (e.g. Senior, Intermediate, Beginner)")
    interests: List[str] = Field(default_factory=list, description="Known technical domains or topics of interest")
    projects: List[str] = Field(default_factory=list, description="Active or historical project names")
    updated_at: datetime = Field(default_factory=_utcnow)
    access_count: int = Field(default=1, ge=0)

    def __init__(self, **data: Any):
        if "full_name" in data and not data.get("name"):
            data["name"] = data["full_name"]
        elif "name" in data and not data.get("full_name"):
            data["full_name"] = data["name"]
        if "role" in data and not data.get("occupation"):
            data["occupation"] = data["role"]
        elif "occupation" in data and not data.get("role"):
            data["role"] = data["occupation"]
        super().__init__(**data)


class MemoryExtractionItem(BaseModel):
    """Individual extracted candidate memory outputted by the Memory Extractor."""
    model_config = ConfigDict(from_attributes=True)

    action: MemoryAction = Field(default=MemoryAction.CREATE)
    memory_type: MemoryType = Field(default=MemoryType.SEMANTIC)
    content: str = Field(..., description="Fact text, event text, or profile summary string")
    key: Optional[str] = Field(default=None, description="Profile attribute key or semantic category")
    value: Optional[str] = Field(default=None, description="Exact value for profile or semantic override")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.7, ge=0.0, le=1.0)
    reasoning: str = Field(default="", description="Why this memory extraction decision was made")


class MemoryExtractionResult(BaseModel):
    """Complete extraction payload emitted by the intelligence layer."""
    model_config = ConfigDict(from_attributes=True)

    should_remember: bool = Field(default=False, description="True if at least one meaningful memory item was extracted")
    extracted_items: List[MemoryExtractionItem] = Field(default_factory=list)
    raw_llm_reasoning: str = Field(default="")


class MemoryContext(BaseModel):
    """
    Consolidated multi-type memory block retrieved by `MemoryRetriever`.
    Injected directly into LangGraph (`Prompt Builder Node`) when invoked.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    conversation_window: List[ConversationMemory] = Field(default_factory=list)
    semantic_facts: List[SemanticMemory] = Field(default_factory=list)
    recent_episodes: List[Episode] = Field(default_factory=list)
    user_profile: Optional[UserProfile] = Field(default=None)
    formatted_context: str = Field(default="", description="Deduplicated, ordered markdown block for LLM prompts")
    total_tokens: int = Field(default=0, ge=0)
