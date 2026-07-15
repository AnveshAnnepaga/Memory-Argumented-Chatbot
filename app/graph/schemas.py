# File: app/graph/schemas.py
"""
(`Milestone 10 GraphRAG Schemas with ⭐ Improvements 1, 2, 3, 5, 6, 7`)
Pydantic schemas representing Knowledge Graph Entities, Relationships, Nodes, Edges,
weighted frequencies, provenance evidence, graph evaluation metrics, and explainable GraphContext.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NodeType(str, Enum):
    """Fixed controlled vocabulary for graph node types."""
    TECHNOLOGY = "Technology"
    FRAMEWORK = "Framework"
    LIBRARY = "Library"
    DATABASE = "Database"
    PROGRAMMING_LANGUAGE = "ProgrammingLanguage"
    CONCEPT = "Concept"
    TOOL = "Tool"
    COMPANY = "Company"
    ORGANIZATION = "Organization"


class RelationshipType(str, Enum):
    """Fixed controlled vocabulary for graph relationship types."""
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    CONNECTS_TO = "CONNECTS_TO"
    SUPPORTED_BY = "SUPPORTED_BY"
    EXTENDS = "EXTENDS"
    RELATED_TO = "RELATED_TO"
    PART_OF = "PART_OF"
    CREATED_BY = "CREATED_BY"


class Entity(BaseModel):
    """
    Represents an extracted or retrieved node in the Knowledge Graph.
    """
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Normalized entity name (e.g., 'FastAPI', 'Pydantic')")
    node_type: NodeType = Field(default=NodeType.CONCEPT, description="Type of the node from controlled vocabulary")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata properties (description, document_id, etc.)")


# Alias for compatibility with Node/Edge nomenclature
Node = Entity


class Relationship(BaseModel):
    """
    Represents an extracted or retrieved directed edge between two entities in the Knowledge Graph.
    Includes ⭐ Improvement 1 (Confidence), ⭐ Improvement 2 (Evidence Provenance), and ⭐ Improvement 3 (Frequency).
    """
    model_config = ConfigDict(from_attributes=True)

    source: str = Field(..., description="Normalized name of the source entity")
    target: str = Field(..., description="Normalized name of the target entity")
    rel_type: RelationshipType = Field(default=RelationshipType.USES, description="Type of directed relationship from controlled vocabulary")
    
    # ⭐ Improvement 1: Graph Confidence
    confidence: float = Field(default=0.95, description="Confidence score [0.0 - 1.0] for the extracted relationship")
    
    # ⭐ Improvement 2: Relationship Evidence (Provenance)
    document_id: str = Field(default="", description="Source document ID where this relationship was discovered")
    chunk_id: str = Field(default="", description="Sanitized chunk ID providing exact text evidence")
    source_url: str = Field(default="", description="Official documentation URL where this relationship originates")
    
    # ⭐ Improvement 3: Relationship Frequency (Weighted Edges)
    frequency: int = Field(default=1, description="Number of times this exact relationship has been observed across documents")
    
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties on the edge")


# Alias for compatibility with Node/Edge nomenclature
Edge = Relationship


class ExtractionResult(BaseModel):
    """
    Result of Hybrid Entity & Relationship Extraction from a single document.
    """
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    document_title: str = ""
    document_hash: str = ""
    source_url: str = ""
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)


class GraphMetrics(BaseModel):
    """
    (`⭐ Improvement 5: Graph Evaluation Metrics & ⭐ Improvement 6: Graph Version`)
    Evaluates the structural health, connectivity, density, and extraction accuracy of the Knowledge Graph.
    """
    model_config = ConfigDict(from_attributes=True)

    total_nodes: int = Field(default=0, description="Total number of nodes in the graph")
    total_edges: int = Field(default=0, description="Total number of directed relationships in the graph")
    average_degree: float = Field(default=0.0, description="Average number of edges per node (Total Edges * 2 / Total Nodes)")
    connected_components: int = Field(default=1, description="Number of disconnected subgraphs inside the graph")
    graph_density: float = Field(default=0.0, description="Graph density ratio: E / (N * (N - 1))")
    traversal_time_ms: float = Field(default=0.0, description="Average multi-hop traversal execution latency in milliseconds")
    extraction_accuracy_score: float = Field(default=0.96, description="Benchmark NER & relationship extraction accuracy")
    graph_version: str = Field(default="1.0.0", description="Semantic version string of the graph state (e.g. '1.0.1')")


class GraphContext(BaseModel):
    """
    (`Milestone 10 Graph Context Builder Schema with ⭐ Improvement 7: Graph Explainability`)
    Structured context extracted from multi-hop neighborhood traversals,
    formatted, explainable, and budget-controlled for LangGraph prompt injection.
    """
    model_config = ConfigDict(from_attributes=True)

    entity_name: str
    node: Optional[Entity] = None
    relationships: List[Relationship] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    
    # ⭐ Improvement 7: Graph Explainability
    traversal_path: List[str] = Field(default_factory=list, description="Step-by-step traversal chain (e.g., FastAPI --[USES]--> SQLAlchemy --[CONNECTS_TO]--> PostgreSQL)")
    explanation: str = Field(default="", description="Human-readable explanation of why and how the entities are connected with confidence and provenance")
    
    graph_version: str = Field(default="1.0.0", description="Version of the graph when this context was built")
    formatted_context: str = Field(default="", description="Clean, formatted text block ready for LangGraph injection")
    total_tokens: int = Field(default=0, description="Token budget count for this graph context block")
