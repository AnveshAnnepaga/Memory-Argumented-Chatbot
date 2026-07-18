# File: app/core/constants.py
from enum import Enum


class EnvironmentType(str, Enum):
    """Supported application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Supported logging severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Application defaults & metadata
DEFAULT_APP_NAME = "Memory-Augmented Chatbot"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_APP_BUILD = "2026.07.01"
DEFAULT_APP_DESCRIPTION = "Advanced Memory-Augmented AI Assistant powered by Knowledge Graphs and Hybrid RAG."
DEFAULT_API_PREFIX = "/api/v1"

# Connection timeouts & limits
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_POOL_SIZE = 10
DEFAULT_MAX_CONNECTIONS = 100

# Default database ports
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_MONGO_PORT = 27017
DEFAULT_NEO4J_PORT = 7687

# AI & Model Registry defaults
DEFAULT_CHAT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-large"
DEFAULT_EVALUATION_MODEL = "llama-3.3-70b-versatile"
DEFAULT_FALLBACK_MODEL = "llama-3.1-8b-instant"

DEFAULT_GROQ_TEMPERATURE = 0.2
DEFAULT_GROQ_MAX_TOKENS = 4096

# NVIDIA NIM defaults
DEFAULT_NVIDIA_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
DEFAULT_NVIDIA_TEMPERATURE = 0.2
DEFAULT_NVIDIA_MAX_TOKENS = 4096

DEFAULT_EMBEDDING_DIMENSION = 1536

# Retrieval defaults
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.75
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64
DEFAULT_BM25_WEIGHT = 0.4
DEFAULT_DENSE_WEIGHT = 0.6

# Memory defaults
DEFAULT_CONVERSATION_WINDOW = 10
DEFAULT_MEMORY_THRESHOLD = 0.8
DEFAULT_SUMMARY_THRESHOLD = 20
DEFAULT_MEMORY_LIMIT = 100
DEFAULT_RETENTION_DAYS = 30
