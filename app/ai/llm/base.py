# File: app/ai/llm/base.py
import abc
from typing import Any, Dict, List, Optional, Union


class BaseLLMProvider(abc.ABC):
    """
    (`⭐ One More Improvement`: Generic LLM Provider Interface)
    Abstract base class ensuring all LLM providers (Groq, Mock, OpenAI, Anthropic, etc.)
    follow an identical interface for initialization, completion, and health checks.
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self._is_initialized = False

    @abc.abstractmethod
    async def initialize(self) -> bool:
        """Initializes API client, validates credentials, and verifies reachability."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Performs live diagnostic check against the provider API (`6.7 Health Integration`)."""
        pass

    @abc.abstractmethod
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
        Executes a completion/chat generation request against the model provider.
        Returns standardized dict: `{"content": str, "model": str, "usage": dict, "raw": any}`.
        """
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """Closes active HTTP sessions or client pools."""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized
