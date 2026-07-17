# File: app/tech_content/enhancer.py
"""
Technical Content Enhancer

Enhances LLM responses with Mermaid diagrams, comparison tables, code examples,
and technical specifications for technical queries.
"""
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from app.utils.sanitizer import sanitize_text


class TechnicalDomain(str, Enum):
    """Technical domains for content enhancement."""
    ARCHITECTURE = "architecture"
    API = "api"
    DATABASE = "database"
    ML = "ml"
    DEVOPS = "devops"
    FRONTEND = "frontend"
    SECURITY = "security"
    ALGORITHM = "algorithm"
    CLOUD = "cloud"
    TESTING = "testing"
    LANGGRAPH = "langgraph"
    GENERAL = "general"


@dataclass
class TechnicalContent:
    """Enhanced technical content package."""
    original_response: str
    mermaid_diagram: Optional[str] = None
    comparison_table: Optional[str] = None
    code_example: Optional[str] = None
    specifications: Optional[str] = None
    domain: TechnicalDomain = TechnicalDomain.GENERAL


# ============================================================
# Domain Detection
# ============================================================

_DOMAIN_KEYWORDS = {
    TechnicalDomain.ARCHITECTURE: [
        "architecture", "design pattern", "microservice", "system design",
        "scalability", "distributed system", "monolith", "service mesh"
    ],
    TechnicalDomain.API: [
        "api", "rest", "graphql", "grpc", "endpoint", "fastapi", "flask",
        "django", "express", "openapi", "swagger", "webhook"
    ],
    TechnicalDomain.DATABASE: [
        "database", "sql", "postgresql", "mysql", "mongodb", "redis",
        "query", "index", "transaction", "migration", "orm", "prisma",
        "sqlalchemy", "dynamodb", "cassandra"
    ],
    TechnicalDomain.ML: [
        "machine learning", "deep learning", "neural network", "transformer",
        "llm", "embedding", "rag", "fine-tuning", "training", "inference",
        "pytorch", "tensorflow", "huggingface", "langchain", "langgraph"
    ],
    TechnicalDomain.DEVOPS: [
        "docker", "kubernetes", "ci/cd", "deployment", "pipeline",
        "terraform", "ansible", "helm", "argocd", "jenkins", "gitlab ci",
        "github actions", "prometheus", "grafana"
    ],
    TechnicalDomain.FRONTEND: [
        "react", "vue", "next.js", "typescript", "css", "frontend",
        "ui", "component", "tailwind", "webpack", "vite", "redux", "zustand"
    ],
    TechnicalDomain.SECURITY: [
        "authentication", "authorization", "oauth", "jwt", "security",
        "encryption", "ssl", "tls", "rbac", "abac", "csrf", "xss",
        "penetration test", "vulnerability"
    ],
    TechnicalDomain.ALGORITHM: [
        "algorithm", "complexity", "big o", "sorting", "search",
        "dynamic programming", "graph algorithm", "tree", "heap"
    ],
    TechnicalDomain.CLOUD: [
        "aws", "azure", "gcp", "cloud", "serverless", "lambda",
        "cloudformation", "s3", "dynamodb", "rds", "ec2", "ecs", "eks"
    ],
    TechnicalDomain.TESTING: [
        "testing", "unit test", "integration test", "e2e test",
        "pytest", "jest", "mock", "coverage", "tdd", "bdd"
    ],
    TechnicalDomain.LANGGRAPH: [
        "langgraph", "langchain", "agent", "workflow", "state graph",
        "state machine", "agentic", "chain of thought", "react agent"
    ],
}


def detect_technical_domain(query: str) -> TechnicalDomain:
    """Detect technical domain from user query."""
    query_lower = query.lower()
    
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return domain
    
    return TechnicalDomain.GENERAL


# ============================================================
# Content Generators
# ============================================================

