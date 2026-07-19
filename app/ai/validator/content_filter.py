# File: app/ai/validator/content_filter.py
"""
(`Guardrails: Output Content Filtering`)
Validates and filters LLM outputs before returning to users.
Detects sensitive content, offensive material, and ensures response quality.
"""
import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("app.ai.validator.content_filter")

OFFENSIVE_PATTERNS = [
    (r"(?i)\b(slur|discriminate)\b", "DISCRIMINATION"),
    (r"(?i)\b(kill|murder|assassinate)\b", "VIOLENCE"),
    (r"(?i)\b(threaten|intimidate|extort)\b", "THREAT"),
]

SENSITIVE_CONTENT_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "EMAIL"),
    (r"\b(password|passwd|secret)\s*[:=]\s*\S+", "SECRET_CREDENTIAL"),
    (r"\b\d+\.\d+\.\d+\.\d+\b", "IP_ADDRESS"),
    (r"\b(?:api[_-]?key|token)\s*[:=]\s*\S+", "API_CREDENTIAL"),
]

MAX_RESPONSE_LENGTH = 8192
MIN_RESPONSE_LENGTH = 1


@dataclass
class ContentFilterResult:
    is_appropriate: bool
    filtered_content: Optional[str] = None
    reason: Optional[str] = None
    detected_issues: Optional[List[str]] = None


class OutputContentFilter:
    """
    Filters and validates LLM outputs before returning to users.
    - Detects offensive content
    - Redacts sensitive information (PII, credentials)
    - Enforces length bounds
    - Masks sensitive system prompts if leaked
    """

    def __init__(
        self,
        block_offensive: bool = True,
        redact_pii: bool = True,
        max_length: int = MAX_RESPONSE_LENGTH,
    ):
        self.block_offensive = block_offensive
        self.redact_pii = redact_pii
        self.max_length = max_length

    def validate(self, content: str) -> ContentFilterResult:
        """Validates and potentially filters LLM output content."""
        if not content:
            return ContentFilterResult(
                is_appropriate=False,
                reason="Empty response from LLM"
            )

        filtered = content
        detected_issues: List[str] = []

        if len(filtered) > self.max_length:
            return ContentFilterResult(
                is_appropriate=False,
                reason=f"Response exceeds maximum length ({self.max_length} chars)"
            )

        if len(filtered) < MIN_RESPONSE_LENGTH:
            return ContentFilterResult(
                is_appropriate=False,
                reason="Response too short"
            )

        for pattern, category in OFFENSIVE_PATTERNS:
            if re.search(pattern, filtered):
                detected_issues.append(f"OFFENSIVE:{category}")
                if self.block_offensive:
                    logger.warning(f"Offensive content detected in LLM output: {category}")
                    return ContentFilterResult(
                        is_appropriate=False,
                        filtered_content=filtered,
                        reason=f"Content violates safety policy: {category}",
                        detected_issues=detected_issues
                    )

        if self.redact_pii:
            for pattern, pii_type in SENSITIVE_CONTENT_PATTERNS:
                matches = re.findall(pattern, filtered)
                if matches:
                    detected_issues.append(f"SENSITIVE:{pii_type}:{len(matches)}")
                    filtered = re.sub(pattern, f"[{pii_type}_REDACTED]", filtered)
                    logger.info(f"Redacted {len(matches)} instances of {pii_type} from output")

        filtered = self._filter_system_leakage(filtered)

        return ContentFilterResult(
            is_appropriate=True,
            filtered_content=filtered,
            detected_issues=detected_issues if detected_issues else None
        )

    def _filter_system_leakage(self, content: str) -> str:
        """Mask any leaked system prompts or internal instructions."""
        system_patterns = [
            r"(?i)system\s*prompt\s*[:\-].*?(?=\n|$)",
            r"(?i)you\s+are\s+a\s+.*?(?=\n|$)",
            r"<\|system\|>.*?<\|",
            r"\[INST\].*?\[/INST\]",
        ]
        filtered = content
        for pattern in system_patterns:
            filtered = re.sub(pattern, "[GENERATED CONTENT]", filtered, flags=re.IGNORECASE | re.DOTALL)
        return filtered


output_content_filter = OutputContentFilter()