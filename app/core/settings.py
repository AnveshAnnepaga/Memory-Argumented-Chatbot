# File: app/core/settings.py
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.constants import (
    EnvironmentType,
    LogLevel,
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_APP_BUILD,
    DEFAULT_APP_DESCRIPTION,
    DEFAULT_API_PREFIX,
    DEFAULT_POSTGRES_PORT,
    DEFAULT_MONGO_PORT,
    DEFAULT_NEO4J_PORT,
    DEFAULT_CHAT_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_RERANKER_MODEL,
    DEFAULT_EVALUATION_MODEL,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_GROQ_TEMPERATURE,
    DEFAULT_GROQ_MAX_TOKENS,
    DEFAULT_NVIDIA_MODEL,
    DEFAULT_NVIDIA_TEMPERATURE,
    DEFAULT_NVIDIA_MAX_TOKENS,
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_BM25_WEIGHT,
    DEFAULT_DENSE_WEIGHT,
    DEFAULT_CONVERSATION_WINDOW,
    DEFAULT_MEMORY_THRESHOLD,
    DEFAULT_SUMMARY_THRESHOLD,
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_RETENTION_DAYS,
)


class ModelRegistryConfig(BaseModel):
    """Centralized Model Registry configuration."""
    chat_model: str = DEFAULT_CHAT_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    reranker_model: str = DEFAULT_RERANKER_MODEL
    evaluation_model: str = DEFAULT_EVALUATION_MODEL
    fallback_model: str = DEFAULT_FALLBACK_MODEL


class FeatureFlagsConfig(BaseModel):
    """Feature toggles to dynamically enable or disable application modules."""
    enable_memory: bool = True
    enable_graph: bool = True
    enable_tools: bool = True
    enable_hybrid_rag: bool = True
    enable_reranker: bool = True
    enable_evaluation: bool = False


class AppConfig(BaseModel):
    """General application settings & metadata."""
    name: str = DEFAULT_APP_NAME
    version: str = DEFAULT_APP_VERSION
    build_version: str = DEFAULT_APP_BUILD
    description: str = DEFAULT_APP_DESCRIPTION
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    debug: bool = True
    api_prefix: str = DEFAULT_API_PREFIX
    secret_key: str = "change-me-in-production-super-secret-key"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        if info.data.get("environment") == EnvironmentType.PRODUCTION and v == "change-me-in-production-super-secret-key":
            raise ValueError("SECRET_KEY must be changed from default when running in production environment.")
        return v


class GroqConfig(BaseModel):
    """Groq API settings."""
    api_key: str = Field(default="", exclude=True)  # Never serialized
    model: str = DEFAULT_CHAT_MODEL
    temperature: float = Field(default=DEFAULT_GROQ_TEMPERATURE, ge=0.0, le=2.0)
    max_tokens: int = Field(default=DEFAULT_GROQ_MAX_TOKENS, gt=0)
    timeout_seconds: int = 30


class NvidiaConfig(BaseModel):
    """NVIDIA NIM API settings."""
    api_key: str = Field(default="", exclude=True)  # Never serialized
    model: str = DEFAULT_NVIDIA_MODEL
    temperature: float = Field(default=DEFAULT_NVIDIA_TEMPERATURE, ge=0.0, le=2.0)
    max_tokens: int = Field(default=DEFAULT_NVIDIA_MAX_TOKENS, gt=0)
    timeout_seconds: int = 90


class EmbeddingConfig(BaseModel):
    """Embedding pipeline configuration."""
    dimension: int = DEFAULT_EMBEDDING_DIMENSION
    batch_size: int = 32
    normalize: bool = True


class PromptConfig(BaseModel):
    """System prompt configuration."""
    max_history_tokens: int = 2048
    system_template_path: str = "app/ai/prompt_builder/templates.py"


class AIConfig(BaseModel):
    """Grouped AI configuration."""
    models: ModelRegistryConfig
    groq: GroqConfig
    nvidia: NvidiaConfig
    embeddings: EmbeddingConfig
    prompt: PromptConfig