def generate_mermaid_diagram(query: str, domain: TechnicalDomain, response: str) -> Optional[str]:
    """Generate Mermaid diagram based on query domain and response."""
    query_lower = query.lower()
    
    # Architecture diagrams
    if domain == "architecture":
        if "microservice" in query.lower():
            return """```mermaid
graph TB
    Client[Client] --> Gateway[API Gateway]
    Gateway --> Auth[Auth Service]
    Gateway --> User[User Service]
    Gateway --> Order[Order Service]
    Gateway --> Payment[Payment Service]
    Gateway --> Inventory[Inventory Service]
    
    User --> DB1[(User DB)]
    Order --> DB2[(Order DB)]
    Payment --> DB3[(Payment DB)]
    Inventory --> DB4[(Inventory DB)]
    
    Order --> Queue[Message Queue]
    Payment --> Queue
    Inventory --> Queue
    
    Queue --> Notification[Notification Service]
    Queue --> Analytics[Analytics Service]
```"""
        elif "layer" in query.lower() or "layered" in query.lower():
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
```"""
    
    # API diagrams
    elif domain == "api":
        if "rest" in query.lower():
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
```"""
        elif "graphql" in query.lower():
            return """```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Schema as GraphQL Schema
    participant Resolvers
    participant DataSources
    
    Client->>Gateway: GraphQL Query
    Gateway->>Schema: Validate Query
    Schema->>Resolvers: Execute Resolvers
    Resolvers->>DataSources: Fetch Data
    DataSources-->>Resolvers: Data
    Resolvers-->>Gateway: Response
    Gateway-->>Client: GraphQL Response
```"""
    
    # Database diagrams
    elif domain == "database":
        if "index" in query.lower():
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
```"""
        elif "transaction" in query.lower():
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
```"""
    
    # LangGraph/LangChain diagrams
    elif domain == "langgraph" or "langgraph" in query.lower() or "langchain" in query.lower():
        if "workflow" in query.lower() or "graph" in query.lower() or "agent" in query.lower():
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
```"""
    
    # ML/AI diagrams
    elif domain == "ml":
        if "rag" in query.lower():
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
```"""
        elif "embedding" in query.lower():
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
```"""
    
    # DevOps diagrams
    elif domain == "devops":
        if "ci/cd" in query.lower() or "pipeline" in query.lower():
            return """```mermaid
graph LR
    Push[Code Push] --> CI[CI Pipeline]
    CI --> Test[Run Tests]
    Test --> Build[Build Image]
    Build --> Scan[Security Scan]
    Scan --> Staging[Deploy to Staging]
    Staging --> E2E[E2E Tests]
    E2E --> Approve{Manual Approve?}
    Approve -->|Yes| Prod[Deploy to Prod]
    Approve -->|No| Reject[Reject Deploy]
    
    style Push fill:#e1f5fe
    style Prod fill:#c8e6c9
    style Reject fill:#ffcdd2
```"""
    
    # Security diagrams
    elif domain == "security":
        if "oauth" in query.lower() or "jwt" in query.lower():
            return """```mermaid
sequenceDiagram
    participant User
    participant Client
    participant Auth as Auth Server
    participant Resource as Resource Server
    
    User->>Client: Clicks Login
    Client->>Auth: Redirect to /authorize
    Auth->>User: Login Consent
    User->>Auth: Credentials
    Auth->>Client: Redirect with Code
    Client->>Auth: Exchange Code for Tokens
    Auth->>Client: Access + Refresh Token
    Client->>Resource: Request with Access Token
    Resource->>Client: Protected Resource
```"""
    
    # Database/Algorithm general flowcharts
    elif "process" in query.lower() or "flow" in query.lower() or "workflow" in query.lower():
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
```"""
    
    return None


def generate_comparison_table(query: str, domain: TechnicalDomain) -> Optional[str]:
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
        
        elif "postgres" in query.lower() and "mongo" in query.lower():
            return """| Feature | PostgreSQL | MongoDB |
|---------|------------|---------|
| **Data Model** | Relational | Document |
| **Schema** | Fixed (ALTER TABLE) | Flexible |
| **ACID** | ✅ Full | ✅ (since 4.0) |
| **Joins** | ✅ Native | ⚠️ $lookup |
| **Scaling** | Vertical + Read replicas | Horizontal (sharding) |
| **JSON** | ✅ JSONB | ✅ Native |"""
        
        elif "django" in query_lower and "fastapi" in query_lower:
            return """| Feature | Django | FastAPI | Flask |
