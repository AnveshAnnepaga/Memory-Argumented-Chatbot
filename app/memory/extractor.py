# File: app/memory/extractor.py
"""
(`Milestone 12 Long-Term Memory Extractor`)
The intelligence engine responsible for analyzing user conversation turns (`user_query`, `ai_response`)
and deciding what information must be remembered, updated, or ignored.
Applies deterministic semantic pattern extraction combined with structured Groq LLM JSON reasoning.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional
from app.ai.llm.llm_manager import llm_manager
from app.memory.schemas import (
    MemoryAction,
    MemoryExtractionItem,
    MemoryExtractionResult,
    MemoryType,
    SemanticMemory,
    UserProfile,
)

logger = logging.getLogger("app.memory.extractor")


class MemoryExtractor:
    """
    (`2. Memory Extractor Intelligence`)
    Decides whether incoming message turns contain valuable, enduring facts, events, or profile data.
    Ensures transient noise (`Thank you`, `Hello`, `Got it`) is explicitly ignored (`should_remember=False`).
    """

    def __init__(self):
        self._compiled_patterns = [
            # Profile Name
            (
                re.compile(r"(?:my name is|i am|call me)\s+([A-Z][a-z0-9_ -]{1,40})", re.IGNORECASE),
                MemoryType.PROFILE,
                "name",
                0.98,
                0.90,
                "Explicit user name declaration",
            ),
            # Location / City from "from [city]" or "i am from [city]" or "i live in [city]"
            (
                re.compile(r"(?:i am from|i live in|i'm from|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE),
                MemoryType.PROFILE,
                "location",
                0.95,
                0.85,
                "User location declaration",
            ),
            # Education / Degree - "pursuing B.Tech in Data Science" or "studying B.Tech in Data Science" or "doing B.Tech in Data Science"
            (
                re.compile(r"(?:pursuing|studying|doing|enrolled in)\s+([A-Za-z0-9\.]+\s*(?:in|of)\s+[A-Za-z0-9\s&]+)", re.IGNORECASE),
                MemoryType.PROFILE,
                "education",
                0.96,
                0.90,
                "User education/degree declaration",
            ),
            # CGPA - "cgpa of 8.76" or "cgpa is 8.76" or "cgpa 8.76"
            (
                re.compile(r"(?:cgpa|gpa)\s*(?:of|is|:)?\s*([0-9]\.[0-9]{1,2})", re.IGNORECASE),
                MemoryType.PROFILE,
                "cgpa",
                0.97,
                0.90,
                "User CGPA declaration",
            ),
            # Field of study from "in Data Science" or "in Computer Science" - more flexible
            (
                re.compile(r"(?:in|majoring in|specializing in)\s+([A-Za-z0-9\s&]+(?:\s+Science|\s+Engineering|\s+Technology|\s+Mathematics|\s+Arts|\s+Commerce|\s+Business|\s+Management|\s+Analytics|\s+Data\s+Science|\s+AI|\s+ML|\s+Computer\s+Science))", re.IGNORECASE),
                MemoryType.PROFILE,
                "field_of_study",
                0.93,
                0.85,
                "User field of study declaration",
            ),
            # College/University name - "at XYZ College" or "from XYZ University"
            (
                re.compile(r"(?:at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:College|University|Institute|Institute\s+of\s+Technology)))", re.IGNORECASE),
                MemoryType.PROFILE,
                "college",
                0.92,
                0.85,
                "User college/university declaration",
            ),
            # Preferred Language / Stack update or preference
            (
                re.compile(r"(?:i prefer|my preferred language is|i love|i use)\s+([A-Za-z0-9_+#-]{2,30})", re.IGNORECASE),
                MemoryType.SEMANTIC,
                "preferred_language",
                0.96,
                0.85,
                "Explicit technology/language preference",
            ),
            (
                re.compile(r"(?:i mostly work with|i switched to|i now use)\s+([A-Za-z0-9_+#-]{2,30})", re.IGNORECASE),
                MemoryType.SEMANTIC,
                "preferred_language",
                0.97,
                0.90,
                "Updated technical language stack override",
            ),
            # Occupation / Role
            (
                re.compile(r"(?:i work as a|i am a|my job is|i'm a)\s+([A-Za-z0-9_ -]{3,50})", re.IGNORECASE),
                MemoryType.PROFILE,
                "occupation",
                0.96,
                0.85,
                "Explicit professional role declaration",
            ),
            # Episodic Milestone / Deployment
            (
                re.compile(r"(?:i completed|we completed|finished|just finished)\s+(milestone\s*\d+|project\s+[a-z0-9_-]+|task)", re.IGNORECASE),
                MemoryType.EPISODIC,
                "milestone",
                0.97,
                0.95,
                "Significant milestone completion event",
            ),
            (
                re.compile(r"(?:today i deployed|just deployed|deployed my|successfully deployed)\s*([a-z0-9_ -]*)", re.IGNORECASE),
                MemoryType.EPISODIC,
                "deployment",
                0.98,
                0.95,
                "Production deployment event",
            ),
            (
                re.compile(r"(?:i fixed|fixed a|resolved)\s+([a-z0-9_ -]+(?:bug|issue|error|crash))", re.IGNORECASE),
                MemoryType.EPISODIC,
                "bugfix",
                0.94,
                0.85,
                "Significant debugging/resolution event",
            ),
            (
                re.compile(r"(?:i changed|switched my)\s+([a-z0-9_ -]+(?:model|database|vector store|config))", re.IGNORECASE),
                MemoryType.EPISODIC,
                "config_change",
                0.95,
                0.85,
                "Architecture/model configuration change event",
            ),
        ]
        # Classification-driven ignore list: transient noise that adds no enduring value
        self._ignore_exact = {
            "thank you", "thanks", "ok", "okay", "hello", "hi", "hey",
            "got it", "cool", "yes", "no", "good morning", "bye", "nice",
            "great", "awesome", "wow", "lol", "haha", "sure", "fine",
        }
        # Low-importance greetings patterns (classification: small talk / greeting -> IGNORE)
        self._greeting_patterns = [
            re.compile(r"\b(?:hello|hi|hey|greetings|good morning|good evening|good afternoon)\b", re.IGNORECASE),
            re.compile(r"\b(?:how are you|how's it going|what's up|how do you do)\b", re.IGNORECASE),
            re.compile(r"\b(?:nice to meet you|pleasure|pleased)\b", re.IGNORECASE),
        ]

    async def extract(
        self,
        user_query: str,
        ai_response: Optional[str] = None,
        existing_profile: Optional[UserProfile] = None,
        existing_semantic: Optional[List[SemanticMemory]] = None,
    ) -> MemoryExtractionResult:
        """
        Analyzes the turn and returns structured items to store or update.
        First executes high-precision semantic regex rules, falling back to Groq LLM extraction if needed.
        """
        clean_q = user_query.strip()
        lower_q = clean_q.lower()

        # Step 1: Check instant rejection for filler/noise
        if lower_q in self._ignore_exact or len(clean_q) < 3:
            logger.debug(f"Query '{clean_q}' recognized as transient conversational filler. Ignoring.")
            return MemoryExtractionResult(should_remember=False, extracted_items=[], raw_llm_reasoning="Transient filler phrase ignored.")

        # Step 1b: Reject greeting/small talk (no enduring value)
        for gpat in self._greeting_patterns:
            if gpat.match(clean_q) and len(clean_q.split()) <= 6:
                logger.debug(f"Query '{clean_q}' classified as greeting/small talk. Ignoring.")
                return MemoryExtractionResult(should_remember=False, extracted_items=[], raw_llm_reasoning="Greeting/small talk ignored - no enduring memory value.")

        extracted_items: List[MemoryExtractionItem] = []

        # Step 2: Deterministic pattern matching
        for regex, mem_type, attr_key, conf, imp, reason in self._compiled_patterns:
            match = regex.search(clean_q)
            if match:
                val = match.group(1).strip().rstrip(".").title() if match.group(1) else "Project"
                if mem_type == MemoryType.PROFILE:
                    content_str = f"User {attr_key} is {val}"
                    action = MemoryAction.CREATE
                    if existing_profile and getattr(existing_profile, attr_key, None):
                        old_val = getattr(existing_profile, attr_key)
                        if old_val.lower() != val.lower():
                            action = MemoryAction.UPDATE
                            reason = f"Updating profile {attr_key} from '{old_val}' to '{val}'"
                elif mem_type == MemoryType.SEMANTIC:
                    content_str = f"User prefers {val}" if attr_key == "preferred_language" else f"User fact: {clean_q}"
                    action = MemoryAction.CREATE
                    if existing_semantic:
                        for s_fact in existing_semantic:
                            if attr_key in (s_fact.category, "preferred_language") and "prefer" in s_fact.fact.lower():
                                action = MemoryAction.UPDATE
                                reason = f"Updating existing semantic preference '{s_fact.fact}' to '{content_str}'"
                                break
                else:  # EPISODIC
                    if attr_key == "deployment" and not val:
                        content_str = "User deployed project"
                    elif attr_key == "deployment":
                        content_str = f"User deployed {val}" if "project" not in val.lower() else f"User deployed {val}"
                    else:
                        content_str = f"User {clean_q.rstrip('.')}"
                    action = MemoryAction.CREATE

                item = MemoryExtractionItem(
                    action=action,
                    memory_type=mem_type,
                    content=content_str,
                    key=attr_key,
                    value=val,
                    confidence=conf,
                    importance_score=imp,
                    reasoning=reason,
                )
                extracted_items.append(item)

        if extracted_items:
            logger.info(f"Extracted {len(extracted_items)} deterministic memory items from user turn.")
            return MemoryExtractionResult(should_remember=True, extracted_items=extracted_items, raw_llm_reasoning="Deterministic rule match.")

        # Step 3: LLM Structured JSON Extraction fallback for nuanced queries
        return await self._extract_via_llm(clean_q, ai_response, existing_profile, existing_semantic)

    async def _extract_via_llm(
        self,
        user_query: str,
        ai_response: Optional[str] = None,
        existing_profile: Optional[UserProfile] = None,
        existing_semantic: Optional[List[SemanticMemory]] = None,
    ) -> MemoryExtractionResult:
        """Invokes Groq LLM with strict JSON schema instructions to extract complex facts."""
        prompt = f"""You are Vyron AI's Long-Term Memory Intelligence Extractor.
