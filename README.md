# Vyron AI

Vyron AI is an intelligent, modular, and decoupled AI Assistant Platform that seamlessly integrates long-term memory, knowledge graph reasoning, real-time data retrieval, and Hybrid RAG to provide context-aware, highly accurate responses in a lightning-fast modern interface.

**Live Demo:** [https://vyronai-six.vercel.app](https://vyronai-six.vercel.app)

---

## Table of Contents
1. [Architecture](#-architecture)
2. [Technology Stack](#-technology-stack)
3. [Core Components](#-core-components)
4. [API Endpoints](#-api-endpoints)
5. [Data Storage](#-data-storage)
6. [Configuration](#-configuration)
7. [Development Setup](#-development-setup)
8. [Deployment](#-deployment)
9. [Security](#-security)
10. [CI/CD](#-cicd)
11. [Roadmap](#-roadmap)

---

## 🏗️ Architecture

### System Architecture

```mermaid
graph TD
    subgraph Frontend["Next.js 15 Cyber UI Layer (Port 3000)"]
        ChatStudio["Chat Studio (/chat)<br/>SSE Stream Reader"]
        Dashboards["Dashboards (/history, /memory, /knowledge, /graph, /evaluation, /admin)"]
        ZustandStore["Zustand Store + TanStack Query Caching"]
    end

    subgraph ReverseProxy["Container & Network Proxy Layer"]
        NGINX["NGINX Reverse Proxy (Port 80)<br/>SSE Buffering Off & Chunked Transfer"]
    end

    subgraph Backend["FastAPI Backend Architecture Layer (Port 8000)"]
        Router["V1 Router Layer (/api/v1/*)"]
        Orchestration["LangGraph StateGraph Engine (The Brain)"]
        
        subgraph DecoupledModules["Independent Intelligence Modules"]
            HybridRAG["Hybrid RAG Pipeline<br/>Pinecone 1024-d + BM25 + RRF"]
            GraphRAG["GraphRAG Engine<br/>Neo4j Cypher Multi-Hop Traversal"]
            LTMemory["Long-Term Memory System<br/>PostgreSQL Profile & Ebbinghaus Curves"]
            ToolSystem["External Tool Framework<br/>WebSearch, SQL, Calculator, Cypher"]
            Observability["Evaluation & Observability Platform<br/>Ragas & DeepEval Read-Only Hooks"]
        end
    end

    subgraph Storage["Persistence & External Services"]
        PostgresDB[(PostgreSQL 16<br/>Profile & Episodic Logs)]
        Neo4jDB[(Neo4j 5 Graph<br/>Knowledge Entities & Edges)]
        PineconeCloud[(Pinecone Cloud<br/>BAAI/bge-large-en Vectors)]
        GroqLLM[("NVIDIA NIM / Groq Cloud API<br/>Llama 3.3 70B Versatile Inference")]
    end

    ChatStudio & Dashboards <==REST / SSE==> NGINX
    NGINX <==Proxy Pass==> Router
    Router --> Orchestration
    Orchestration --> HybridRAG & GraphRAG & LTMemory & ToolSystem
    HybridRAG <--> PineconeCloud
    GraphRAG <--> Neo4jDB
    LTMemory <--> PostgresDB
    Orchestration <--> GroqLLM
    Observability -.-o Orchestration
```

### Data Flow

```
User Query → Next.js Frontend → NGINX → FastAPI /api/v1/chat/stream
    ↓
LangGraph StateGraph "The Brain"
    ↓ (Intent Classification)
[RAG | GraphRAG | Memory | Tools] → LLM (NVIDIA/Groq)
    ↓
SSE Response Stream
```

### Project Structure

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
│   ├── rag/                    # Hybrid RAG
│   ├── memory/                 # LTMemory
│   ├── graph/                  # GraphRAG
│   └── tools/                  # Tool framework
│
├── frontend/                   # Next.js application
│   ├── package.json
│   ├── src/                    # React components
│   └── Dockerfile              # Frontend container
│
└── nginx/
    └── nginx.conf              # Reverse proxy config
```

---

## 🛠️ Technology Stack

### Backend

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

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 15 | React 19 App Router |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS 4 | Modern glassmorphism UI |
| State | Zustand | Client-side state management |
| Data Fetching | TanStack Query | Server state caching |
| Animation | Framer Motion | Micro-interactions |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Reverse Proxy | NGINX | Load balancing, SSE streaming |
| Container | Docker | Application packaging |
| Orchestration | Docker Compose | Multi-service deployment |
| Platform | Railway | Cloud deployment |
| Platform | Vercel | Frontend deployment |

---

## ⚙️ Core Components

### LangGraph StateGraph Engine ("The Brain")

The orchestration engine routes queries through 5 distinct pipelines:
- `DIRECT_LLM` - Direct LLM response
- `HYBRID_RAG` - Retrieval-augmented generation
- `GRAPH_RAG` - Knowledge graph reasoning
- `MEMORY_ENHANCED` - Memory-augmented response
- `TOOLS_ENHANCED` - Tool-augmented response

**Features:**
- Conditional DAG routing based on intent confidence
- LLM fallback chain (NVIDIA → Groq → Mock)
- Server-Sent Events (SSE) streaming
- Intermediate tool thought visualization

### Hybrid RAG Pipeline

- **Dense Retrieval**: Pinecone BAAI/bge-large-en-v1.5 (1024 dimensions)
- **Sparse Retrieval**: BM25 keyword search
- **Fusion**: Reciprocal Rank Fusion (RRF)

### GraphRAG Engine

- Neo4j Cypher query execution
- Multi-hop entity traversal
- Knowledge graph construction from documents
- Entity relationship extraction

### Long-Term Memory System

- PostgreSQL-based user profiles
- Ebbinghaus forgetting curve implementation
- Semantic fact extraction
- Episodic conversation logging

### Tool Framework

Decoupled tool execution:
- **Web Search** - Real-time web queries
- **SQL Executor** - Database queries
- **Calculator** - Mathematical operations
- **Cypher** - Graph database queries

---

## 🔌 API Endpoints

### Endpoint Overview

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

### Key Endpoints

**Chat:**
- `POST /api/v1/chat` - Send chat message
- `POST /api/v1/chat/stream` - SSE streaming response
- `GET /api/v1/chat/history` - Get chat history

**Memory:**
- `GET /api/v1/memory/user/{user_id}` - Get user memories
- `POST /api/v1/memory` - Store memory
- `DELETE /api/v1/memory/{memory_id}` - Delete memory

**Knowledge:**
- `GET /api/v1/knowledge` - List knowledge items
- `POST /api/v1/knowledge` - Add knowledge item
- `GET /api/v1/knowledge/search` - Search knowledge

**Graph:**
- `GET /api/v1/graph/query` - Execute Cypher query
- `POST /api/v1/graph/entity` - Add entity
- `GET /api/v1/graph/neighbors` - Get node neighbors

**Monitoring:**
- `GET /health` - Health check
- `GET /api/v1/monitoring/metrics` - System metrics

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## 💾 Data Storage

### PostgreSQL (Profiles & Episodic Memory)
```yaml
Host: POSTGRES_HOST (default: localhost)
Port: 5432
Database: vyron_db
Purpose: User profiles, conversation logs, semantic memories
```

### Neo4j (Knowledge Graph)
```yaml
URI: bolt://localhost:7687
Database: neo4j
Purpose: Graph entities, relationships, multi-hop queries
```

### Pinecone (Vector Storage)
```yaml
Environment: us-east-1
Index: chatbot-vectors
Dimension: 1024
Namespace: default
Purpose: Dense embeddings, semantic search
```

### MongoDB (Document Store)
```yaml
URI: mongodb://localhost:27017
Database: chatbot_memory
Purpose: Knowledge documents, file storage
```

---

## 🔐 Configuration

### Environment Variables

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

### Feature Flags

```env
ENABLE_MEMORY=true
ENABLE_GRAPH=true
ENABLE_TOOLS=true
ENABLE_HYBRID_RAG=true
ENABLE_RERANKER=true
ENABLE_EVALUATION=false
```

---

## 💻 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Backend
```bash
pip install -r requirements.txt
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Full Stack (Docker)
```bash
docker compose up -d
```

---

## 🚀 Deployment

### Docker Compose (Production Stack)
```bash
docker compose up -d --build
```

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80 | Reverse proxy |
| frontend | 3000 | Next.js app |
| backend | 8000 | FastAPI app |

### Railway Deployment
1. Connect GitHub repository
2. Railway auto-detects `Dockerfile`
3. Set environment variables in dashboard
4. Deploy with health check on `/health`

### Vercel Deployment (Frontend)
1. Import `frontend/` directory
2. Set environment variables:
   - `NEXT_PUBLIC_API_BASE_URL`
3. Deploy automatically

---

## 🔒 Security

### Secrets Management
- Never commit `.env` files
- Use environment variables for all secrets
- Rotate API keys regularly

### API Security
- CORS configured for specific origins
- Request ID tracking for audit logs
- Rate limiting (recommended for production)

### Database Security
- Use strong passwords
- Enable SSL connections in production
- Regular backups

---

## 🧪 CI/CD

Automated GitHub Actions workflows (`.github/workflows/deploy.yml`):

1. **Python Contract Verification**: Runs `python scratch/test_frontend_api_contract.py` using FastAPI `TestClient`
2. **Next.js Production Compilation**: Executes `npm run build` in `frontend/`
3. **Docker Multi-Stage Integrity Check**: Verifies image builds

---

## 🧭 Roadmap & Completed Milestones

- ✅ Milestone 1: FastAPI Backend Architecture, Configuration Layer & Exception Handling
- ✅ Milestone 2: Infrastructure & Database Connections
- ✅ Milestone 3: Repository Layer (PostgresRepository, MongoRepository, Neo4jRepository)
- ✅ Milestone 4: Knowledge Ingestion Pipeline (PDF, DOCX, Markdown, YAML)
- ✅ Milestone 5: Hybrid RAG Pipeline (Pinecone Dense + BM25 + RRF)
- ✅ Milestone 6: Knowledge Repository & Relational Persistence Layer
- ✅ Milestone 7: Pinecone Dense Retrieval Engine & Cross-Encoder Reranking
- ✅ Milestone 8: GraphRAG Knowledge Graph (Neo4j)
- ✅ Milestone 9 & 10: Retrieval Fusion (RRF) & Graph Structural Evaluation
- ✅ Milestone 11: LangGraph Orchestration (The Brain)
- ✅ Milestone 12: Long-Term Memory System (PostgreSQL)
- ✅ Milestone 13: Tool Execution Framework
- ✅ Milestone 14: Evaluation, Monitoring & Observability Platform
- ✅ Milestone 15: Productization, Next.js 15, Live SSE & Docker Deployment

---

## 📄 License

Copyright © 2026. All rights reserved.