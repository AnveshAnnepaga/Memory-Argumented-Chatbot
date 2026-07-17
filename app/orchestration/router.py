# File: app/orchestration/router.py
"""
(`Milestone 11 Intelligent Router - Decision Engine`)
Classifies incoming user queries and determines the optimal execution route (`RouteType`).
Strictly operates without calling the LLM to ensure sub-millisecond classification latency.

Architecture Improvements:
- Dynamically flags `requires_memory` / `requires_tools` based on rule-based heuristics
  (no longer hardcoded to False).
- Routes personalized queries to MEMORY_ENHANCED so Long-Term Memory enriches Groq.
- Routes real-time/data-driven queries to TOOLS_ENHANCED so Tool Pipeline fires.
- Falls back gracefully when no retrieval context is available -> still calls Groq LLM
  using its base knowledge with a clean system prompt.
"""
import logging
import re
from typing import List, Optional, Set, Tuple

from app.core.config import settings
from app.orchestration.schemas import (
    IntentResult,
    IntentType,
    RouterDecision,
    RouteType,
)

logger = logging.getLogger("app.orchestration.router")


# -----------------------------------------------------------------------------
# Regex Patterns (deterministic high-speed classification)
# -----------------------------------------------------------------------------
_GREETING_PATTERNS = re.compile(
    r"^\s*(hello|hi|hey|good\s*(morning|afternoon|evening)|howdy|greetings|"
    r"what'?s\s*up|how\s*are\s*you|who\s*are\s*you|thanks|thank\s*you|"
    r"bye|goodbye)\b",
    re.IGNORECASE,
)

_RELATIONSHIP_PATTERNS = re.compile(
    r"\b(related\s*to|connected\s*to|relationship\s*between|connection\s*between|"
    r"depends\s*on|relies\s*on|uses|using|implements|shortest\s*path|"
    r"neighborhood|extends|part\s*of|supported\s*by)\b",
    re.IGNORECASE,
)

_EXPLANATION_PATTERNS = re.compile(
    r"\b(what\s*is|what\s*are|explain|how\s*does|how\s*do|describe|guide|"
    r"tutorial|documentation|code|example|architecture|setup|config|"
    r"configuration|difference\s*between|define|meaning\s*of|overview\s*of)\b",
    re.IGNORECASE,
)

_PERSONAL_PATTERNS = re.compile(
    r"\b(my\s+name|i\s+am|i'?m|remember\s+that|do\s+you\s+remember|"
    r"what\s+did\s+i|earlier\s+i|previously\s+i|you\s+know\s+that|"
    r"my\s+favorite|my\s+preference|as\s+we\s+discussed|last\s+time\s+we|"
    r"according\s+to\s+my|what\s+(?:is|'s)\s+my|what\s+is\s+my|"
    r"my\s+(?:cgpa|gpa|name|age|location|education|cgpa|degree))\b",
    re.IGNORECASE,
)