|---------|--------|---------|-------|
| **Type** | Full-stack | API-first | Micro |
| **Admin** | ✅ Built-in | ❌ | ❌ |
| **ORM** | ✅ Built-in | ❌ (use SQLAlchemy) | ❌ |
| **Auth** | ✅ Built-in | Manual | Manual |
| **Async** | ⚠️ Limited | ✅ Native | ⚠️ Limited |"""
    
    # Framework comparison general
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


def generate_code_example(query: str, domain: TechnicalDomain) -> Optional[str]:
    """Generate relevant code example for technical queries."""
    query_lower = query.lower()
    
    if "fastapi" in query_lower and ("dependency" in query_lower or "di" in query_lower or "depends" in query_lower):
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
    
    if "sqlalchemy" in query_lower and ("async" in query_lower or "session" in query_lower):
        return """```python
# SQLAlchemy Async Session Example
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_user_with_posts(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).options(selectinload(User.posts)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# Using in FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```
"""
    
    if "docker" in query_lower and ("compose" in query_lower or "dockerfile" in query_lower):
        return """```dockerfile
# Multi-stage Dockerfile for FastAPI
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/db
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=db
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
```"""
    
    if "redis" in query_lower and ("cache" in query_lower or "session" in query_lower):
        return """```python
# Redis Caching with FastAPI
import redis.asyncio as redis
from fastapi import Depends
from functools import wraps
import json

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

async def cache_get(key: str):
    data = await redis_client.get(key)
    return json.loads(data) if data else None

async def cache_set(key: str, value: dict, expire: int = 3600):
    await redis_client.setex(key, expire, json.dumps(value))

def cached(expire: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = await cache_get(key)
            if cached:
                return cached
            result = await func(*args, **kwargs)
            await cache_set(key, result, expire)
            return result
        return wrapper
    return decorator

# Usage
@app.get("/users/{user_id}")
@cached(expire=300)
async def get_user(user_id: int):
    return await db.get_user(user_id)
```
"""
    
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
      - name: app
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
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
            path: /health
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
    
    if "pytest" in query_lower and ("fixture" in query_lower or "async" in query_lower):
        return """```python
# pytest async fixtures and testing
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def async_session(async_engine):
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def async_client(async_session):
    async def override_get_db():
        yield async_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

# Test example
@pytest.mark.asyncio
async def test_create_user(async_client):
    response = await async_client.post("/users/", json={"email": "test@example.com", "name": "Test"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
```
"""
    
    if "websocket" in query_lower or "real-time" in query_lower or "sse" in query_lower:
        return """```python
# FastAPI WebSocket Example
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
```"""
    
    return None


def generate_specifications(query: str, domain: TechnicalDomain) -> Optional[str]:
    """Generate technical specifications table."""
    query_lower = query.lower()
    
    if domain == "api":
        return """| Aspect | Specification |
|--------|---------------|
| **Protocol** | HTTP/1.1, HTTP/2, HTTP/3 |
| **Data Format** | JSON (primary), XML, Protobuf |
| **Authentication** | JWT, OAuth 2.0, API Keys |
| **Rate Limiting** | Token bucket / Sliding window |
| **Versioning** | URL path (/v1/), Header, Query param |
| **Error Format** | RFC 7807 Problem Details |
| **Pagination** | Cursor-based (preferred), Offset |
| **Filtering** | Query params (?field=value) |
| **Sorting** | ?sort=field,-field |
| **Field Selection** | ?fields=id,name,email |"""
    
    if domain == "database":
        return """| Aspect | PostgreSQL | MongoDB | Redis |
|--------|------------|---------|-------|
| **Type** | Relational | Document | Key-Value |
| **ACID** | ✅ Full | ✅ (4.0+) | ⚠️ Limited |
| **Max Document/Row** | 1TB | 16MB | 512MB |
| **Concurrency** | MVCC | Document-level | Single-threaded |
| **Full-text Search** | ✅ tsvector | ✅ Atlas Search | ❌ |
| **Geospatial** | ✅ PostGIS | ✅ Native | ✅ Redis Geo |
| **Replication** | Streaming | Replica Sets | Master-Replica |"""
    
    if "spec" in query.lower() or "specification" in query.lower():
        if "api" in query.lower():
            return """| Aspect | OpenAPI 3.1 | GraphQL |