class RetrievalConfig(BaseModel):
    """Hybrid RAG retrieval settings."""
    top_k: int = Field(default=DEFAULT_TOP_K, gt=0)
    similarity_threshold: float = Field(default=DEFAULT_SIMILARITY_THRESHOLD, ge=0.0, le=1.0)
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, gt=0)
    chunk_overlap: int = Field(default=DEFAULT_CHUNK_OVERLAP, ge=0)
    bm25_weight: float = Field(default=DEFAULT_BM25_WEIGHT, ge=0.0, le=1.0)
    dense_weight: float = Field(default=DEFAULT_DENSE_WEIGHT, ge=0.0, le=1.0)
    sparse_weight: float = 0.0
    namespace: str = "default"

    @model_validator(mode="after")
    def validate_weights(self) -> "RetrievalConfig":
        total = self.bm25_weight + self.dense_weight
        if total > 0 and abs(total - 1.0) > 1e-4 and self.sparse_weight == 0.0:
            # Normalize or allow flexibility if sparse_weight is added explicitly
            pass
        return self


class MemoryConfig(BaseModel):
    """Memory retention and summarization configuration."""
    conversation_window: int = Field(default=DEFAULT_CONVERSATION_WINDOW, gt=0)
    memory_threshold: float = Field(default=DEFAULT_MEMORY_THRESHOLD, ge=0.0, le=1.0)
    summary_threshold: int = Field(default=DEFAULT_SUMMARY_THRESHOLD, gt=0)
    memory_limit: int = Field(default=DEFAULT_MEMORY_LIMIT, gt=0)
    retention_days: int = Field(default=DEFAULT_RETENTION_DAYS, ge=1)


class ToolsConfig(BaseModel):
    """Tool manager & third-party tool API configurations."""
    weather_api_key: str = Field(default="", exclude=True)  # Never serialized
    weather_enabled: bool = True
    news_api_key: str = Field(default="", exclude=True)  # Never serialized
    news_enabled: bool = True
    search_api_key: str = Field(default="", exclude=True)  # Never serialized
    search_enabled: bool = True
    translation_enabled: bool = True
    currency_enabled: bool = True


class LoggingConfig(BaseModel):
    """Extended logging configuration."""
    console_logging: bool = True
    file_logging: bool = True
    level: LogLevel = LogLevel.INFO
    format_json: bool = False
    file_path: Optional[str] = "app.log"
    max_file_size_mb: int = 10
    retention_files: int = 5


class EvaluationConfig(BaseModel):
    """Evaluation metrics configuration for Ragas & DeepEval."""
    faithfulness_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    groundedness_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    latency_target_ms: int = Field(default=2000, gt=0)
    ragas_enabled: bool = True
    deepeval_enabled: bool = True
    prompt_cost_per_1m_tokens_usd: float = Field(default=0.50, ge=0.0, description="USD cost per 1M prompt tokens")
    completion_cost_per_1m_tokens_usd: float = Field(default=0.80, ge=0.0, description="USD cost per 1M completion tokens")



class PostgresConfig(BaseModel):
    """PostgreSQL relational database settings."""
    host: str = "localhost"
    port: int = DEFAULT_POSTGRES_PORT
    user: str = "postgres"
    password: str = Field(default="password", exclude=True)  # Never serialized
    db_name: str = "chatbot_db"
    pool_size: int = 10
    echo: bool = False

    @property
    def sync_url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"

    @property
    def async_url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"


class MongoConfig(BaseModel):
    """MongoDB NoSQL document store settings."""
    uri: str = f"mongodb://localhost:{DEFAULT_MONGO_PORT}"
    db_name: str = "chatbot_memory"
    max_connections: int = 100


class PineconeConfig(BaseModel):
    """Pinecone vector database settings."""
    api_key: str = Field(default="", exclude=True)  # Never serialized
    environment: str = "us-east-1"
    index_name: str = "chatbot-vectors"
    namespace: str = "default"
    dimension: int = DEFAULT_EMBEDDING_DIMENSION


class Neo4jConfig(BaseModel):
    """Neo4j graph database settings."""
    uri: str = f"bolt://localhost:{DEFAULT_NEO4J_PORT}"
    user: str = "neo4j"
    username: str = "neo4j"
    password: str = Field(default="password", exclude=True)  # Never serialized
    database: str = "neo4j"
    max_connection_pool_size: int = 50

    @model_validator(mode="after")
    def sync_username(self) -> "Neo4jConfig":
        """Ensure `username` always mirrors `user` for backward compatibility."""
        if not self.username:
            self.username = self.user
        return self