_TOOL_PATTERNS = re.compile(
    r"\b(weather|temperature|forecast|rain|cloudy|sunny|humidity|wind|"
    r"calculate|compute|sqrt|sin\(|cos\(|tan\(|"
    r"convert\s+\d|usd|inr|eur|gbp|jpy|exchange\s+rate|currency|"
    r"current\s+time|what\s+time|today'?s\s+date|timezone|utc|local\s+time|"
    r"translate\s+|in\s+spanish|in\s+french|in\s+german|in\s+japanese|"
    r"search\s+the\s+web|latest\s+news|web\s+search|who\s+won|"
    r"current\s+events|google|search\s+online|news\s+about|"
    r"celsius|fahrenheit|kilometers?|miles?|pounds?|kilograms?|"
    r"latest\s+news|breaking\s+news|news\s+about|headlines|news\s+headlines|"
    r"cricket\s+score|match\s+result|live\s+score|who\s+won\s+match|ipl|world\s+cup|test\s+match|odi|t20|"
    r"stock\s+price|crypto\s+price|bitcoin|ethereum|share\s+price|market\s+cap|nasdaq|nse|bse|"
    r"search\s+the\s+web|web\s+search|google\s+search|duckduckgo|search\s+for|find\s+information|"
    # Roles / positions
    r"who\s+is\s+(?:the\s+)?(?:current\s+|new\s+)?(?:president|prime\s*minister|captain|"
    r"leader|CEO|director|chancellor|governor|mayor|chief|head|chairman|secretary|"
    r"spokesperson|ambassador|manager|coach|winner|champion|incumbent|king|queen|emperor|ruler|"
    r"owner|founder|ceo|cto|coo|president\s*elect)|"
    r"who\s+was\s+(?:the\s+)?(?:president|prime\s*minister|captain|leader|king|queen|"
    r"CEO|director|manager|coach|winner|champion|owner|incumbent)|"
    r"(?:president|captain|prime\s*minister|PM|CEO|leader|king|queen|owner|"
    r"winner|champion|incumbent)\s+of\s+(?:the\s+)?[A-Za-z]\w+|"
    r"current\s+(?:president|captain|prime\s*minister|CEO|leader|king|queen|"
    r"manager|coach|winner|champion|owner|incumbent|mayor)|"
    r"who\s+(?:became|became\s+the|is\s+the\s+new|will\s+be\s+the\s+next)\s+"
    r"(?:president|prime\s*minister|captain|leader|CEO|manager|coach|champion)|"
    # Sports
    r"score|scores|result|results|fixture|match|matches|"
    r"tournament|championship|standings|points\s+table|leaderboard|"
    r"playoff|final|semi.?final|quarter.?final|"
    r"[A-Z]\w+\s+(?:vs|v/s|versus)\s+[A-Z]\w+|"
    r"who\s+won\s+(?:the\s+)?(?:match|game|series|ipl|world\s+cup|trophy|championship|final)|"
    r"ipl\s+\d{4}|world\s+cup\s+\d{4}|"
    # Finance
    r"stock\s+price|share\s+price|crypto\s+price|bitcoin|ethereum|"
    r"solana|dogecoin|ripple|cryptocurrency|"
    r"market\s+cap|nifty|sensex|dow\s+jones|nasdaq|s&p\s+500|"
    r"stock\s+market|bullion|gold\s+price|silver\s+price|ipo|"
    r"\b[A-Z]{2,5}\s+stock\b|price\s+of\s+(?:bitcoin|ethereum|gold|silver|oil)|"
    # Prices / costs
    r"price\s+of|cost\s+of|how\s+much\s+(?:is|does|are|were)|"
    r"what\s+(?:is|are)\s+the\s+(?:current|latest)\s+(?:price|rate|cost)|"
    # Statistics / data
    r"population\s+of|GDP\s+of|gdp\s+of|inflation\s+rate|"
    r"unemployment\s+rate|interest\s+rate|"
    r"what\s+(?:is|are)\s+the\s+(?:current|latest)\s+(?:population|gdp|inflation|unemployment)|"
    # Time-sensitive (current / latest / recent / today)
    r"current\s+(?:population|gdp|inflation|unemployment|weather|temperature|"
    r"time|date|status|situation|president|captain|CEO|leader|"
    r"price|rate|value|score|result|news|events|market|stock|share|index)|"
    r"latest\s+(?:news|update|updates|information|data|figures|stats|"
    r"technology|tech|model|version|release|edition|"
    r"price|prices|rate|rates|score|scores|result|results|"
    r"movie|film|trend|trends|developments|report|reports|research|findings)|"
    r"recent\s+(?:news|events|developments|updates|changes|"
    r"releases|announcements|reports|studies|"
    r"price|rate|score|result|match|election)|"
    r"today'?s\s+(?:news|weather|date|headlines|"
    r"result|score|match|price|rate|exchange\s+rate|"
    r"stock|market|cricket|football|sports)|"
    r"what\s+(?:happened|occurred|took\s+place)\s+(?:today|yesterday|this\s+week|this\s+month|"
    r"this\s+year|recently|lately)|"
    r"this\s+(?:week|month|quarter|year)'?s?\s+(?:news|update|result|election|report|sales|earnings)|"
    # Year markers
    r"(?:20[2-9][4-9]|20[3-9][0-9])\s+(?:election|result|winner|"
    r"president|captain|champion|championship|olympics|"
    r"world\s+cup|t20|tournament|budget|GDP|census|"
    r"price|rate|sales|revenue|model|version|release)|"
    # Entertainment
    r"box\s+office|highest\s+grossing|ratings|viewership|trp|"
    r"oscar|grammy|emmy|tony|golden\s+globe|"
    r"most\s+watched|most\s+popular|trending|viral|"
    # Technology
    r"newly\s+released|newly\s+launched|just\s+released|just\s+launched|"
    r"latest\s+(?:version|update|release|model|edition|os|android|ios|iphone|samsung|pixel|windows|macos)|"
    r"upcoming\s+(?:phone|model|device|version|release|launch|event)|"
    # Geo / place facts
    r"capital\s+of|area\s+of|largest\s+city\s+in|"
    r"official\s+language\s+of|currency\s+of|"
    r"what\s+is\s+the\s+(?:capital|population|area|currency|language)\s+of|"
    # General catch-all
    r"what\s+(?:is|are)\s+the\s+(?:current|latest|new|recent)\s+\w+|"
    r"who\s+(?:is|are)\s+the\s+(?:current|latest|new|recent)\s+\w+|"
    r"(?:what|who)\s+(?:is|are)\s+the\s+(?:latest|newest|most\s+recent)|"
    r"tell\s+me\s+(?:about|the)\s+(?:current|latest|recent)\s+\w+)\b",
    re.IGNORECASE,
)

