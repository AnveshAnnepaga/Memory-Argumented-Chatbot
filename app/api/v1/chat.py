# File: app/api/v1/chat.py
import asyncio
import json
import logging
import os
import re
import uuid
from typing import Optional, AsyncGenerator, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_request_id
from app.schemas.common import APIResponse, success_response
from app.orchestration.pipeline import orchestration_pipeline
from app.orchestration.schemas import WorkflowResponse
from app.memory.pipeline import memory_pipeline
from app.utils.sanitizer import sanitize_text
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    UserInDB,
    audit_log,
)
from app.core.config import settings
from app.ai.validator.validator import guardrail_validator
from app.ai.validator.rate_limiter import check_rate_limit

logger = logging.getLogger("app.api.v1.chat")
router = APIRouter(tags=["Chat"])


class ChatQueryRequest(BaseModel):
    query: str = Field(..., description="User prompt or question to process via LangGraph orchestration")
    conversation_id: Optional[str] = Field("default", description="Conversation session ID")
    user_id: Optional[str] = Field("default", description="User identifier")
    file_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of uploaded files to include as context")
    image_ids: Optional[List[str]] = Field(default_factory=list, description="IDs of uploaded images for visual Q&A")


# ============================================================
# Enhanced Technical Content Generator
# ============================================================

def _detect_technical_domain(query: str) -> str:
    """Detect technical domain from query for enhanced content generation."""
    query_lower = query.lower()
    
    domains = {
        "architecture": ["architecture", "design pattern", "microservice", "system design", "scalability"],
        "api": ["api", "rest", "graphql", "grpc", "endpoint", "fastapi", "flask", "django"],
        "database": ["database", "sql", "postgresql", "mongodb", "redis", "query", "index", "transaction"],
        "ml": ["machine learning", "deep learning", "neural network", "transformer", "llm", "embedding", "rag"],
        "devops": ["docker", "kubernetes", "ci/cd", "deployment", "pipeline", "terraform", "ansible"],
        "frontend": ["react", "vue", "next.js", "typescript", "css", "frontend", "ui", "component"],
        "security": ["authentication", "authorization", "oauth", "jwt", "security", "encryption", "ssl"],
        "algorithm": ["algorithm", "complexity", "big o", "sorting", "search", "dynamic programming"],
        "cloud": ["aws", "azure", "gcp", "cloud", "serverless", "lambda", "cloudformation"],
        "testing": ["testing", "unit test", "integration test", "pytest", "mock", "coverage"],
        "langgraph": ["langgraph", "langchain", "agent", "workflow", "state", "graph"],
    }
    
    for domain, keywords in domains.items():
        if any(kw in query_lower for kw in keywords):
            return domain
    return "general"


