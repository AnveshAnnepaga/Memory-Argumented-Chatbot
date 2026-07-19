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
        await asyncio.sleep(0.05)

        prompt_text = (
            messages[-1].get("content", "") if isinstance(messages, list) and messages
            else str(messages)
        ).strip()

        import re
        q_lower = prompt_text.lower().strip()

        greetings = [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreetings\b", r"\bgood morning\b", r"\bgood afternoon\b", r"\bgood evening\b"]
        if any(re.search(pat, q_lower) for pat in greetings) and len(q_lower.split()) <= 4:
            simulated_response = "Hello! I'm Vyron AI, your intelligent assistant. I'm here to help with coding, analysis, explanations, and more. What would you like to explore today?"
        elif any(re.search(r"\b(who are you|what are you|about you)\b", q_lower) for _ in [0]):
            simulated_response = "I am Vyron AI, an intelligent AI coding and reasoning assistant created by Anvesh Mishra. I'm powered by a hybrid RAG system combining vector search, knowledge graphs, and long-term memory. How can I help you today?"
        elif re.search(r"\bpython\b", q_lower) and any(w in q_lower for w in ["what", "explain", "tell", "about"]):
            simulated_response = "Python is a high-level, general-purpose programming language known for its clear syntax and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is widely used in web development, data science, machine learning, automation, and more."
        elif re.search(r"\b(langchain|langgraph)\b", q_lower) and any(w in q_lower for w in ["what", "explain", "tell", "about"]):
            topic = "LangChain" if "langchain" in q_lower else "LangGraph"
            simulated_response = f"{topic} is a framework for building applications powered by large language models (LLMs). " + (f"LangChain provides tools for prompts, chains, agents, and memory components." if topic == "LangChain" else "LangGraph extends LangChain with graph-based workflows using a StateGraph model for complex multi-step reasoning with state management.")
        elif re.search(r"\b(rag|retrieval|hybrid)\b", q_lower) and any(w in q_lower for w in ["what", "explain", "tell", "about"]):
            simulated_response = "RAG (Retrieval-Augmented Generation) combines vector database retrieval with LLM generation. Hybrid RAG blends dense vector search (semantic similarity) with sparse keyword search (BM25) for better retrieval. Results are fused using Reciprocal Rank Fusion for optimal context selection."
        elif any(w in q_lower for w in ["help", "capabilities", "what can you do"]):
            simulated_response = "I can help you with: coding assistance and debugging, explaining technical concepts and architectures, analyzing documents (PDF, DOCX, images), web search and information retrieval, database queries and graph traversal, calculator and unit conversions, and general reasoning tasks. Just ask!"
        elif re.search(r"\b(thanks|thank you|cheers)\b", q_lower):
            simulated_response = "You're welcome! Is there anything else I can help you with?"
        else:
            simulated_response = f"I understand you're asking about: '{prompt_text}'. To provide accurate information, I need access to my full LLM capabilities. Currently running in fallback mode. Please ensure GROQ_API_KEY or NVIDIA_API_KEY is properly configured in your environment variables. For production, set these API keys in your Railway/Railway environment settings."

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
