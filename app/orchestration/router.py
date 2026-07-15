# File: app/orchestration/router.py
"""
(`Milestone 11 Intelligent Router - Decision Engine`)
Classifies incoming user queries and determines the optimal execution route (`RouteType`).
Strictly operates without calling the LLM to ensure sub-millisecond classification latency.
"""
import logging
import re
from typing import List, Optional, Set, Tuple

from app.orchestration.schemas import (
    IntentResult,
    IntentType,
    RouterDecision,
    RouteType,
)

logger = logging.getLogger("app.orchestration.router")


# Pre-compiled regex patterns for deterministic high-speed classification
_GREETING_PATTERNS = re.compile(
    r"^\s*(hello|hi|hey|good\s*(morning|afternoon|evening)|howdy|greetings|what'?s\s*up|how\s*are\s*you|who\s*are\s*you|thanks|thank\s*you|bye|goodbye)\b",
    re.IGNORECASE,
)

_RELATIONSHIP_PATTERNS = re.compile(
    r"\b(related\s*to|connected\s*to|relationship\s*between|connection\s*between|depends\s*on|relies\s*on|uses|using|implements|shortest\s*path|neighborhood|extends|part\s*of|supported\s*by)\b",
    re.IGNORECASE,
)

_EXPLANATION_PATTERNS = re.compile(
    r"\b(what\s*is|what\s*are|explain|how\s*does|how\s*do|describe|guide|tutorial|documentation|code|example|architecture|setup|config|configuration|difference\s*between)\b",
    re.IGNORECASE,
)

# Known technical concepts dictionary for instant keyword extraction
_TECHNICAL_VOCAB: Set[str] = {
    "fastapi", "python", "pydantic", "starlette", "uvicorn", "langchain", "langgraph",
    "stategraph", "postgresql", "postgres", "neo4j", "cypher", "groq", "asyncio",
    "sqlalchemy", "pytest", "redis", "pinecone", "docker", "kubernetes",
    "dependency injection", "mvcc", "concurrency", "rrf", "reciprocal rank fusion",
    "bm25", "rag", "graphrag", "embedding", "vector", "hybrid", "chunking",
}