def _generate_mermaid_diagram(query: str, domain: str, response: str) -> Optional[str]:
    """Generate Mermaid diagram based on query domain and response."""
    query_lower = query.lower()
    
    # Architecture diagrams
    if domain == "architecture" or "architecture" in query_lower:
        if "microservice" in query_lower:
            return """```mermaid
graph TB
    Client[Client] --> Gateway[API Gateway]
    Gateway --> Auth[Auth Service]
    Gateway --> User[User Service]
    Gateway --> Order[Order Service]
    Gateway --> Payment[Payment Service]
    Gateway --> Inventory[Inventory Service]
    
    User --> DB[(User DB)]
    Order --> DB2[(Order DB)]
    Payment --> DB3[(Payment DB)]
    Inventory --> DB4[(Inventory DB)]
    
    Order --> Queue[Message Queue]
    Payment --> Queue
    Inventory --> Queue
    
    Queue --> Notification[Notification Service]
    Queue --> Analytics[Analytics Service]
```"""
        elif "layer" in query_lower or "layered" in query_lower:
            return """```mermaid
graph TB
    subgraph Presentation[Presentation Layer]
        UI[UI Components]
        API[API Controllers]
    end
    
    subgraph Business[Business Logic Layer]
        Services[Domain Services]
        UseCases[Use Cases]
    end
    
    subgraph Data[Data Access Layer]
        Repos[Repositories]
        ORM[ORM/Database]
    end
    
    subgraph Infrastructure[Infrastructure Layer]
        Cache[Cache/Redis]
        Queue[Message Queue]
        External[External APIs]
    end
    
    Presentation --> Business
    Business --> Data
    Business --> Infrastructure
```
"""
    
    # API diagrams
    elif domain == "api":
        if "rest" in query_lower:
            return """```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant Service as Business Service
    participant DB as Database
    
    Client->>Gateway: HTTP Request
    Gateway->>Auth: Validate Token
    Auth-->>Gateway: Valid/Invalid
    Gateway->>Service: Forward Request
    Service->>DB: Query Data
    DB-->>Service: Return Data
    Service-->>Gateway: Response
    Gateway-->>Client: HTTP Response
```
"""
    
    # Database diagrams
    elif domain == "database":
        if "index" in query_lower:
            return """```mermaid
graph TD
    A[Query] --> B{Index Exists?}
    B -->|Yes| C[Index Scan]
    B -->|No| D[Full Table Scan]
    C --> E[Return Results]
    D --> E
    
    subgraph Index Types
        BTREE[B-Tree Index]
        HASH[Hash Index]
        GIN[GIN Index]
        BRIN[BRIN Index]
    end
    
    E --> F[Return to Client]
```
"""
        elif "transaction" in query_lower:
            return """```mermaid
sequenceDiagram
    participant App
    participant DB as Database
    
    App->>DB: BEGIN TRANSACTION
    App->>DB: INSERT/UPDATE/DELETE
    alt Success
        App->>DB: COMMIT
        DB-->>App: Committed
    else Failure
        App->>DB: ROLLBACK
        DB-->>App: Rolled Back
    end
```
"""
    
    # LangGraph/LangChain diagrams
    elif domain == "langgraph" or "langgraph" in query_lower or "langchain" in query_lower:
        if "workflow" in query_lower or "graph" in query_lower:
            return """```mermaid
graph TD
    START[START] --> Intent[Intent Analysis]
    Intent --> Router{Router Decision}
    
    Router -->|DIRECT_LLM| LLM[Direct LLM]
    Router -->|HYBRID_RAG| RAG[Hybrid RAG Retrieval]
    Router -->|GRAPH_RAG| Graph[GraphRAG Traversal]
    Router -->|MEMORY_ENHANCED| Memory[Memory Retrieval]
    Router -->|TOOLS_ENHANCED| Tools[Tool Execution]
    
    RAG --> Merge[Context Merge]
    Graph --> Merge
    Memory --> Merge
    Tools --> Merge
    LLM --> Merge
    
    Merge --> LLMGen[LLM Generation]
    LLMGen --> Format[Response Formatter]
    Format --> END[END]
    
    style START fill:#e1f5fe
    style END fill:#c8e6c9
    style Merge fill:#fff3e0
```
"""
    
    # ML/AI diagrams
    elif domain == "ml":
        if "rag" in query_lower:
            return """```mermaid
graph TD
    Q[User Query] --> E[Embedding Model]
    E --> V[Vector Search]
    V --> P[Pinecone/Vector DB]
    P --> R[Top-K Results]
    R --> RR[Reranker]
    RR --> C[Context Assembly]
    C --> LLM[LLM Generation]
    LLM --> O[Final Answer]
    
    subgraph Retrieval
        E --> V
        V --> P
        P --> R
        R --> RR
    end
    
    subgraph Generation
        C --> LLM
        LLM --> O
    end
```
"""
        elif "embedding" in query_lower:
            return """```mermaid
graph LR
    T[Text Input] --> Token[Tokenizer]
    Token --> Emb[Embedding Model]
    Emb --> V[Vector Output]
    
    subgraph Models
        BERT[BERT-based]
        SENTENCE[Sentence Transformers]
        OPENAI[OpenAI ada-002]
        CUSTOM[Custom Fine-tuned]
    end
    
    V --> Sim[Similarity Search]
    Sim --> Results[Top-K Results]
```
"""

    # General flowchart for processes
    elif "process" in query_lower or "flow" in query_lower or "workflow" in query_lower:
        return """```mermaid
flowchart TD
    Start([Start]) --> Input[Input Processing]
    Input --> Validate{Validation}
    Validate -->|Valid| Process[Core Processing]
    Validate -->|Invalid| Error[Error Handling]
    Process --> Transform[Transform Data]
    Transform --> Validate2{Validate Output}
    Validate2 -->|Valid| Output[Generate Output]
    Validate2 -->|Invalid| Retry[Retry/Adjust]
    Retry --> Process
    Error --> Log[Log Error]
    Log --> End([End])
    Output --> End
```
"""

    return None