_KNOWLEDGE_BASE_INTENT = re.compile(
    r"\b(what\s+is|who\s+is|when\s+was|where\s+is|why\s+is|how\s+does|"
    r"explain|describe|define|tell\s+me\s+about|history\s+of|"
    r"advantages\s+of|disadvantages\s+of|benefits\s+of|compare|"
    r"difference\s+between)\b",
    re.IGNORECASE,
)

_OPINION_PATTERNS = re.compile(
    r"\b(what\s+do\s+you\s+think|your\s+opinion|do\s+you\s+like|"
    r"recommend|suggest|advice|should\s+i|best\s+way\s+to)\b",
    re.IGNORECASE,
)


_TECHNICAL_VOCAB: Set[str] = {
    "fastapi", "python", "pydantic", "starlette", "uvicorn", "langchain", "langgraph",
    "stategraph", "postgresql", "postgres", "neo4j", "cypher", "groq", "asyncio",
    "sqlalchemy", "pytest", "redis", "pinecone", "docker", "kubernetes",
    "dependency injection", "mvcc", "concurrency", "rrf", "reciprocal rank fusion",
    "bm25", "rag", "graphrag", "embedding", "vector", "hybrid", "chunking",
    "async", "await", "coroutine", "type hint", "endpoint", "middleware",
    "session", "transaction", "crud", "orm", "schema", "migration",
    "jwt", "oauth", "rest api", "graphql", "websocket", "sse",
    "nextjs", "react", "typescript", "tailwind", "zustand",
    "machine learning", "deep learning", "neural network", "transformer", "llm",
    "rag", "vector", "embedding", "tokenizer", "prompt engineering",
}


