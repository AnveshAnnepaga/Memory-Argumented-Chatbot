# File: app/domain/graph.py
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class GraphNode(BaseModel):
    """Domain model representing a generic node in Neo4j (`7.5 Graph Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphRelationship(BaseModel):
    """Domain model representing a generic relationship/edge in Neo4j (`7.5 Graph Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_node_id: str
    target_node_id: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class Entity(BaseModel):
    """Domain model representing a knowledge graph entity (`7.5 Entity Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    entity_type: str  # e.g., "Person", "Concept", "Tool", "Project"
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    """Domain model representing a typed semantic relationship between entities (`7.5 Relationship Repository`)."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_entity_id: str
    target_entity_id: str
    relation_type: str  # e.g., "USES", "KNOWS", "PART_OF", "DEPENDS_ON"
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