def _generate_comparison_table(query: str, domain: str) -> Optional[str]:
    """Generate comparison table for technical topics."""
    query_lower = query.lower()
    
    if "vs" in query_lower or "versus" in query_lower or "compare" in query_lower:
        if "fastapi" in query_lower and "flask" in query_lower:
            return """| Feature | FastAPI | Flask |
|---------|---------|-------|
| **Performance** | ⚡ Very High (async) | Medium (sync) |
| **Type Safety** | ✅ Built-in (Pydantic) | ❌ Manual |
| **Auto Docs** | ✅ Swagger/ReDoc | ❌ Manual |
| **Async Support** | ✅ Native | ⚠️ Limited |
| **Learning Curve** | Medium | Low |
| **Ecosystem** | Growing | Mature |
| **Best For** | High-performance APIs | Simple apps, prototyping |"""
        
        elif "postgres" in query_lower and "mongo" in query_lower:
            return """| Feature | PostgreSQL | MongoDB |
|---------|------------|---------|
| **Data Model** | Relational | Document |
| **Schema** | Fixed (ALTER TABLE) | Flexible |
| **ACID** | ✅ Full | ✅ (since 4.0) |
| **Joins** | ✅ Native | ⚠️ $lookup |
| **Scaling** | Vertical + Read replicas | Horizontal (sharding) |
| **JSON** | ✅ JSONB | ✅ Native |"""
    
    # Framework comparison tables
    if "framework" in query_lower and "vs" in query_lower:
        if "django" in query_lower:
            return """| Feature | Django | FastAPI | Flask |
|---------|--------|---------|-------|
| **Type** | Full-stack | API-first | Micro |
| **Admin** | ✅ Built-in | ❌ | ❌ |
| **ORM** | ✅ Built-in | ❌ (use SQLAlchemy) | ❌ |
| **Auth** | ✅ Built-in | Manual | Manual |
| **Async** | ⚠️ Limited | ✅ Native | ⚠️ Limited |"""
    
    return None


def _generate_code_example(query: str, domain: str) -> Optional[str]:
    """Generate relevant code example for technical queries."""
    query_lower = query.lower()
    
    if "fastapi" in query_lower and ("dependency" in query_lower or "di" in query_lower):
        return """```python
# FastAPI Dependency Injection Example
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Using dependency
@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    return user

# Dependency with parameters
def get_pagination(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}

@app.get("/items")
async def list_items(pagination: dict = Depends(get_pagination)):
    return {"skip": pagination["skip"], "limit": pagination["limit"]}
```"""
    
    if "redis" in query_lower and ("cache" in query_lower or "session" in query_lower):
        return """```python
# Redis Caching Example with FastAPI
import redis.asyncio as redis
from functools import wraps
import json

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=600)
async def get_user_profile(user_id: int):
    return await db.get_user(user_id)
```"""
    
    if "async" in query_lower and "database" in query_lower:
        return """```python
# Async Database Operations with SQLAlchemy 2.0
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Engine setup
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=True,
    pool_size=20,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# CRUD Operations
async def create_user(db: AsyncSession, user_data: dict):
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def update_user(db: AsyncSession, user_id: int, data: dict):
    user = await db.get(User, user_id)
    for key, value in data.items():
        setattr(user, key, value)
    await db.commit()
    return user
```"""
    
    if "docker" in query_lower and "compose" in query_lower:
        return """```yaml
# docker-compose.yml for FastAPI + PostgreSQL + Redis
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app
    command: uvicorn main:app --host 0.0.0.0 --reload

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```"""
    
    if "kubernetes" in query_lower or "k8s" in query_lower:
        return """```yaml
# Kubernetes Deployment for FastAPI
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: api
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```"""
    
    return None


