# File: app/ai/validator/safety.py
"""
(`Guardrails: Input Safety Validation`)
Sanitizes and validates user inputs against prompt injection, harmful content,
and malformed requests before they reach the LLM or RAG pipeline.
"""
import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("app.ai.validator.safety")

INJECTION_PATTERNS = [
    r"(?i)^(ignore|disregard|forget)\s+(all|previous|your)\s+(instructions?|rules?|constraints?)",
    r"(?i)^(ignore|disregard|forget)\s+all\s+(previous|your)\s+(instructions?|rules?|constraints?)",
    r"(?i)^(ignore|disregard)\s+all\s+(instructions?)",
    r"(?i)you\s+are\s+now\s+a\s+",
    r"(?i)(system|prompt)\s*[:\-]",
    r"(?i)<\|(?:system|user|assistant)\|>",
    r"(?i)(new\s+instructions?|override)",
    r"(?i)(role\s*=\s*|pretend\s+you\s+are\s+)",
]

HARMFUL_CONTENT_PATTERNS = [
    r"(?i)\b(hack|exploit|attack)\s+(a\s+)?.*?(system|server|database|network|website)\b",
    r"(?i)\b(steal|phish|spam)\b",
    r"(?i)\b(create|make|build)\s+(virus|malware|ransomware|trojan)\b",
    r"(?i)\b(swat|dox|harass)\s+(someone|a\s+person)\b",
]

PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL"),
]

MAX_QUERY_LENGTH = 8192
MAX_TOKENS_ESTIMATE = MAX_QUERY_LENGTH // 4


@dataclass
class SafetyValidationResult:
    is_safe: bool
    reason: Optional[str] = None
    sanitized_query: Optional[str] = None
    detected_patterns: Optional[List[str]] = None


class InputSafetyValidator:
    """
    Validates and sanitizes user inputs before they reach the AI pipeline.
    Detects:
    - Prompt injection attempts
    - Harmful content
    - PII in inputs
    - Oversized payloads
    """

    def __init__(self, block_injection: bool = True, block_harmful: bool = True, block_pii: bool = False):
        self.block_injection = block_injection
        self.block_harmful = block_harmful
        self.block_pii = block_pii

    def validate(self, query: str) -> SafetyValidationResult:
        """
        Validates a user query for safety concerns.
        Returns SafetyValidationResult with is_safe=True if clean, or details on violation.
        """
        if not query or not query.strip():
            return SafetyValidationResult(
                is_safe=False,
                reason="Empty query received"
            )

        cleaned = query.strip()
        detected = []

        if len(cleaned) > MAX_QUERY_LENGTH:
            return SafetyValidationResult(
                is_safe=False,
                reason=f"Query exceeds maximum length ({MAX_QUERY_LENGTH} chars)"
            )

        cleaned = self._sanitize_special_chars(cleaned)
        cleaned = self._normalize_whitespace(cleaned)

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, cleaned):
                detected.append(f"INJECTION_PATTERN:{pattern}")
                if self.block_injection:
                    logger.warning(f"Prompt injection detected: {pattern}")
                    return SafetyValidationResult(
                        is_safe=False,
                        reason="Potential prompt injection detected",
                        sanitized_query=cleaned,
                        detected_patterns=detected
                    )

        for pattern in HARMFUL_CONTENT_PATTERNS:
            if re.search(pattern, cleaned):
                detected.append(f"HARMFUL_PATTERN:{pattern}")
                if self.block_harmful:
                    logger.warning(f"Potentially harmful content detected: {pattern}")
                    return SafetyValidationResult(
                        is_safe=False,
                        reason="Content violates safety policy",
                        sanitized_query=cleaned,
                        detected_patterns=detected
                    )

        if self.block_pii:
            pii_found = []
            for pattern, pii_type in PII_PATTERNS:
                matches = re.findall(pattern, cleaned)
                if matches:
                    pii_found.append(f"{pii_type}:{len(matches)}")
                    cleaned = re.sub(pattern, f"[{pii_type}_REDACTED]", cleaned)
            if pii_found:
                detected.extend(pii_found)
                logger.info(f"PII detected and redacted: {pii_found}")

        return SafetyValidationResult(
            is_safe=True,
            sanitized_query=cleaned,
            detected_patterns=detected if detected else None
        )

    def _sanitize_special_chars(self, text: str) -> str:
        """Remove null bytes and other control characters."""
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize multiple whitespace to single space."""
        return " ".join(text.split())


input_safety_validator = InputSafetyValidator()