Analyze the user's input and decide what enduring facts, events, or profile data should be stored.

USER INPUT: "{user_query}"
ASSISTANT RESPONSE: "{ai_response or ''}"

MEMORY CLASSIFICATION RULES:
| Type | Store? | Database |
|------|--------|----------|
| Greeting / Small Talk | IGNORE | None |
| Personal Preference (e.g. "I like Python") | STORE | PostgreSQL + Pinecone + Neo4j |
| User Goal (e.g. "I want to learn AI") | STORE | PostgreSQL + Pinecone + Neo4j |
| Technical Stack (e.g. "I use FastAPI") | STORE | PostgreSQL + Neo4j |
| Conversation Query/Response | STORE | MongoDB |
| Knowledge Chunks | STORE | PostgreSQL + Pinecone |
| User Relationships | STORE | Neo4j |
| Temporary Context | SESSION only | MongoDB |
| Retrieved Documents | REGENERATE | None |

Rules:
1. If the input is transient chat ("hello", "thanks", "how does asyncio work"), output `"should_remember": false`.
2. If the user states a permanent preference/fact ("I like Neo4j", "I use LangGraph"), extract as `SEMANTIC`.
3. If the user shares personal profile data ("I live in New York", "I am a Senior Engineer"), extract as `PROFILE`.
4. If the user shares a major accomplishment or event ("We launched v2 today"), extract as `EPISODIC`.
5. If the user mentions a goal or aspiration ("I want to become an AI engineer"), extract as `PROFILE` (category: goal).
6. If the user mentions a project ("I'm building VYRON", "working on a chatbot"), extract as `PROFILE` (category: project).
7. If updating a known fact, set `"action": "UPDATE"`. Otherwise `"CREATE"`.