def _enhance_technical_response(response: str, query: str) -> str:
    """Enhance technical responses with diagrams, tables, and code examples."""
    domain = _detect_technical_domain(query)
    enhanced_parts = [response]
    
    # Add Mermaid diagram if relevant
    diagram = _generate_mermaid_diagram(query, domain, response)
    if diagram:
        enhanced_parts.append(f"\n\n### Architecture Diagram\n{diagram}")
    
    # Add comparison table if relevant
    table = _generate_comparison_table(query, domain)
    if table:
        enhanced_parts.append(f"\n\n### Comparison\n{table}")
    
    # Add code example if relevant
    code = _generate_code_example(query, domain)
    if code:
        enhanced_parts.append(f"\n\n### Implementation Example\n{code}")
    
    return "\n".join(enhanced_parts)


def _public_chat_payload(result: WorkflowResponse, original_query: str = "") -> dict:
    """Build a UI-safe dict from a `WorkflowResponse`."""
    raw = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    
    # Get the raw response text
    raw_response = raw.get("response", "") or ""
    
    # Enhance technical responses with the original query
    enhanced_response = _enhance_technical_response(sanitize_text(raw_response), original_query)
    
    public = {
        "response": enhanced_response,
        "intent": {
            "type": (raw.get("intent") or {}).get("intent"),
            "confidence": (raw.get("intent") or {}).get("confidence"),
        },
        "router_decision": {
            "route": (raw.get("router_decision") or {}).get("route"),
            "confidence": (raw.get("router_decision") or {}).get("confidence"),
            "used_memory": bool((raw.get("router_decision") or {}).get("requires_memory")),
            "used_tools": bool((raw.get("router_decision") or {}).get("requires_tools")),
            "used_rag": bool((raw.get("router_decision") or {}).get("requires_rag")),
            "used_graph": bool((raw.get("router_decision") or {}).get("requires_graph")),
        },
        "metadata": {
            "execution_time_ms": (raw.get("metadata") or {}).get("execution_time_ms"),
            "tokens": {
                "prompt": (raw.get("metadata") or {}).get("total_prompt_tokens"),
                "rag": (raw.get("metadata") or {}).get("rag_tokens"),
                "memory": (raw.get("metadata") or {}).get("memory_tokens"),
                "tools": (raw.get("metadata") or {}).get("tool_tokens"),
                "graph": (raw.get("metadata") or {}).get("graph_tokens"),
            },
        },
    }
    chunks = (raw.get("metadata") or {}).get("retrieved_chunks")
    if isinstance(chunks, list):
        public["metadata"]["retrieved_chunks"] = len(chunks)
    return public


# ============================================================
# In-Memory Chat History Store
# ============================================================

_chat_history: Dict[str, List[Dict[str, Any]]] = {}

# JSON file persistence for chat history across server restarts
_CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chat_history.json")


def _save_chat_history() -> None:
    try:
        os.makedirs(os.path.dirname(_CHAT_HISTORY_FILE), exist_ok=True)
        with open(_CHAT_HISTORY_FILE, "w") as f:
            json.dump(_chat_history, f, indent=2, default=str)
    except Exception as exc:
        logger.warning(f"Failed to save chat history to file: {exc}")


def _load_chat_history() -> None:
    try:
        if not os.path.exists(_CHAT_HISTORY_FILE):
            return
        with open(_CHAT_HISTORY_FILE) as f:
            data = json.load(f)
        _chat_history.clear()
        _chat_history.update(data)
        logger.info(f"Loaded chat history from file ({sum(len(v) for v in data.values())} entries)")
    except Exception as exc:
        logger.warning(f"Failed to load chat history from file: {exc}")


# Load persisted chat history on startup
_load_chat_history()


async def _load_file_attachments(file_ids: List[str], image_ids: List[str]) -> str:
    """
    Loads uploaded file content (text extraction, image descriptions, audio transcripts)
    and returns a formatted context string to prepend to the user query.
    """
    if not file_ids and not image_ids:
        return ""

    from app.database.postgres import postgres_manager
    from app.repositories.postgres.document_file_repository import DocumentFileRepository as _FileRepo
    all_ids = list(set(file_ids + image_ids))
    context_parts = []
    seen_texts = set()

    async for session in postgres_manager.get_session():
        repo = _FileRepo(session=session)
        for fid in all_ids:
            try:
                doc_file = await repo.get(fid)
                if not doc_file:
                    continue
                text = doc_file.extracted_text or ""
                if not text:
                    continue
                
                # Truncate extremely large texts just in case (e.g., limit each file to ~15k chars)
                text = text[:15000]

                if text in seen_texts:
                    continue
                seen_texts.add(text)

                context_parts.append(f"[Attachment: {doc_file.filename} ({doc_file.mime_type})]\n{text}")
            except Exception as e:
                logger.error(f"Failed to load attachment {fid}: {e}")
        break  # Just need one DB session

    if not context_parts:
        return ""
    
    return "\n\n---\n\n".join(context_parts)