class IntelligentRouter:
    """
    (`2️⃣ router.py`)
    The central decision engine for LangGraph Orchestration.
    Analyzes query intent, extracts domain keywords, and emits a clean `RouterDecision` and `IntentResult`.
    Does NOT call the LLM directly.
    """
    def __init__(self):
        pass

    def _extract_keywords(self, query: str) -> List[str]:
        """Extracts technical terms and normalized domain keywords from the user prompt."""
        lower_query = query.lower()
        found: Set[str] = set()
        
        # Check against known vocabulary
        for term in _TECHNICAL_VOCAB:
            if re.search(rf"\b{re.escape(term)}\b", lower_query):
                found.add(term)
                
        # Extract capitalized technical terms (e.g. StateGraph, Uvicorn)
        ignore_words = {
            "The", "This", "When", "If", "For", "With", "And", "Or", "Using",
            "How", "What", "Why", "Where", "Can", "Could", "Should", "Tell",
            "Hello", "Hi", "Hey", "Greetings", "Thanks", "Thank", "Good",
            "Morning", "Afternoon", "Evening", "There", "Who", "Are", "You"
        }
        for match in re.findall(r"\b([A-Z][a-zA-Z0-9_]{2,25})\b", query):
            if match not in ignore_words and match.lower() not in ignore_words:
                found.add(match)

        return sorted(list(found))

    def analyze_intent(self, user_query: str) -> IntentResult:
        """
        Classifies the user query into high-level intent (`IntentType`) and extracts domain keywords.
        """
        clean_query = user_query.strip()
        keywords = self._extract_keywords(clean_query)

        # 1. Check for pure greetings or conversational pleasantries
        if _GREETING_PATTERNS.match(clean_query) and not any(k.lower() in _TECHNICAL_VOCAB for k in keywords):
            return IntentResult(
                intent=IntentType.GREETING,
                confidence=0.99,
                keywords=keywords,
                reasoning="Matched standard conversational greeting without technical terms."
            )

        has_rel = bool(_RELATIONSHIP_PATTERNS.search(clean_query))
        has_exp = bool(_EXPLANATION_PATTERNS.search(clean_query))

        # 2. Check for mixed reasoning (both deep explanation/documentation AND structural relationship queries)
        if has_rel and (has_exp or len(keywords) >= 2):
            # Example: "Explain FastAPI and how it depends on Starlette."
            if "and how" in clean_query.lower() or "and what" in clean_query.lower() or "explain" in clean_query.lower() and "depend" in clean_query.lower():
                return IntentResult(
                    intent=IntentType.MIXED_REASONING,
                    confidence=0.97,
                    keywords=keywords,
                    reasoning="Query requests both comprehensive technical explanation and structural graph relationships."
                )

        # 3. Check for specific relationship / structural queries
        if has_rel and not clean_query.lower().startswith(("what is", "explain ")):
            # Example: "How is FastAPI related to Starlette?"
            return IntentResult(
                intent=IntentType.RELATIONSHIP_QUERY,
                confidence=0.96,
                keywords=keywords,
                reasoning="Query explicitly focuses on connections, dependencies, or relationship traversals between entities."
            )

        # 4. Check for technical documentation queries
        if has_exp or len(keywords) > 0:
            return IntentResult(
                intent=IntentType.TECHNICAL_DOCS,
                confidence=0.95,
                keywords=keywords,
                reasoning="Query requests technical documentation, conceptual definition, or how-to explanation."
            )

        # 5. Default fallback to general chat
        return IntentResult(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.90,
            keywords=keywords,
            reasoning="Query does not match specific technical or relational retrieval triggers."
        )

    def route_query(self, user_query: str, intent_result: Optional[IntentResult] = None) -> RouterDecision:
        """
        Determines the exact execution route (`RouteType`) based on semantic analysis and intent classification.
        """
        intent = intent_result or self.analyze_intent(user_query)

        if intent.intent == IntentType.GREETING or intent.intent == IntentType.GENERAL_CHAT:
            return RouterDecision(
                route=RouteType.DIRECT_LLM,
                confidence=intent.confidence,
                requires_rag=False,
                requires_graph=False,
                requires_memory=False,  # Placeholder for M12
                requires_tools=False,   # Placeholder for M13
                reasoning=f"Classified as {intent.intent.value}; routing directly to LLM without vector/graph overhead."
            )

        if intent.intent == IntentType.RELATIONSHIP_QUERY:
            return RouterDecision(
                route=RouteType.GRAPH_RAG,
                confidence=intent.confidence,
                requires_rag=False,
                requires_graph=True,
                requires_memory=False,
                requires_tools=False,
                reasoning="Classified as RELATIONSHIP_QUERY; routing directly to Knowledge Graph (Neo4j) for structural traversal."
            )

        if intent.intent == IntentType.MIXED_REASONING:
            return RouterDecision(
                route=RouteType.HYBRID_SYNTHESIS,
                confidence=intent.confidence,
                requires_rag=True,
                requires_graph=True,
                requires_memory=False,
                requires_tools=False,
                reasoning="Classified as MIXED_REASONING; executing both Hybrid RAG and GraphRAG to synthesize comprehensive context."
            )

        # Default for TECHNICAL_DOCS
        return RouterDecision(
            route=RouteType.HYBRID_RAG,
            confidence=intent.confidence,
            requires_rag=True,
            requires_graph=False,
            requires_memory=False,
            requires_tools=False,
            reasoning="Classified as TECHNICAL_DOCS; routing to Hybrid RAG (Dense Vector + BM25 + Cross-Encoder Reranker)."
        )


intelligent_router = IntelligentRouter()
