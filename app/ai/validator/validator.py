# File: app/ai/validator/validator.py
"""
(`Guardrails: Main Validator Orchestrator`)
Coordinates input safety validation and output content filtering.
Applies guardrails before LLM processing and before response delivery.
"""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from app.ai.validator.safety import InputSafetyValidator, input_safety_validator, SafetyValidationResult
from app.ai.validator.content_filter import OutputContentFilter, output_content_filter, ContentFilterResult

logger = logging.getLogger("app.ai.validator")

GUARDRAIL_DISABLED_RESPONSE = (
    "I apologize, but I'm unable to process this request. "
    "It appears to contain content that violates our safety guidelines. "
    "Please rephrase your query and try again."
)


@dataclass
class GuardrailCheckResult:
    passed: bool
    sanitized_input: Optional[str] = None
    filtered_output: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[dict] = None


class GuardrailValidator:
    """
    Main guardrail orchestrator that validates both inputs and outputs.
    Use this before sending to LLM and before returning responses.
    """

    def __init__(
        self,
        input_validator: Optional[InputSafetyValidator] = None,
        output_filter: Optional[OutputContentFilter] = None,
    ):
        self.input_validator = input_validator or input_safety_validator
        self.output_filter = output_filter or output_content_filter

    def validate_input(self, query: str) -> GuardrailCheckResult:
        """
        Validates user input against safety guardrails.
        Returns sanitized query if validation passes.
        """
        result = self.input_validator.validate(query)

        if result.is_safe:
            return GuardrailCheckResult(
                passed=True,
                sanitized_input=result.sanitized_query,
                details={"patterns_found": result.detected_patterns}
            )
        else:
            return GuardrailCheckResult(
                passed=False,
                reason=result.reason,
                details={"patterns_found": result.detected_patterns}
            )

    def validate_output(self, content: str) -> GuardrailCheckResult:
        """
        Validates LLM output against content safety rules.
        Returns filtered content if validation passes.
        """
        result = self.output_filter.validate(content)

        if result.is_appropriate:
            return GuardrailCheckResult(
                passed=True,
                filtered_output=result.filtered_content,
                details={"issues_found": result.detected_issues}
            )
        else:
            return GuardrailCheckResult(
                passed=False,
                filtered_output=result.filtered_content or GUARDRAIL_DISABLED_RESPONSE,
                reason=result.reason,
                details={"issues_found": result.detected_issues}
            )

    def validate_pair(self, query: str, response: str) -> Tuple[GuardrailCheckResult, GuardrailCheckResult]:
        """
        Validates both input and output in one call.
        Returns (input_result, output_result).
        """
        input_result = self.validate_input(query)
        output_result = self.validate_output(response)
        return input_result, output_result


guardrail_validator = GuardrailValidator()