async def store_chat_history(
    user_id: str,
    query: str,
    response: str,
    route_type: str = "UNKNOWN",
    execution_time_ms: float = 0.0,
    tokens_used: int = 0,
    conversation_id: str = "default",
):
    """Store a chat interaction in MongoDB and in-memory history."""
    from datetime import datetime as dt
    now = dt.utcnow()
    entry_id = f"hist-{uuid.uuid4().hex[:12]}"

    # Store in-memory
    if user_id not in _chat_history:
        _chat_history[user_id] = []
    
    entry = {
        "id": entry_id,
        "user_id": user_id,
        "query": query,
        "response": response,
        "route_type": route_type,
        "execution_time_ms": execution_time_ms,
        "tokens_used": tokens_used,
        "conversation_id": conversation_id,
        "timestamp": now.isoformat(),
    }
    _chat_history[user_id].append(entry)
    if len(_chat_history[user_id]) > 1000:
        _chat_history[user_id] = _chat_history[user_id][-1000:]
    _save_chat_history()

    # Persist to MongoDB
    try:
        from app.database.mongodb import mongo_manager as _mm
        coll = _mm.get_collection("chat_history")
        if coll is not None:
            await coll.insert_one(entry)
        messages_coll = _mm.get_collection("messages")
        if messages_coll is not None:
            await messages_coll.insert_one({
                "id": f"msg-{uuid.uuid4().hex[:12]}",
                "conversation_id": conversation_id,
                "role": "user",
                "content": query,
                "created_at": now,
            })
            await messages_coll.insert_one({
                "id": f"msg-{uuid.uuid4().hex[:12]}",
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": response,
                "created_at": now,
            })
        # Update conversation last_active
        conv_coll = _mm.get_collection("conversations")
        if conv_coll is not None:
            await conv_coll.update_one(
                {"id": conversation_id},
                {"$set": {"updated_at": now, "last_active": now},
                 "$inc": {"message_count": 2}},
            )
    except Exception as exc:
        logger.debug(f"MongoDB chat history storage skipped ({exc}).")
    
    await audit_log(user_id, "history_store", "chat", {"query_length": len(query)}, None, True)


