# File: app/ai/llm/mock_provider.py
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from app.ai.llm.base import BaseLLMProvider

logger = logging.getLogger("app.ai.llm.mock_provider")


class MockLLMProvider(BaseLLMProvider):
    """
    (`⭐ One More Improvement`: Mock Provider for Testing)
    Deterministic simulation provider for running automated tests, offline local development,
    and fallback validation without consuming external API credits or requiring network reachability.
    """
    def __init__(self):
        super().__init__(provider_name="mock")
        self._is_initialized = False

    async def initialize(self) -> bool:
        self._is_initialized = True
        logger.info("MockLLMProvider initialized.")
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {
            "healthy": True,
            "status": "online",
            "provider": "mock",
            "message": "Mock LLM provider ready for offline generation & testing",
        }

    async def generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Simulate slight async processing delay
        await asyncio.sleep(0.05)

        prompt_text = (
            messages[-1].get("content", "") if isinstance(messages, list) and messages
            else str(messages)
        ).strip()
        
        q_lower = prompt_text.lower()
        if any(w in q_lower for w in ["hello", "hi", "hey", "greetings", "good morning", "good evening"]):
            simulated_response = "Hello! I'm ready to assist you. What can we explore or solve together today?"
        elif any(w in q_lower for w in ["who are you", "what are you"]):
            simulated_response = "I am Antigravity, an intelligent AI coding and reasoning assistant created by Anvesh Mishra. How can I help you today?"
        else:
            simulated_response = f"I have analyzed your query: '{prompt_text}'. Based on our current context, I'm ready to provide detailed insights, code generation, or multi-hop reasoning as needed. What specific aspect would you like to dive into next?"

        return {
            "content": simulated_response,
            "model": model or "llama-3.3-70b-versatile",
            "usage": {
                "prompt_tokens": max(10, len(prompt_text) // 4),
                "completion_tokens": max(15, len(simulated_response) // 4),
                "total_tokens": max(25, (len(prompt_text) + len(simulated_response)) // 4),
            },
            "raw": {"status": "mocked", "messages": messages},
        }

    async def close(self) -> None:
        self._is_initialized = False
        logger.info("MockLLMProvider closed.")
