# File: app/ai/llm/groq_client.py
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import httpx
from groq import AsyncGroq
from app.ai.llm.base import BaseLLMProvider
from app.core.config import settings
from app.core.exceptions import GroqException
from app.core.retry import execute_with_retry

logger = logging.getLogger("app.ai.llm.groq_client")


class GroqProvider(BaseLLMProvider):
    """
    (`6.5 Groq Manager ⭐`)
    Primary LLM provider implementation wrapping the official Groq Python SDK (`AsyncGroq`).
    Provides model registry integration, automatic fallback switching, retry logic,
    timeout handling, and API health diagnostics.
    """
    def __init__(self):
        super().__init__(provider_name="groq")
        self.client: AsyncGroq | None = None
        self.stub_mode: bool = False

    @execute_with_retry(max_attempts=1, min_wait=0.2, max_wait=0.5, exceptions=(Exception,))
    async def _ping_api(self) -> Dict[str, Any]:
        if not self.client:
            return {}
        # Fetching model list acts as an official API reachability and key validation check
        response = await asyncio.wait_for(self.client.models.list(), timeout=2.5)
        models = [m.id for m in getattr(response, "data", [])]
        return {"models_count": len(models), "sample_models": models[:5]}

    async def initialize(self) -> bool:
        """(`6.5 Groq Manager`: API Key Validation & Client Initialization)"""
        api_key = getattr(settings, "GROQ_API_KEY", getattr(settings.ai.groq, "api_key", ""))
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY missing or placeholder. GroqProvider entering stub/fallback mode.")
            self._is_initialized = True
            self.stub_mode = True
            return False

        try:
            timeout_val = getattr(settings.ai.groq, "timeout_seconds", 30)
            self.client = AsyncGroq(
                api_key=api_key,
                timeout=timeout_val,
                http_client=httpx.AsyncClient(timeout=timeout_val),
            )
            stats = await self._ping_api()
            self._is_initialized = True
            self.stub_mode = False
            logger.info(
                f"Groq API Client verified successfully [Primary Model: '{settings.ai.models.chat_model}' | Available Models: {stats.get('models_count', 0)}]."
            )
            return True
        except Exception as exc:
            logger.warning(
                f"Groq API verification failed during startup ({exc}). Entering offline/stub mode."
            )
            self._is_initialized = True
            self.stub_mode = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Diagnoses Groq API reachability and key status."""
        if self.stub_mode or not self.client:
            return {
                "healthy": False,
                "status": "stubbed_local_dev",
                "message": "Groq API not connected (placeholder API key configured)",
                "primary_model": settings.ai.models.chat_model,
                "fallback_model": settings.ai.models.fallback_model,
            }
        try:
            stats = await self._ping_api()
            return {
                "healthy": True,
                "status": "online",
                "primary_model": settings.ai.models.chat_model,
                "fallback_model": settings.ai.models.fallback_model,
                "details": stats,
            }
        except Exception as exc:
            return {"healthy": False, "status": "error", "error": str(exc)}

    @execute_with_retry(max_attempts=3, min_wait=1.0, max_wait=5.0, exceptions=(Exception,))
    async def generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        (`6.5 Groq Manager`: Request Management, Retry Logic & Model Fallback)
        Executes a chat completion using the primary model (`llama-3.3-70b-versatile`).
        If a rate limit or execution error occurs, attempts fallback (`llama-3.1-8b-instant`).
        """
        if self.stub_mode or not self.client:
            raise GroqException("GroqProvider is in offline/stub mode. Cannot generate completion without a valid API key.")

        formatted_messages = (
            [{"role": "user", "content": messages}] if isinstance(messages, str) else messages
        )
        target_model = model or settings.ai.models.chat_model
        temp = temperature if temperature is not None else settings.ai.groq.temperature
        tokens = max_tokens if max_tokens is not None else settings.ai.groq.max_tokens

        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=formatted_messages,
                temperature=temp,
                max_tokens=tokens,
                timeout=timeout or settings.ai.groq.timeout_seconds,
                **kwargs,
            )
            choice = response.choices[0] if response.choices else None
            content = choice.message.content if choice and choice.message else ""
            tool_calls = None
            if choice and choice.message and getattr(choice.message, "tool_calls", None):
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
            usage = (
                response.usage.model_dump() if hasattr(response, "usage") and hasattr(response.usage, "model_dump")
                else dict(response.usage) if hasattr(response, "usage") and response.usage else {}
            )
            return {
                "content": content,
                "model": response.model,
                "usage": usage,
                "tool_calls": tool_calls,
                "raw": response,
            }
        except Exception as primary_exc:
            # Fallback switching logic (`6.5 Groq Manager`: Fallback Model `llama-3.1-8b-instant`)
            fallback_model = settings.ai.models.fallback_model
            if target_model != fallback_model:
                logger.warning(
                    f"Primary model '{target_model}' failed ({primary_exc}). Automatically switching to fallback model '{fallback_model}'..."
                )
                try:
                    response = await self.client.chat.completions.create(
                        model=fallback_model,
                        messages=formatted_messages,
                        temperature=temp,
                        max_tokens=tokens,
                        timeout=timeout or settings.ai.groq.timeout_seconds,
                        **kwargs,
                    )
                    choice = response.choices[0] if response.choices else None
                    content = choice.message.content if choice and choice.message else ""
                    tool_calls_fb = None
                    if choice and choice.message and getattr(choice.message, "tool_calls", None):
                        tool_calls_fb = [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                }
                            }
                            for tc in choice.message.tool_calls
                        ]
                    usage = (
                        response.usage.model_dump() if hasattr(response, "usage") and hasattr(response.usage, "model_dump")
                        else dict(response.usage) if hasattr(response, "usage") and response.usage else {}
                    )
                    return {
                        "content": content,
                        "model": response.model,
                        "usage": usage,
                        "tool_calls": tool_calls_fb,
                        "fallback_triggered": True,
                        "raw": response,
                    }
                except Exception as fallback_exc:
                    raise GroqException(
                        f"Both primary ('{target_model}') and fallback ('{fallback_model}') models failed: {fallback_exc}"
                    ) from fallback_exc
            raise GroqException(f"Groq API generation failed on model '{target_model}': {primary_exc}") from primary_exc

    async def close(self) -> None:
        """(`6.9 Connection Lifecycle`) Closes active AsyncGroq HTTP sessions."""
        if self.client:
            await self.client.close()
            self.client = None
            self._is_initialized = False
            logger.info("GroqProvider HTTP client closed.")