async def get_user_chat_history(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Retrieve paginated chat history for a user from the in-memory store."""
    entries = _chat_history.get(user_id, [])
    return list(reversed(entries))[offset:offset + limit]


async def get_user_conversations(user_id: str) -> List[Dict[str, Any]]:
    """Group chat history by conversation_id and return conversation summaries."""
    entries = _chat_history.get(user_id, [])
    groups: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        cid = entry.get("conversation_id", "default")
        if cid not in groups:
            groups[cid] = {
                "id": cid,
                "title": entry["query"],
                "last_message": entry["query"],
                "updated_at": entry["timestamp"],
                "message_count": 0,
            }
        else:
            # Keep the first query as the title
            groups[cid]["last_message"] = entry["query"]
            groups[cid]["updated_at"] = entry["timestamp"]
        groups[cid]["message_count"] += 1  # Each entry = user+assistant pair
    # Return reverse chronological (most recent first)
    result = sorted(groups.values(), key=lambda c: c["updated_at"], reverse=True)
    return result


# ============================================================
# Chat API Endpoints
# ============================================================

@router.post("/message", response_model=APIResponse[dict], summary="Send Chat Message (Alias)")
@router.post("/query", response_model=APIResponse[dict], summary="Process Chat Query via Orchestration")
async def process_chat_query(
    payload: ChatQueryRequest,
    request_id: str = Depends(get_request_id),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    """
    Sends the user query through the LangGraph Orchestration Pipeline and returns
    complete reasoning, routing, and response metadata.
    Supports file attachments (PDF, DOCX, image, audio) referenced by file_ids.
    """
    user_id = current_user.id if current_user else (payload.user_id or "default")
    conversation_id = payload.conversation_id or "default"
    
    logger.info(f"Chat API processing query: '{payload.query[:50]}...' [Session: {conversation_id}, User: {user_id}]")
    
    # Guardrail: Validate input safety
    if settings.guardrails and settings.guardrails.enabled:
        input_check = guardrail_validator.validate_input(payload.query)
        if not input_check.passed:
            logger.warning(f"Input guardrail blocked query: {input_check.reason}")
            return success_response(
                data={"response": "I apologize, but I'm unable to process this request. Please rephrase your query and try again.", "guardrail_triggered": True, "reason": input_check.reason},
                message="Request blocked by safety guardrails",
                request_id=request_id,
            )
        logger.debug(f"Input passed guardrails: {input_check.details}")
    
    # Rate limiting
    if settings.guardrails and settings.guardrails.enabled:
        rate_check = check_rate_limit(
            user_id,
            per_minute=settings.guardrails.rate_limit_per_minute,
            per_hour=settings.guardrails.rate_limit_per_hour
        )
        if not rate_check.allowed:
            logger.warning(f"Rate limit exceeded for user {user_id}: {rate_check.limit_type} limit")
            return success_response(
                data={"response": "Too many requests. Please wait before trying again.", "rate_limited": True, "retry_after_seconds": int(rate_check.reset_in_seconds)},
                message="Rate limit exceeded",
                request_id=request_id,
            )
    
    # Load file attachments if any
    attachment_context = await _load_file_attachments(payload.file_ids or [], payload.image_ids or [])
    if attachment_context:
        logger.info(f"Loaded {len(payload.file_ids or []) + len(payload.image_ids or [])} attachment(s) for context")

    try:
        result: WorkflowResponse = await orchestration_pipeline.process_query(
            user_query=payload.query,
            conversation_id=conversation_id,
            user_id=user_id,
            file_context=attachment_context
        )
    except Exception as process_exc:
        logger.error(f"Chat processing failed: {type(process_exc).__name__}: {process_exc}", exc_info=True)
        return success_response(
            data={"response": f"I apologize, but I encountered an issue processing your request. Please try again."},
            message=f"Processing error: {type(process_exc).__name__}",
            request_id=request_id,
        )
    
    # Guardrail: Validate output safety
    if settings.guardrails and settings.guardrails.enabled and result.response:
        output_check = guardrail_validator.validate_output(result.response)
        if not output_check.passed:
            logger.warning(f"Output guardrail blocked response: {output_check.reason}")
            result.response = "I apologize, but I'm unable to provide that response. Please try a different query."
        else:
            result.response = output_check.filtered_output
            logger.debug(f"Output passed guardrails: {output_check.details}")
    
    public_payload = _public_chat_payload(result, original_query=payload.query)
    
    # Store history for authenticated users
    if current_user:
        await store_chat_history(
            user_id=current_user.id,
            query=payload.query,
            response=result.response or "",
            route_type=result.router_decision.route.value if result.router_decision else "UNKNOWN",
            execution_time_ms=result.metadata.execution_time_ms if result.metadata else 0,
            tokens_used=result.metadata.total_prompt_tokens if result.metadata else 0,
            conversation_id=conversation_id,
        )
        # Store conversation turn in memory pipeline for follow-up context
        await memory_pipeline.process_turn(
            user_query=payload.query,
            ai_response=result.response or "",
            user_id=current_user.id,
            conversation_id=conversation_id,
        )
    
    return success_response(
        data=public_payload,
        message="Query processed successfully via LangGraph orchestration",
        request_id=request_id,
    )


@router.post("/stream", summary="Stream Chat Response via Server-Sent Events (SSE)")
async def stream_chat_query(
    payload: ChatQueryRequest,
    request_id: str = Depends(get_request_id),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
):
    """
    Streams the chat response token-by-token over Server-Sent Events,
    while emitting lightweight status events showing real-time LangGraph node progression.
    """
    user_id = current_user.id if current_user else (payload.user_id or "default")
    conversation_id = payload.conversation_id or "default"
    
    logger.info(f"SSE Chat API streaming query: '{payload.query[:50]}...' [Session: {conversation_id}, User: {user_id}]")
    
    # Guardrail: Validate input safety before processing
    if settings.guardrails and settings.guardrails.enabled:
        input_check = guardrail_validator.validate_input(payload.query)
        if not input_check.passed:
            logger.warning(f"SSE Input guardrail blocked query: {input_check.reason}")
            async def blocked_generator() -> AsyncGenerator[str, None]:
                yield "event: error\ndata: " + json.dumps({"error": "Request blocked by safety guardrails", "reason": input_check.reason}) + "\n\n"
            return StreamingResponse(blocked_generator(), media_type="text/event-stream")
    
    # Rate limiting
    if settings.guardrails and settings.guardrails.enabled:
        rate_check = check_rate_limit(
            user_id,
            per_minute=settings.guardrails.rate_limit_per_minute,
            per_hour=settings.guardrails.rate_limit_per_hour
        )
        if not rate_check.allowed:
            logger.warning(f"SSE Rate limit exceeded for user {user_id}: {rate_check.limit_type} limit")
            async def rate_limited_generator() -> AsyncGenerator[str, None]:
                yield "event: error\ndata: " + json.dumps({"error": "Rate limit exceeded", "retry_after_seconds": int(rate_check.reset_in_seconds)}) + "\n\n"
            return StreamingResponse(rate_limited_generator(), media_type="text/event-stream")
    
    attachment_context = await _load_file_attachments(payload.file_ids or [], payload.image_ids or [])
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            yield "event: step\ndata: " + json.dumps({
                "node": "intent_analysis",
                "status": "RUNNING",
                "label": "Analyzing Query Intent"
            }) + "\n\n"
            await asyncio.sleep(0.03)
            
            # Start background task to allow for keep-alive pings preventing 502 proxy timeouts
            task = asyncio.create_task(
                orchestration_pipeline.process_query(
                    user_query=payload.query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    file_context=attachment_context
                )
            )
            
            # Yield ping events every 15 seconds while waiting
            while not task.done():
                try:
                    # shield() prevents the task from being cancelled if wait_for times out
                    await asyncio.wait_for(asyncio.shield(task), timeout=15.0)
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
            
            result: WorkflowResponse = task.result()
            
            # Guardrail: Validate output safety
            if settings.guardrails and settings.guardrails.enabled and result.response:
                output_check = guardrail_validator.validate_output(result.response)
                if not output_check.passed:
                    logger.warning(f"SSE Output guardrail blocked response: {output_check.reason}")
                    result.response = "I apologize, but I'm unable to provide that response. Please try a different query."
                else:
                    result.response = output_check.filtered_output
            
            yield "event: step\ndata: " + json.dumps({
                "node": "routing",
                "status": "COMPLETED",
                "label": f"Routed via {(result.router_decision.route.value if result.router_decision else 'DIRECT_LLM')}"
            }) + "\n\n"
            await asyncio.sleep(0.03)
            
            public = _public_chat_payload(result, original_query=payload.query)
            response_text = public["response"]
            
            yield "event: step\ndata: " + json.dumps({
                "node": "llm_generation",
                "status": "RUNNING",
                "label": "Generating Response via Groq LLM"
            }) + "\n\n"
            await asyncio.sleep(0.03)
            
            words = response_text.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i + 3]) + (" " if i + 3 < len(words) else "")
                yield "event: token\ndata: " + json.dumps({"text": chunk}) + "\n\n"
                await asyncio.sleep(0.015)
            
            # Store history for authenticated users
            if current_user:
                await store_chat_history(
                    user_id=current_user.id,
                    query=payload.query,
                    response=result.response or "",
                    route_type=result.router_decision.route.value if result.router_decision else "UNKNOWN",
                    execution_time_ms=result.metadata.execution_time_ms if result.metadata else 0,
                    tokens_used=result.metadata.total_prompt_tokens if result.metadata else 0,
                    conversation_id=conversation_id,
                )
                await memory_pipeline.process_turn(
                    user_query=payload.query,
                    ai_response=result.response or "",
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                )
            
            yield "event: complete\ndata: " + json.dumps({
                "response": public["response"],
                "intent": public["intent"],
                "router_decision": public["router_decision"],
                "metadata": public["metadata"],
            }) + "\n\n"
        except Exception as exc:
            logger.error(f"SSE Streaming failure: {exc}", exc_info=True)
            yield "event: error\ndata: " + json.dumps({"error": str(exc)}) + "\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{user_id}", response_model=APIResponse[list], summary="Get User Chat History")
async def get_chat_history(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: UserInDB = Depends(get_current_user),
    request_id: str = Depends(get_request_id),
):
    """Retrieve paginated chat history for the authenticated user."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own chat history"
        )
    
    history = await get_user_chat_history(user_id, limit=page_size, offset=(page - 1) * page_size)
    
    return success_response(
        data=history,
        message=f"Retrieved {len(history)} chat history entries",
        request_id=request_id,
    )