class StorageConfig(BaseModel):
    """Grouped storage database configuration."""
    sql: PostgresConfig
    mongo: MongoConfig
    vector: PineconeConfig
    graph: Neo4jConfig


class Settings(BaseSettings):
    """
    Centralized Application Configuration loaded from environment variables and .env file.
    Validates and constructs all grouped sub-configurations:
    - app (AppConfig)
    - feature_flags (FeatureFlagsConfig)
    - ai (AIConfig -> models, groq, embeddings, prompt)
    - retrieval (RetrievalConfig)
    - memory (MemoryConfig)
    - tools (ToolsConfig)
    - evaluation (EvaluationConfig)
    - storage (StorageConfig -> sql, mongo, vector, graph)
    - logging (LoggingConfig)
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Flat Environment Variables
    APP_NAME: str = DEFAULT_APP_NAME
    APP_VERSION: str = DEFAULT_APP_VERSION
    APP_BUILD_VERSION: str = DEFAULT_APP_BUILD
    APP_DESCRIPTION: str = DEFAULT_APP_DESCRIPTION
    APP_ENV: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    API_PREFIX: str = DEFAULT_API_PREFIX
    SECRET_KEY: str = "change-me-in-production-super-secret-key"

    # Feature Flags
    ENABLE_MEMORY: bool = True
    ENABLE_GRAPH: bool = True
    ENABLE_TOOLS: bool = True
    ENABLE_HYBRID_RAG: bool = True
    ENABLE_RERANKER: bool = True
    ENABLE_EVALUATION: bool = False

    # Model Registry
    CHAT_MODEL: str = DEFAULT_CHAT_MODEL
    EMBEDDING_MODEL: str = DEFAULT_EMBEDDING_MODEL
    RERANKER_MODEL: str = DEFAULT_RERANKER_MODEL
    EVALUATION_MODEL: str = DEFAULT_EVALUATION_MODEL
    FALLBACK_MODEL: str = DEFAULT_FALLBACK_MODEL

    # Groq & AI
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = DEFAULT_CHAT_MODEL
    GROQ_TEMPERATURE: float = DEFAULT_GROQ_TEMPERATURE
    GROQ_MAX_TOKENS: int = DEFAULT_GROQ_MAX_TOKENS

    # NVIDIA NIM
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = DEFAULT_NVIDIA_MODEL
    NVIDIA_TEMPERATURE: float = DEFAULT_NVIDIA_TEMPERATURE
    NVIDIA_MAX_TOKENS: int = DEFAULT_NVIDIA_MAX_TOKENS

    # Retrieval
    RETRIEVAL_TOP_K: int = DEFAULT_TOP_K
    RETRIEVAL_SIMILARITY_THRESHOLD: float = DEFAULT_SIMILARITY_THRESHOLD
    RETRIEVAL_CHUNK_SIZE: int = DEFAULT_CHUNK_SIZE
    RETRIEVAL_CHUNK_OVERLAP: int = DEFAULT_CHUNK_OVERLAP
    RETRIEVAL_BM25_WEIGHT: float = DEFAULT_BM25_WEIGHT
    RETRIEVAL_DENSE_WEIGHT: float = DEFAULT_DENSE_WEIGHT

    # Memory
    MEMORY_CONVERSATION_WINDOW: int = DEFAULT_CONVERSATION_WINDOW
    MEMORY_THRESHOLD: float = DEFAULT_MEMORY_THRESHOLD
    MEMORY_SUMMARY_THRESHOLD: int = DEFAULT_SUMMARY_THRESHOLD
    MEMORY_LIMIT: int = DEFAULT_MEMORY_LIMIT
    MEMORY_RETENTION_DAYS: int = DEFAULT_RETENTION_DAYS

    # Tools
    WEATHER_API_KEY: str = ""
    WEATHER_ENABLED: bool = True
    NEWS_API_KEY: str = ""
    NEWS_ENABLED: bool = True
    SEARCH_API_KEY: str = ""
    SEARCH_ENABLED: bool = True
    TRANSLATION_ENABLED: bool = True
    CURRENCY_ENABLED: bool = True

    # Evaluation
    EVAL_FAITHFULNESS_THRESHOLD: float = 0.8
    EVAL_GROUNDEDNESS_THRESHOLD: float = 0.8
    EVAL_LATENCY_TARGET_MS: int = 2000
    RAGAS_ENABLED: bool = True
    DEEPEVAL_ENABLED: bool = True
    EVAL_PROMPT_COST_PER_1M_TOKENS: float = 0.50
    EVAL_COMPLETION_COST_PER_1M_TOKENS: float = 0.80

    # Storage Databases
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = DEFAULT_POSTGRES_PORT
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "chatbot_db"
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_ECHO: bool = False

    MONGODB_URI: str = f"mongodb://localhost:{DEFAULT_MONGO_PORT}"
    MONGODB_DB_NAME: str = "chatbot_memory"
    MONGODB_MAX_CONNECTIONS: int = 100

    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "chatbot-vectors"
    PINECONE_NAMESPACE: str = "default"
    PINECONE_DIMENSION: int = DEFAULT_EMBEDDING_DIMENSION

    NEO4J_URI: str = f"bolt://localhost:{DEFAULT_NEO4J_PORT}"
    NEO4J_USER: str = "neo4j"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"

    # Logging
    LOG_CONSOLE: bool = True
    LOG_FILE: bool = True
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FORMAT_JSON: bool = False
    LOG_FILE_PATH: Optional[str] = "app.log"
    LOG_MAX_FILE_SIZE_MB: int = 10
    LOG_RETENTION_FILES: int = 5

    # Grouped Sub-Configurations
    app: Optional[AppConfig] = None
    feature_flags: Optional[FeatureFlagsConfig] = None
    ai: Optional[AIConfig] = None
    retrieval: Optional[RetrievalConfig] = None
    memory: Optional[MemoryConfig] = None
    tools: Optional[ToolsConfig] = None
    evaluation: Optional[EvaluationConfig] = None
    storage: Optional[StorageConfig] = None
    logging: Optional[LoggingConfig] = None

    @model_validator(mode="after")
    def build_sub_configs(self) -> "Settings":
        """Builds all categorized sub-configurations from flat environment inputs."""
        self.app = AppConfig(
            name=self.APP_NAME,
            version=self.APP_VERSION,
            build_version=self.APP_BUILD_VERSION,
            description=self.APP_DESCRIPTION,
            environment=self.APP_ENV,
            debug=self.DEBUG,
            api_prefix=self.API_PREFIX,
            secret_key=self.SECRET_KEY,
        )
        self.feature_flags = FeatureFlagsConfig(
            enable_memory=self.ENABLE_MEMORY,
            enable_graph=self.ENABLE_GRAPH,
            enable_tools=self.ENABLE_TOOLS,
            enable_hybrid_rag=self.ENABLE_HYBRID_RAG,
            enable_reranker=self.ENABLE_RERANKER,
            enable_evaluation=self.ENABLE_EVALUATION,
        )
        models_cfg = ModelRegistryConfig(
            chat_model=self.CHAT_MODEL,
            embedding_model=self.EMBEDDING_MODEL,
            reranker_model=self.RERANKER_MODEL,
            evaluation_model=self.EVALUATION_MODEL,
            fallback_model=self.FALLBACK_MODEL,
        )
        groq_cfg = GroqConfig(
            api_key=self.GROQ_API_KEY,
            model=self.GROQ_MODEL,
            temperature=self.GROQ_TEMPERATURE,
            max_tokens=self.GROQ_MAX_TOKENS,
        )
        nvidia_cfg = NvidiaConfig(
            api_key=self.NVIDIA_API_KEY,
            model=self.NVIDIA_MODEL,
            temperature=self.NVIDIA_TEMPERATURE,
            max_tokens=self.NVIDIA_MAX_TOKENS,
        )
        embeddings_cfg = EmbeddingConfig(dimension=self.PINECONE_DIMENSION)
        prompt_cfg = PromptConfig()
        self.ai = AIConfig(
            models=models_cfg,
            groq=groq_cfg,
            nvidia=nvidia_cfg,
            embeddings=embeddings_cfg,
            prompt=prompt_cfg,
        )
        self.retrieval = RetrievalConfig(
            top_k=self.RETRIEVAL_TOP_K,
            similarity_threshold=self.RETRIEVAL_SIMILARITY_THRESHOLD,
            chunk_size=self.RETRIEVAL_CHUNK_SIZE,
            chunk_overlap=self.RETRIEVAL_CHUNK_OVERLAP,
            bm25_weight=self.RETRIEVAL_BM25_WEIGHT,
            dense_weight=self.RETRIEVAL_DENSE_WEIGHT,
            namespace=self.PINECONE_NAMESPACE,
        )
        self.memory = MemoryConfig(
            conversation_window=self.MEMORY_CONVERSATION_WINDOW,
            memory_threshold=self.MEMORY_THRESHOLD,
            summary_threshold=self.MEMORY_SUMMARY_THRESHOLD,
            memory_limit=self.MEMORY_LIMIT,
            retention_days=self.MEMORY_RETENTION_DAYS,
        )
        self.tools = ToolsConfig(
            weather_api_key=self.WEATHER_API_KEY,
            weather_enabled=self.WEATHER_ENABLED,
            news_api_key=self.NEWS_API_KEY,
            news_enabled=self.NEWS_ENABLED,
            search_api_key=self.SEARCH_API_KEY,
            search_enabled=self.SEARCH_ENABLED,
            translation_enabled=self.TRANSLATION_ENABLED,
            currency_enabled=self.CURRENCY_ENABLED,
        )
        self.evaluation = EvaluationConfig(
            faithfulness_threshold=self.EVAL_FAITHFULNESS_THRESHOLD,
            groundedness_threshold=self.EVAL_GROUNDEDNESS_THRESHOLD,
            latency_target_ms=self.EVAL_LATENCY_TARGET_MS,
            ragas_enabled=self.RAGAS_ENABLED,
            deepeval_enabled=self.DEEPEVAL_ENABLED,
            prompt_cost_per_1m_tokens_usd=self.EVAL_PROMPT_COST_PER_1M_TOKENS,
            completion_cost_per_1m_tokens_usd=self.EVAL_COMPLETION_COST_PER_1M_TOKENS,
        )
        sql_cfg = PostgresConfig(
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            user=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            db_name=self.POSTGRES_DB,
            pool_size=self.POSTGRES_POOL_SIZE,
            echo=self.POSTGRES_ECHO,
        )
        mongo_cfg = MongoConfig(
            uri=self.MONGODB_URI,
            db_name=self.MONGODB_DB_NAME,
            max_connections=self.MONGODB_MAX_CONNECTIONS,
        )
        vector_cfg = PineconeConfig(
            api_key=self.PINECONE_API_KEY,
            environment=self.PINECONE_ENVIRONMENT,
            index_name=self.PINECONE_INDEX_NAME,
            namespace=self.PINECONE_NAMESPACE,
            dimension=self.PINECONE_DIMENSION,
        )
        graph_cfg = Neo4jConfig(
            uri=self.NEO4J_URI,
            user=self.NEO4J_USER,
            username=self.NEO4J_USERNAME or self.NEO4J_USER,
            password=self.NEO4J_PASSWORD,
            database=self.NEO4J_DATABASE,
        )
        self.storage = StorageConfig(
            sql=sql_cfg,
            mongo=mongo_cfg,
            vector=vector_cfg,
            graph=graph_cfg,
        )
        self.logging = LoggingConfig(
            console_logging=self.LOG_CONSOLE,
            file_logging=self.LOG_FILE,
            level=self.LOG_LEVEL,
            format_json=self.LOG_FORMAT_JSON,
            file_path=self.LOG_FILE_PATH,
            max_file_size_mb=self.LOG_MAX_FILE_SIZE_MB,
            retention_files=self.LOG_RETENTION_FILES,
        )
        return self

    # Shortcut Properties for direct database access (e.g., settings.postgres)
    @property
    def postgres(self) -> PostgresConfig:
        return self.storage.sql

    @property
    def mongodb(self) -> MongoConfig:
        return self.storage.mongo

    @property
    def pinecone(self) -> PineconeConfig:
        return self.storage.vector

    @property
    def neo4j(self) -> Neo4jConfig:
        return self.storage.graph