Return EXACTLY valid JSON matching this schema:
{{
  "should_remember": boolean,
  "reasoning": string,
  "items": [
    {{
      "action": "CREATE" or "UPDATE" or "IGNORE",
      "memory_type": "SEMANTIC" or "EPISODIC" or "PROFILE",
      "content": "clear fact description",
      "key": "optional attribute name e.g. preferred_language or occupation",
      "value": "optional exact attribute value",
      "confidence": 0.95,
      "importance_score": 0.8
    }}
  ]
}}
"""
        try:
            full_prompt = f"System: You are a strict JSON data extractor. Output JSON only without code blocks.\n\nUser: {prompt}"
            resp = await llm_manager.generate(
                messages=full_prompt,
                max_tokens=400,
                temperature=0.1,
            )
            raw_res = resp.get("content", "") if isinstance(resp, dict) else str(resp)
            clean_json = raw_res.strip()
            if clean_json.startswith("[Mock Completion") or llm_manager.active_provider_key == "mock":
                item = MemoryExtractionItem(
                    action=MemoryAction.CREATE,
                    memory_type=MemoryType.SEMANTIC,
                    content=f"Nuanced fact: {prompt[:80]}",
                    key="nuanced_fact",
                    value=prompt[:50],
                    confidence=0.90,
                    importance_score=0.75,
                    reasoning="Mock LLM structured extraction",
                )
                return MemoryExtractionResult(should_remember=True, extracted_items=[item], raw_llm_reasoning="Mock mode JSON extraction")

            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            data = json.loads(clean_json)
            should_remember = bool(data.get("should_remember", False))
            raw_reasoning = str(data.get("reasoning", "LLM extraction"))
            raw_items = data.get("items", [])

            items: List[MemoryExtractionItem] = []
            if should_remember and isinstance(raw_items, list):
                for raw in raw_items:
                    act_str = raw.get("action", "CREATE").upper()
                    if act_str == "IGNORE":
                        continue
                    mtype_str = raw.get("memory_type", "SEMANTIC").upper()
                    items.append(
                        MemoryExtractionItem(
                            action=MemoryAction(act_str) if act_str in MemoryAction._value2member_map_ else MemoryAction.CREATE,
                            memory_type=MemoryType(mtype_str) if mtype_str in MemoryType._value2member_map_ else MemoryType.SEMANTIC,
                            content=str(raw.get("content", "")).strip(),
                            key=raw.get("key"),
                            value=raw.get("value"),
                            confidence=float(raw.get("confidence", 0.90)),
                            importance_score=float(raw.get("importance_score", 0.70)),
                            reasoning=raw_reasoning,
                        )
                    )

            return MemoryExtractionResult(
                should_remember=(len(items) > 0),
                extracted_items=items,
                raw_llm_reasoning=raw_reasoning,
            )
        except Exception as exc:
            logger.warning(f"Groq LLM memory extraction fallback failed: {exc}. Returning clean non-remembered state.")
            return MemoryExtractionResult(should_remember=False, extracted_items=[], raw_llm_reasoning=f"LLM Error: {exc}")