@router.get("/conversations", response_model=APIResponse[list], summary="Get User Conversations")
async def get_conversations(
    current_user: UserInDB = Depends(get_current_user),
    request_id: str = Depends(get_request_id),
):
    """Retrieve conversation summaries grouped by conversation_id."""
    conversations = await get_user_conversations(current_user.id)

    return success_response(
        data=conversations,
        message=f"Retrieved {len(conversations)} conversations",
        request_id=request_id,
    )


class SaveConversationRequest(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]


@router.post("/conversations/save", summary="Save Full Conversation to History")
async def save_conversation(
    payload: SaveConversationRequest,
    current_user: UserInDB = Depends(get_current_user),
    request_id: str = Depends(get_request_id),
):
    """Save an entire conversation to user history as paired entries."""
    user_id = current_user.id
    cid = payload.conversation_id
    now = datetime.utcnow().isoformat()

    if user_id not in _chat_history:
        _chat_history[user_id] = []

    first_query = ""
    user_text = ""
    for msg in payload.messages:
        sender = msg.get("sender")
        text = msg.get("text", "")
        if not text:
            continue
        if sender == "user":
            user_text = text
            if not first_query:
                first_query = text
        elif sender == "assistant" and user_text:
            entry = {
                "id": f"hist-{uuid.uuid4().hex[:12]}",
                "user_id": user_id,
                "query": user_text,
                "response": text,
                "route_type": "MANUAL_SAVE",
                "execution_time_ms": 0,
                "tokens_used": 0,
                "conversation_id": cid,
                "timestamp": now,
            }
            _chat_history[user_id].append(entry)
            user_text = ""

    _save_chat_history()

    if first_query:
        logger.info(f"Conversation '{cid}' saved for user {user_id} (starts with: {first_query[:50]})")

    return success_response(
        data={"conversation_id": cid, "message_count": len(payload.messages)},
        message="Conversation saved successfully",
        request_id=request_id,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=APIResponse[list], summary="Get Conversation Messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_user),
    request_id: str = Depends(get_request_id),
):
    """Retrieve all messages for a given conversation."""
    entries = _chat_history.get(current_user.id, [])
    msgs = [e for e in entries if e.get("conversation_id") == conversation_id]
    formatted = []
    for e in msgs:
        if e.get("query"):
            formatted.append({"sender": "user", "text": e["query"], "id": f"user-{e['id']}"})
        if e.get("response"):
            formatted.append({"sender": "assistant", "text": e["response"], "id": f"asst-{e['id']}"})

    return success_response(
        data=formatted,
        message=f"Retrieved {len(formatted)} messages",
        request_id=request_id,
    )