class IntelligentRouter:
    """
    (`2️⃣ router.py`)
    The central decision engine for LangGraph Orchestration.
    Analyzes query intent, extracts domain keywords, and emits a clean
    `RouterDecision` and `IntentResult`. Does NOT call the LLM directly.
    """

    def __init__(self):
        pass

    def _feature_enabled(self, flag_name: str) -> bool:
        """Helper to safely read feature flags from settings."""
        try:
            flags = getattr(settings, "feature_flags", None)
            if flags is None:
                return True
            attr = {
                "memory": "enable_memory",
                "graph": "enable_graph",
                "tools": "enable_tools",
                "hybrid_rag": "enable_hybrid_rag",
            }.get(flag_name, flag_name)
            return bool(getattr(flags, attr, True))
        except Exception:
            return True

    def _extract_keywords(self, query: str) -> List[str]:
        """Extracts technical terms and normalized domain keywords from the user prompt."""
        lower_query = query.lower()
        found: Set[str] = set()

        for term in _TECHNICAL_VOCAB:
            if re.search(rf"\b{re.escape(term)}\b", lower_query):
                found.add(term)

        ignore_words = {
            "The", "This", "When", "If", "For", "With", "And", "Or", "Using",
            "How", "What", "Why", "Where", "Can", "Could", "Should", "Tell",
            "Hello", "Hi", "Hey", "Greetings", "Thanks", "Thank", "Good",
            "Morning", "Afternoon", "Evening", "There", "Who", "Are", "You",
            "Does", "Do", "Did", "Are", "Was", "Were", "Is",
        }
        for match in re.findall(r"\b([A-Z][a-zA-Z0-9_]{2,25})\b", query):
            if match not in ignore_words and match.lower() not in ignore_words:
                found.add(match)

        return sorted(list(found))

    def analyze_intent(self, user_query: str) -> IntentResult:
        """Classifies user query into IntentType and extracts domain keywords."""
        clean_query = user_query.strip()
        keywords = self._extract_keywords(clean_query)
        lower = clean_query.lower()

        # 1. Pure greeting / pleasantry with no technical load
        if (_GREETING_PATTERNS.match(clean_query)
                and not any(k.lower() in _TECHNICAL_VOCAB for k in keywords)
                and not _TOOL_PATTERNS.search(clean_query)
                and not _KNOWLEDGE_BASE_INTENT.search(clean_query)):
            return IntentResult(
                intent=IntentType.GREETING,
                confidence=0.99,
                keywords=keywords,
                reasoning="Matched standard conversational greeting without technical terms.",
            )

        has_rel = bool(_RELATIONSHIP_PATTERNS.search(clean_query))
        has_exp = bool(_EXPLANATION_PATTERNS.search(clean_query))
        has_personal = bool(_PERSONAL_PATTERNS.search(clean_query))
        has_tool = bool(_TOOL_PATTERNS.search(clean_query))
        has_kb = bool(_KNOWLEDGE_BASE_INTENT.search(clean_query))
        has_opinion = bool(_OPINION_PATTERNS.search(clean_query))

        # 2. Personalized memory-driven queries
        if has_personal:
            return IntentResult(
                intent=IntentType.MEMORY_RECALL,
                confidence=0.96,
                keywords=keywords,
                reasoning="Query references user history, preferences, or previously shared facts. "
                          "Routing to long-term memory for personalization.",
            )

        # 3. Real-time tool-driven queries (weather/calc/translate/etc.)
        if has_tool:
            return IntentResult(
                intent=IntentType.TOOL_QUERY,
                confidence=0.95,
                keywords=keywords,
                reasoning="Query requires live data, computation, or translation. Routing to tool pipeline.",
            )

        # 4. Mixed reasoning: explanation + structural relationship
        if has_rel and (has_exp or len(keywords) >= 2):
            return IntentResult(
                intent=IntentType.MIXED_REASONING,
                confidence=0.97,
                keywords=keywords,
                reasoning="Query requests both comprehensive technical explanation and "
                          "structural graph relationships.",
            )

        # 5. Structural / relationship queries
        if has_rel and not clean_query.lower().startswith(("what is", "explain ")):
            return IntentResult(
                intent=IntentType.RELATIONSHIP_QUERY,
                confidence=0.96,
                keywords=keywords,
                reasoning="Query explicitly focuses on connections, dependencies, "
                          "or relationship traversals between entities.",
            )

        # 6. General technical / knowledge-base explanation
        if has_exp or has_kb or len(keywords) > 0:
            return IntentResult(
                intent=IntentType.TECHNICAL_DOCS,
                confidence=0.95,
                keywords=keywords,
                reasoning="Query requests technical documentation, conceptual definition, "
                          "or how-to explanation.",
            )

        # 7. Opinion / recommendation (no retrieval needed - direct to Groq with memory context)
        if has_opinion:
            return IntentResult(
                intent=IntentType.OPINION_QUERY,
                confidence=0.92,
                keywords=keywords,
                reasoning="Query asks for opinion/recommendation. Will use LLM with optional memory context.",
            )

        # 8. Default
        return IntentResult(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.90,
            keywords=keywords,
            reasoning="Query does not match specific technical or relational retrieval triggers.",
        )

    def route_query(
        self, user_query: str, intent_result: Optional[IntentResult] = None
    ) -> RouterDecision:
        """Determines RouteType + execution dependencies based on intent classification."""
        intent = intent_result or self.analyze_intent(user_query)
        memory_on = self._feature_enabled("memory")
        graph_on = self._feature_enabled("graph")
        tools_on = self._feature_enabled("tools")
        rag_on = self._feature_enabled("hybrid_rag")

        # ----- Greeting / general chat: LLM + optional memory personalization -----
        if intent.intent in (IntentType.GREETING, IntentType.GENERAL_CHAT, IntentType.OPINION_QUERY):
            return RouterDecision(
                route=RouteType.MEMORY_ENHANCED if memory_on else RouteType.DIRECT_LLM,
                confidence=intent.confidence,
                requires_rag=False,
                requires_graph=False,
                requires_memory=memory_on,
                requires_tools=False,
                reasoning=f"Classified as {intent.intent.value}; routing to LLM "
                          f"with{'out' if not memory_on else ''} memory personalization.",
            )

        # ----- Memory recall: LLM + memory (no RAG/Graph/Tools) -----
        if intent.intent == IntentType.MEMORY_RECALL:
            return RouterDecision(
                route=RouteType.MEMORY_ENHANCED,
                confidence=intent.confidence,
                requires_rag=False,
                requires_graph=False,
                requires_memory=memory_on,
                requires_tools=False,
                reasoning="Classified as MEMORY_RECALL; prioritizing long-term memory for personalization.",
            )

        # ----- Live tool query: LLM + tools (calculator/weather/etc.) -----
        if intent.intent == IntentType.TOOL_QUERY:
            return RouterDecision(
                route=RouteType.TOOLS_ENHANCED,
                confidence=intent.confidence,
                requires_rag=False,
                requires_graph=False,
                requires_memory=memory_on,
                requires_tools=tools_on,
                reasoning="Classified as TOOL_QUERY; routing to tool pipeline for real-time computation/data.",
            )

        # ----- Relationship: LLM + GraphRAG (Neo4j) -----
        if intent.intent == IntentType.RELATIONSHIP_QUERY:
            return RouterDecision(
                route=RouteType.GRAPH_RAG,
                confidence=intent.confidence,
                requires_rag=False,
                requires_graph=graph_on,
                requires_memory=memory_on,
                requires_tools=False,
                reasoning="Classified as RELATIONSHIP_QUERY; routing to Knowledge Graph for structural traversal.",
            )

        # ----- Mixed reasoning: RAG + Graph + Memory + Tools (full synthesis) -----
        if intent.intent == IntentType.MIXED_REASONING:
            return RouterDecision(
                route=RouteType.HYBRID_SYNTHESIS,
                confidence=intent.confidence,
                requires_rag=rag_on,
                requires_graph=graph_on,
                requires_memory=memory_on,
                requires_tools=tools_on,
                reasoning="Classified as MIXED_REASONING; executing RAG + Graph + Memory + Tools.",
            )

        # ----- Technical docs: RAG + Memory + Tools (best-effort full retrieval) -----
        return RouterDecision(
            route=RouteType.HYBRID_RAG,
            confidence=intent.confidence,
            requires_rag=rag_on,
            requires_graph=False,
            requires_memory=memory_on,
            requires_tools=tools_on,
            reasoning="Classified as TECHNICAL_DOCS; routing to Hybrid RAG with memory + tool enrichment.",
        )


intelligent_router = IntelligentRouter()
