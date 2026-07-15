# File: app/ai/llm/parser.py
import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger("app.ai.llm.parser")


class LLMResponseParser:
    """
    Helps parse, clean, and validate raw LLM string completions into structured JSON/Pydantic schemas.
    """

    @staticmethod
    def extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON payload from markdown code blocks or plain JSON strings."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1).rstrip("`").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "", 1).rstrip("`").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to decode JSON from LLM response ({exc}): '{raw_text[:200]}...'")
            return None

    @staticmethod
    def parse_to_model(raw_text: str, schema: type[BaseModel]) -> Optional[BaseModel]:
        """Parses LLM output directly into a Pydantic schema."""
        payload = LLMResponseParser.extract_json(raw_text)
        if not payload:
            return None
        try:
            return schema.model_validate(payload)
        except Exception as exc:
            logger.error(f"Failed to validate LLM output against schema '{schema.__name__}': {exc}")
            return None
