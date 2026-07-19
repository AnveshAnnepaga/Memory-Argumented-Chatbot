# Vyron AI - Technical Documentation

**Version:** 0.1.0 | **Build:** 2026.07.01 | **Status:** Production Ready

---

## Table of Contents
1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [API Endpoints](#4-api-endpoints)
5. [Core Components](#5-core-components)
6. [Data Storage](#6-data-storage)
7. [Configuration](#7-configuration)
8. [Deployment](#8-deployment)
9. [Development Setup](#9-development-setup)
10. [Security](#10-security)

---

## 1. Overview

**Vyron AI** is an intelligent, modular, and decoupled AI Assistant Platform that seamlessly integrates:
- Long-term memory persistence
- Knowledge graph reasoning
- Real-time data retrieval
- Hybrid RAG (Retrieval-Augmented Generation)

The platform provides context-aware, highly accurate responses through a lightning-fast modern interface.

### Live Demo
**https://vyronai-six.vercel.app**

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Next.js 15 Frontend (Port 3000)                     │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │   │ Chat Studio  │  │  Dashboard   │  │   Zustand    │              │   │
│  │   │   (/chat)    │  │  (/history)  │  │   + Query    │              │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │ REST / SSE
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NGINX Reverse Proxy (Port 80)                        │
│              Routes: /api/v1/* → Backend, /* → Frontend                      │
│              Features: SSE Streaming, Gzip Compression                      │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND (Port 8000)                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         API Router Layer                               │   │
│  │                   /api/v1/* → Versioned Endpoints                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   LangGraph StateGraph Engine                          │   │
│  │                      "The Brain" - Orchestration                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│          │                    │                    │                    │    │
│          ▼                    ▼                    ▼                    ▼    │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Hybrid RAG   │  │    GraphRAG      │  │  LTMemory    │  │   Tools    │  │
│  │   Pipeline   │  │     Engine       │  │    System    │  │   System   │  │
│  └──────────────┘  └──────────────────┘  └──────────────┘  └────────────┘  │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│     Pinecone      │      │      Neo4j        │      │   PostgreSQL      │
│   (Vectors)       │      │   (Knowledge)     │      │   (Profiles)      │
│                   │      │                   │      │                   │
│  BAAI/bge-large   │      │  Graph Entities   │      │  User Memory      │
│  1024-d Embedding │      │  & Relationships │      │  & Episodic Logs  │
└───────────────────┘      └───────────────────┘      └───────────────────┘
```

### 2.2 Data Flow Diagram

```
User Query
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                           │
│                    (SSE Stream Reader)                         │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ HTTP/REST
┌──────────────────────────────────────────────────────────────┐
│                    NGINX Proxy                                │
│              (Chunked Transfer Encoding)                      │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│              FastAPI /api/v1/chat/stream                       │
│                    (SSE Endpoint)                              │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│              LangGraph StateGraph "The Brain"                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Router (Intent Classification)        │ │
│  │         Determines: RAG, GraphRAG, Memory, Tools          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                   │
│    ┌───────────────────────┼───────────────────────────────┐ │
│    │                       │                               │ │
│    ▼                       ▼                               ▼ │
│ ┌────────┐          ┌────────────┐                   ┌──────────┐
│ │  RAG   │          │  GraphRAG  │                   │  Memory  │
│ │ (Dense │◄────────►│  (Neo4j)   │                   │ (Postgres)│
│ │ BM25)  │          │            │                   │          │
│ └────────┘          └────────────┘                   └──────────┘
│    │                                                                   │
│    └───────────────────────┬───────────────────────────┘
│                            ▼
│               ┌────────────────────────┐
│               │    LLM (NVIDIA/Groq)    │
│               │  (Fallback Chain)       │
│               └────────────────────────┘
│                            │
│                            ▼
│               ┌────────────────────────┐
│               │  SSE Response Stream   │
│               └────────────────────────┘
```

---

## 3. Technology Stack

### 3.1 Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | Async REST API |
| Language | Python 3.11 | Core application |
| Orchestration | LangGraph StateGraph | Conditional DAG reasoning |
| Vector DB | Pinecone | Dense 1024-d embeddings |
| Graph DB | Neo4j 5 | Knowledge graph reasoning |
| Relational DB | PostgreSQL 16 | User profiles, episodic memory |
| Document Store | MongoDB | Knowledge document storage |
| LLM Primary | NVIDIA NIM | Llama 3.3 Nemotron 49B |
| LLM Fallback | Groq | Llama 3.1 8B Instant |

### 3.2 Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 15 | React 19 App Router |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS 4 | Modern glassmorphism UI |
| State | Zustand | Client-side state management |
| Data Fetching | TanStack Query | Server state caching |
| Animation | Framer Motion | Micro-interactions |

### 3.3 Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Reverse Proxy | NGINX | Load balancing, SSE streaming |
| Container | Docker | Application packaging |
| Orchestration | Docker Compose | Multi-service deployment |
| Platform | Railway | Cloud deployment |
| Platform | Vercel | Frontend deployment |

---

## 4. API Endpoints

### 4.1 Endpoint Overview

| Prefix | Module | Description |
|--------|--------|-------------|
| `/api/v1/health` | Health | System health checks |
| `/api/v1/auth` | Auth | Authentication |
| `/api/v1/chat` | Chat | Chat and streaming |
| `/api/v1/memory` | Memory | Long-term memory |
| `/api/v1/knowledge` | Knowledge | Knowledge base |
| `/api/v1/ingestion` | Ingestion | Document processing |
| `/api/v1/graph` | Graph | Graph queries |
| `/api/v1/retrieval` | Retrieval | Direct retrieval |
| `/api/v1/tools` | Tools | Tool execution |
| `/api/v1/evaluation` | Evaluation | Evaluation metrics |
| `/api/v1/monitoring` | Monitoring | System metrics |
| `/api/v1/admin` | Admin | Admin operations |
| `/api/v1/upload` | Upload | File uploads |

### 4.2 Key Endpoints

#### Chat
- `POST /api/v1/chat` - Send chat message
- `POST /api/v1/chat/stream` - SSE streaming response
- `GET /api/v1/chat/history` - Get chat history

#### Memory
- `GET /api/v1/memory/user/{user_id}` - Get user memories
- `POST /api/v1/memory` - Store memory
- `DELETE /api/v1/memory/{memory_id}` - Delete memory

#### Knowledge
- `GET /api/v1/knowledge` - List knowledge items
- `POST /api/v1/knowledge` - Add knowledge item
- `GET /api/v1/knowledge/search` - Search knowledge

#### Graph
- `GET /api/v1/graph/query` - Execute Cypher query
- `POST /api/v1/graph/entity` - Add entity
- `GET /api/v1/graph/neighbors` - Get node neighbors

### 4.3 Monitoring
- `GET /health` - Health check (container healthcheck)
- `GET /api/v1/monitoring/metrics` - System metrics
- `GET /api/v1/monitoring/logs` - Application logs

---

## 5. Core Components

### 5.1 LangGraph StateGraph Engine ("The Brain")

The orchestration engine routes queries through 5 distinct pipelines:

```
Intent Classification → [DIRECT_LLM | HYBRID_RAG | GRAPH_RAG | MEMORY_ENHANCED | TOOLS_ENHANCED]
```

**Features:**
- Conditional DAG routing based on intent confidence
- LLM fallback chain (NVIDIA → Groq → Mock)
- Server-Sent Events (SSE) streaming
- Intermediate tool thought visualization

### 5.2 Hybrid RAG Pipeline

**Components:**
1. **Dense Retrieval** - Pinecone BAAI/bge-large-en-v1.5 (1024 dimensions)
2. **Sparse Retrieval** - BM25 keyword search
3. **Fusion** - Reciprocal Rank Fusion (RRF)

**Configuration:**
```python
top_k: 5
similarity_threshold: 0.75
bm25_weight: 0.4
dense_weight: 0.6
```

### 5.3 GraphRAG Engine

- Neo4j Cypher query execution
- Multi-hop entity traversal
- Knowledge graph construction from documents
- Entity relationship extraction

### 5.4 Long-Term Memory System

- PostgreSQL-based user profiles
- Ebbinghaus forgetting curve implementation
- Semantic fact extraction
- Episodic conversation logging

### 5.5 Tool Framework

Decoupled tool execution:
- **Web Search** - Real-time web queries
- **SQL Executor** - Database queries
- **Calculator** - Mathematical operations
- **Cypher** - Graph database queries

---

## 6. Data Storage

### 6.1 PostgreSQL (Profiles & Episodic Memory)

```yaml
Host: POSTGRES_HOST (default: localhost)
Port: 5432
Database: vyron_db
Purpose: User profiles, conversation logs, semantic memories
```

### 6.2 Neo4j (Knowledge Graph)

```yaml
URI: bolt://localhost:7687
Database: neo4j
Purpose: Graph entities, relationships, multi-hop queries
```

### 6.3 Pinecone (Vector Storage)

```yaml
Environment: us-east-1
Index: chatbot-vectors
Dimension: 1024
Namespace: default
Purpose: Dense embeddings, semantic search
```

### 6.4 MongoDB (Document Store)

```yaml
URI: mongodb://localhost:27017
Database: chatbot_memory
Purpose: Knowledge documents, file storage
```

---

## 7. Configuration

### 7.1 Environment Variables

Critical configuration (see `.env.example`):

```env
# Application
APP_NAME="Memory-Augmented Chatbot"
APP_VERSION="0.1.0"
APP_ENV="production"
DEBUG=false
SECRET_KEY="your-super-secret-key"

# AI Models
CHAT_MODEL="nvidia/llama-3.3-nemotron-super-49b-v1.5"
EMBEDDING_MODEL="BAAI/bge-large-en-v1.5"

# API Keys
NVIDIA_API_KEY="your-nvidia-key"
GROQ_API_KEY="your-groq-key"
PINECONE_API_KEY="your-pinecone-key"

# Storage
POSTGRES_URL="postgresql://user:pass@host:5432/db"
NEO4J_URI="bolt://host:7687"
NEO4J_PASSWORD="your-password"
MONGODB_URI="mongodb://localhost:27017"
```

### 7.2 Feature Flags

```env
ENABLE_MEMORY=true
ENABLE_GRAPH=true
ENABLE_TOOLS=true
ENABLE_HYBRID_RAG=true
ENABLE_RERANKER=true
ENABLE_EVALUATION=false
```

---

## 8. Deployment

### 8.1 Docker Compose (Production Stack)

```bash
docker compose up -d --build
```

**Services:**
| Service | Port | Description |
|---------|------|-------------|
| nginx | 80 | Reverse proxy |
| frontend | 3000 | Next.js app |
| backend | 8000 | FastAPI app |

### 8.2 Railway Deployment

1. Connect GitHub repository
2. Railway auto-detects `Dockerfile`
3. Set environment variables in dashboard
4. Deploy with health check on `/health`

**Config:** `railway.json`
```json
{
  "build": { "builder": "DOCKERFILE" },
  "deploy": { "port": 8000, "healthcheckPath": "/health" }
}
```

### 8.3 Vercel Deployment (Frontend)

1. Import `frontend/` directory
2. Set environment variables:
   - `NEXT_PUBLIC_API_BASE_URL`
3. Deploy automatically

---

## 9. Development Setup

### 9.1 Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### 9.2 Backend

```bash
pip install -r requirements.txt
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 9.3 Frontend

```bash
cd frontend
npm install
npm run dev
```

### 9.4 Full Stack (Docker)

```bash
docker compose up -d
```

---

## 10. Security

### 10.1 Secrets Management
- Never commit `.env` files
- Use environment variables for all secrets
- Rotate API keys regularly

### 10.2 API Security
- CORS configured for specific origins
- Request ID tracking for audit logs
- Rate limiting (recommended for production)

### 10.3 Database Security
- Use strong passwords
- Enable SSL connections in production
- Regular backups

---

## Appendix A: Project Structure

```
Memory-Argumented-Chatbot/
├── .env                         # Secrets (git-ignored)
├── .env.example                 # Template for configuration
├── main.py                      # Backend entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Backend container
├── docker-compose.yml           # Full stack deployment
├── railway.json                 # Railway config
├── vercel.json                  # Vercel config
│
├── app/                         # FastAPI application
│   ├── main.py                 # App factory
│   ├── core/                   # Settings & config
│   ├── api/v1/                 # API routes
│   ├── orchestration/          # LangGraph brain
│   ├── rag/                   # Hybrid RAG
│   ├── memory/                 # LTMemory
│   ├── graph/                 # GraphRAG
│   └── tools/                 # Tool framework
│
├── frontend/                   # Next.js application
│   ├── package.json
│   ├── src/                   # React components
│   └── Dockerfile             # Frontend container
│
└── nginx/
    └── nginx.conf             # Reverse proxy config
```

## Appendix B: API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

**Document Version:** 1.0.0
**Last Updated:** July 2026
**Author:** Vyron AI Team