@router.delete("/conversations/{conversation_id}", summary="Delete a Single Conversation")
async def delete_conversation(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_user),
    request_id: str = Depends(get_request_id),
):
    """Delete all entries for a given conversation_id for the authenticated user."""
    user_id = current_user.id
    if user_id not in _chat_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    before = len(_chat_history[user_id])
    _chat_history[user_id] = [
        e for e in _chat_history[user_id]
        if e.get("conversation_id") != conversation_id
    ]
    removed = before - len(_chat_history[user_id])

    if removed == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    _save_chat_history()

    logger.info(f"Conversation '{conversation_id}' deleted for user {user_id} ({removed} entries removed)")

    return success_response(
        data={"conversation_id": conversation_id, "removed_entries": removed},
        message="Conversation deleted successfully",
        request_id=request_id,
    )


@router.delete("/history", summary="Clear User Chat History")
async def clear_chat_history(
    current_user: UserInDB = Depends(get_current_user),
    request_id: str = Depends(get_request_id),
):
    """Clear all chat history for the authenticated user."""
    user_id = current_user.id
    if user_id in _chat_history:
        _chat_history[user_id] = []
        _save_chat_history()
    
    await audit_log(current_user.id, "history_clear", "history", {}, None, True)
    
    return success_response(
        data={},
        message="Chat history cleared successfully",
        request_id=request_id,
    )
