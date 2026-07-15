# File: app/memory/__init__.py
"""
(`Milestone 12 Long-Term Memory System`)
Exports schemas, extractor, manager, retriever, summarizer, and pipeline facade.
"""
from app.memory.schemas import (
    ConversationMemory,
    Episode,
    MemoryAction,
    MemoryContext,
    MemoryExtractionItem,
    MemoryExtractionResult,
    MemoryType,
    SemanticMemory,
    UserProfile,
)
from app.memory.extractor import MemoryExtractor
from app.memory.manager import MemoryManager, memory_manager
from app.memory.retriever import MemoryRetriever, memory_retriever
from app.memory.summarizer import MemorySummarizer, memory_summarizer
from app.memory.pipeline import MemoryPipeline, memory_pipeline

__all__ = [
    "MemoryType",
    "MemoryAction",
    "ConversationMemory",
    "SemanticMemory",
    "Episode",
    "UserProfile",
    "MemoryExtractionItem",
    "MemoryExtractionResult",
    "MemoryContext",
    "MemoryExtractor",
    "MemoryManager",
    "memory_manager",
    "MemoryRetriever",
    "memory_retriever",
    "MemorySummarizer",
    "memory_summarizer",
    "MemoryPipeline",
    "memory_pipeline",
]
