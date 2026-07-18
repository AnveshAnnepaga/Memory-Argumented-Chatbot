# File: app/ai/llm/llm_manager.py
import logging
from typing import Any, Dict, List, Optional, Union
from app.ai.llm.base import BaseLLMProvider
from app.ai.llm.groq_client import GroqProvider
from app.ai.llm.nvidia_client import NvidiaProvider
from app.ai.llm.mock_provider import MockLLMProvider
from app.core.exceptions import GroqException
from app.core.infrastructure import BaseInfrastructureManager

logger = logging.getLogger("app.ai.llm.llm_manager")


class LLMProviderManager(BaseInfrastructureManager):
    """
    (`⭐ One More Improvement`: Decoupled LLM Provider Manager & `6.5 Groq Manager`)
    Centralized orchestration layer for all large language model interactions.
    Manages primary Groq provider, testing Mock provider, and future multi-provider routing without
    tightly coupling application code (`LangGraph`, `ChatService`) directly to a single vendor.
    """
    def __init__(self):
        super().__init__(name="groq")
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.primary_provider_key: str = "nvidia"
        self._setup_providers()

    def _setup_providers(self) -> None:
        self.register_provider("nvidia", NvidiaProvider())
        self.register_provider("groq", GroqProvider())
        self.register_provider("mock", MockLLMProvider())

    def register_provider(self, key: str, provider: BaseLLMProvider) -> None:
        self.providers[key] = provider
        logger.debug(f"Registered LLM Provider: '{key}' ({provider.__class__.__name__})")

    async def initialize(self) -> bool:
        """Initializes primary provider (Groq) and secondary testing provider (Mock)."""
        logger.info("Initializing LLM Provider Manager...")
        results = {}
        for key, provider in self.providers.items():
            try:
                results[key] = await provider.initialize()
            except Exception as exc:
                logger.error(f"Failed to initialize provider '{key}': {exc}")
                results[key] = False

        self._is_initialized = results.get(self.primary_provider_key, False) or results.get("mock", False)
        logger.info(f"LLM Provider Manager ready [Active Primary: '{self.active_provider_key}'].")
        return self._is_initialized

    @property
    def active_provider_key(self) -> str:
        primary = self.providers.get(self.primary_provider_key)
        if primary and primary.is_initialized and not getattr(primary, "stub_mode", False):
            return self.primary_provider_key
        groq = self.providers.get("groq")
        if groq and groq.is_initialized and not getattr(groq, "stub_mode", False):
            return "groq"
        return "mock" if "mock" in self.providers else self.primary_provider_key

    def get_provider(self, provider_key: Optional[str] = None) -> BaseLLMProvider:
        """Returns the requested provider (or the currently active primary/fallback provider)."""
        key = provider_key or self.active_provider_key
        if key not in self.providers:
            raise KeyError(f"LLM provider '{key}' is not registered.")
        return self.providers[key]

    def get_client(self) -> Any:
        """(`6.9 Connection Lifecycle`) Returns underlying SDK client of the active provider."""
        provider = self.get_provider()
        return getattr(provider, "client", provider)

    async def health_check(self) -> Dict[str, Any]:
        """(`6.7 Health Integration`) Diagnoses status of all registered LLM providers."""
        provider_reports = {}
        for key, provider in self.providers.items():
            try:
                provider_reports[key] = await provider.health_check()
            except Exception as exc:
                provider_reports[key] = {"healthy": False, "status": "error", "error": str(exc)}

        primary_healthy = provider_reports.get(self.primary_provider_key, {}).get("healthy", False)
        return {
            "healthy": primary_healthy or self.active_provider_key == "mock",
            "status": "online" if primary_healthy else "degraded_fallback_to_mock",
            "active_provider": self.active_provider_key,
            "providers": provider_reports,
        }

    async def generate(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        provider_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Executes text completion through the active provider (`Groq` by default).
        If `Groq` is offline or fails, automatically falls back to `MockProvider` when appropriate.
        """
        target_key = provider_key or self.active_provider_key
        provider = self.get_provider(target_key)
        try:
            return await provider.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                **kwargs,
            )
        except Exception as exc:
            fallback_chain = ["groq", "mock"]
            for fb_key in fallback_chain:
                if target_key == fb_key or fb_key not in self.providers:
                    continue
                fb_provider = self.providers[fb_key]
                if getattr(fb_provider, "stub_mode", False):
                    continue
                logger.warning(
                    f"LLM generation on provider '{target_key}' failed ({exc}). Falling back to '{fb_key}' provider..."
                )
                try:
                    return await fb_provider.generate(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=timeout,
                        **kwargs,
                    )
                except Exception:
                    continue
            raise GroqException(f"LLM generation failed across all available providers: {exc}") from exc

    async def close(self) -> None:
        """(`6.9 Connection Lifecycle`) Closes all provider connections."""
        for key, provider in self.providers.items():
            await provider.close()
            logger.info(f"Closed LLM provider '{key}'.")
        self._is_initialized = False


llm_manager = LLMProviderManager()
