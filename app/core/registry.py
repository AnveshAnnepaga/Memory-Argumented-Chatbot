# File: app/core/registry.py
from typing import Dict, Optional
from app.core.config import settings


class ModelRegistry:
    """
    Centralized Model Registry providing clean model lookups and fallback logic
    based on the AI configuration (`settings.ai.models`).
    """

    @classmethod
    def get_chat_model(cls) -> str:
        """Returns the primary chat LLM model identifier."""
        return settings.ai.models.chat_model

    @classmethod
    def get_embedding_model(cls) -> str:
        """Returns the embedding model identifier."""
        return settings.ai.models.embedding_model

    @classmethod
    def get_reranker_model(cls) -> str:
        """Returns the cross-encoder reranker model identifier."""
        return settings.ai.models.reranker_model

    @classmethod
    def get_evaluation_model(cls) -> str:
        """Returns the evaluation LLM model identifier."""
        return settings.ai.models.evaluation_model

    @classmethod
    def get_fallback_model(cls) -> str:
        """Returns the fallback chat LLM model identifier."""
        return settings.ai.models.fallback_model

    @classmethod
    def get_all_models(cls) -> Dict[str, str]:
        """Returns a dictionary of all registered model identifiers."""
        return {
            "chat": cls.get_chat_model(),
            "embedding": cls.get_embedding_model(),
            "reranker": cls.get_reranker_model(),
            "evaluation": cls.get_evaluation_model(),
            "fallback": cls.get_fallback_model(),
        }
