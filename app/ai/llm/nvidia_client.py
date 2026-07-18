# File: app/ai/llm/nvidia_client.py
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

import httpx

from app.ai.llm.base import BaseLLMProvider
from app.core.config import settings
from app.core.exceptions import GroqException
from app.core.retry import execute_with_retry

logger = logging.getLogger("app.ai.llm.nvidia_client")


class NvidiaProvider(BaseLLMProvider):
    """
    LLM provider wrapping NVIDIA NIM's OpenAI-compatible API.
    Uses the /v1/chat/completions endpoint with httpx.
    """
    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self):
        super().__init__(provider_name="nvidia")
        self.client: httpx.AsyncClient | None = None
        self.stub_mode: bool = False

    @execute_with_retry(max_attempts=1, min_wait=0.2, max_wait=0.5, exceptions=(Exception,))
    async def _ping_api(self) -> Dict[str, Any]:
        if not self.client:
            return {}
        response = await asyncio.wait_for(
            self.client.get(f"{self.BASE_URL}/models"),
            timeout=5.0,
        )
        if response.status_code != 200:
            return {}
        data = response.json()
        models = [m["id"] for m in data.get("data", [])]
        return {"models_count": len(models), "sample_models": models[:5]}

    async def initialize(self) -> bool:
        api_key = getattr(settings, "NVIDIA_API_KEY", getattr(settings.ai.nvidia, "api_key", ""))
        if not api_key or api_key == "your_nvidia_api_key_here":
            logger.warning("NVIDIA_API_KEY missing or placeholder. NvidiaProvider entering stub/fallback mode.")
            self._is_initialized = True
            self.stub_mode = True
            return False

        try:
            timeout_val = getattr(settings.ai.nvidia, "timeout_seconds", 60)
            self.client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(timeout_val),
            )
            stats = await self._ping_api()
            self._is_initialized = True
            self.stub_mode = False
            logger.info(
                f"NVIDIA NIM Client verified successfully [Model: '{settings.ai.models.chat_model}' | Available Models: {stats.get('models_count', 0)}]."
            )
            return True
        except Exception as exc:
            logger.warning(
                f"NVIDIA NIM API verification failed during startup ({exc}). Entering offline/stub mode."
            )
            self._is_initialized = True
            self.stub_mode = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        if self.stub_mode or not self.client:
            return {
                "healthy": False,
                "status": "stubbed_local_dev",
                "message": "NVIDIA NIM API not connected (placeholder API key configured)",
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

    @execute_with_retry(max_attempts=1, min_wait=1.0, max_wait=5.0, exceptions=(Exception,))
    async def generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if self.stub_mode or not self.client:
            raise GroqException("NvidiaProvider is in offline/stub mode. Cannot generate completion without a valid API key.")

        formatted_messages = (
            [{"role": "user", "content": messages}] if isinstance(messages, str) else messages
        )
        target_model = model or settings.ai.nvidia.model
        temp = temperature if temperature is not None else settings.ai.nvidia.temperature
        tokens = max_tokens if max_tokens is not None else settings.ai.nvidia.max_tokens

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": formatted_messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        tools = kwargs.pop("tools", None)
        if tools:
            payload["tools"] = tools

        try:
            response = await asyncio.wait_for(
                self.client.post("/chat/completions", json=payload),
                timeout=timeout or settings.ai.nvidia.timeout_seconds,
            )
            if response.status_code != 200:
                raise GroqException(
                    f"NVIDIA NIM API returned status {response.status_code}: {response.text[:500]}"
                )

            data = response.json()
            choice = data["choices"][0] if data.get("choices") else None
            message = choice.get("message", {}) if choice else {}
            content = message.get("content", "")
            tool_calls_raw = message.get("tool_calls")

            tool_calls = None
            if tool_calls_raw:
                tool_calls = [
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                    for tc in tool_calls_raw
                ]

            usage = data.get("usage", {})

            return {
                "content": content,
                "model": data.get("model", target_model),
                "usage": usage,
                "tool_calls": tool_calls,
                "raw": data,
            }
        except Exception as exc:
            exc_msg = str(exc) or type(exc).__name__
            raise GroqException(
                f"NVIDIA NIM API generation failed on model '{target_model}': {exc_msg}"
            ) from exc

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
            self._is_initialized = False
            logger.info("NvidiaProvider HTTP client closed.")