|--------|-------------|---------|
| **Type System** | JSON Schema | GraphQL SDL |
| **Versioning** | URL/Header/Query | Schema evolution |
| **Introspection** | OpenAPI Spec | Built-in |
| **Over-fetching** | Possible | Avoided |
| **Under-fetching** | Possible | Avoided |
| **Caching** | HTTP Cache | Normalized Cache |
| **Real-time** | Webhooks/SSE | Subscriptions |"""
    
    return None


# ============================================================
# Main Enhancement Function
# ============================================================

def enhance_technical_response(
    query: str,
    base_response: str,
    domain: Optional[TechnicalDomain] = None
) -> TechnicalContent:
    """
    Enhance a base LLM response with technical diagrams, tables, and code.
    
    Args:
        query: Original user query
        base_response: Base LLM response
        domain: Pre-detected domain (auto-detected if None)
    
    Returns:
        TechnicalContent with enhanced components
    """
    if domain is None:
        domain = detect_technical_domain(query)
    
    # Only enhance for technical domains
    if domain == TechnicalDomain.GENERAL:
        return TechnicalContent(original_response=base_response, domain=domain)
    
    # Generate enhanced components
    diagram = generate_mermaid_diagram(query, domain, base_response)
    table = generate_comparison_table(query, domain)
    code = generate_code_example(query, domain)
    specs = generate_specifications(query, domain)
    
    # Only add enhancements if they add value
    enhanced_parts = []
    
    if diagram:
        enhanced_parts.append(f"\n\n## Architecture Diagram\n{diagram}")
    
    if table:
        enhanced_parts.append(f"\n\n## Comparison\n{table}")
    
    if code:
        enhanced_parts.append(f"\n\n## Code Example\n{code}")
    
    if specs:
        enhanced_parts.append(f"\n\n## Technical Specifications\n{specs}")
    
    # Combine original response with enhancements
    enhanced_response = base_response
    if enhanced_parts:
        enhanced_response = base_response + "\n" + "\n".join(enhanced_parts)
    
    return TechnicalContent(
        original_response=base_response,
        enhanced_response=enhanced_response,
        mermaid_diagram=diagram,
        comparison_table=table,
        code_example=code,
        specifications=specs,
        domain=domain
    )


def format_enhanced_response(content: TechnicalContent) -> str:
    """Format enhanced content for display."""
    if content.domain == TechnicalDomain.GENERAL:
        return content.original_response
    
    parts = [content.original_response]
    
    if content.mermaid_diagram:
        parts.append(f"\n\n## 📐 Architecture Diagram\n{content.mermaid_diagram}")
    
    if content.comparison_table:
        parts.append(f"\n\n## ⚖️ Comparison\n{content.comparison_table}")
    
    if content.code_example:
        parts.append(f"\n\n## 💻 Code Example\n{content.code_example}")
    
    if content.specifications:
        parts.append(f"\n\n## 📋 Technical Specifications\n{content.specifications}")
    
    return "\n".join(parts)


# ============================================================
# Content Filtering
# ============================================================

def should_enhance(query: str) -> bool:
    """Determine if query should trigger technical enhancement."""
    technical_indicators = [
        "how to", "how does", "explain", "implement", "create", "build",
        "architecture", "design", "pattern", "best practice", "optimize",
        "compare", "vs", "versus", "difference", "trade-off",
        "code", "example", "snippet", "implementation", "tutorial",
        "api", "database", "database", "deployment", "docker", "kubernetes",
        "fastapi", "sqlalchemy", "pydantic", "redis", "postgresql",
        "langgraph", "langchain", "rag", "embedding", "vector"
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in technical_indicators)


# Export
__all__ = [
    "TechnicalDomain",
    "TechnicalContent",
    "detect_technical_domain",
    "generate_mermaid_diagram",
    "generate_comparison_table",
    "generate_code_example",
    "generate_specifications",
    "enhance_technical_response",
    "format_enhanced_response",
    "should_enhance",
]