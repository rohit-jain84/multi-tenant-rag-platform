# Multi-Tenant RAG Platform

A production-grade Retrieval-Augmented Generation platform with full multi-tenant isolation, hybrid search, intelligent reranking, and comprehensive evaluation.

---

## Architecture

```
                                   Multi-Tenant RAG Platform
                                   ========================

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                              React SPA (Frontend)                          │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
    │  │  Query   │ │Documents │ │  Eval    │ │ Tenants  │ │ Health Dashboard │ │
    │  │  Page    │ │  Page    │ │  Page    │ │  Page    │ │                  │ │
    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
    │       React 19 · TypeScript · Vite · TailwindCSS · Recharts · Axios       │
    └───────────────────────────────┬──────────────────────────────────────────-──┘
                                    │ HTTP / SSE
                                    ▼
    ┌───────────────────────────────────────────────────────────────────────────┐
    │                          FastAPI Backend (Python)                         │
    │                                                                           │
    │  ┌─── API Layer ──────────────────────────────────────────────────────┐   │
    │  │  Auth Middleware (Argon2 API Keys) · Rate Limiter (Redis Sliding)  │   │
    │  │  /api/v1/documents · /api/v1/query · /api/v1/admin · /health      │   │
    │  └───────────────────────────────────────────────────────────────────-┘   │
    │                                                                           │
    │  ┌─── Ingestion Pipeline ────┐   ┌─── Retrieval Pipeline ────────────┐   │
    │  │  Extractors:              │   │  Dense Retriever (Qdrant)         │   │
    │  │   PDF · DOCX · HTML · MD  │   │  Sparse Retriever (BM25/Redis)   │   │
    │  │  Chunkers:                │   │  Reciprocal Rank Fusion (k=60)   │   │
    │  │   Fixed · Semantic ·      │   │  Reranker:                       │   │
    │  │   Parent-Child            │   │   Cohere API + CrossEncoder      │   │
    │  │  Embeddings:              │   │  Metadata Filtering              │   │
    │  │   sentence-transformers   │   │  Low-Confidence Detection        │   │
    │  └───────────────────────────┘   └──────────────────────────────────-┘   │
    │                                                                           │
    │  ┌─── Generation Pipeline ───┐   ┌─── Evaluation Pipeline ──────────┐   │
    │  │  LLM Service (OpenAI API) │   │  RAGAS Metrics                   │   │
    │  │  Citation Builder         │   │  A/B Comparison (Hybrid vs Dense)│   │
    │  │  SSE Streaming            │   │  Reranking Impact Analysis       │   │
    │  │  Cost Tracker             │   │  50-Question Eval Set            │   │
    │  └───────────────────────────┘   └──────────────────────────────────-┘   │
    │                                                                           │
    └──────┬────────────────────┬──────────────────────┬───────────────────────-┘
           │                    │                      │
           ▼                    ▼                      ▼
    ┌──────────────┐   ┌──────────────┐   ┌───────────────────┐
    │ PostgreSQL 16│   │   Redis 7    │   │     Qdrant        │
    │              │   │              │   │                   │
    │ Tenants      │   │ Rate Limits  │   │ tenant_{uuid}     │
    │ API Keys     │   │ Query Cache  │   │   collections     │
    │ Documents    │   │ BM25 Indices │   │                   │
    │ Query Logs   │   │              │   │ 384-dim vectors   │
    │ Eval Results │   │              │   │ cosine similarity │
    └──────────────┘   └──────────────┘   └───────────────────┘
```

### RAG Query Flow

```
User Query
    │
    ├──► Embed Query (all-MiniLM-L6-v2)
    │       │
    │       ├──► Dense Search (Qdrant, top-20)
    │       │
    │       └──► Sparse Search (BM25, top-20)
    │               │
    │               ▼
    │       Reciprocal Rank Fusion
    │               │
    │               ▼
    │       Metadata Filtering (doc IDs, dates, categories)
    │               │
    │               ▼
    │       Reranking (Cohere / CrossEncoder) → top-5
    │               │
    │               ▼
    │       Confidence Check (threshold: 0.3)
    │           │           │
    │       < 0.3       ≥ 0.3
    │           │           │
    │    "Insufficient   LLM Generation
    │     information"   with [Source N] citations
    │                       │
    │                       ▼
    └──────────────► Response
                     { answer, citations, latency_breakdown, token_usage }
```

### Multi-Tenancy Model

```
┌─────────────────────────────────────────────┐
│                API Gateway                   │
│  Authorization: Bearer <api_key>            │
│                                              │
│  1. Extract key → lookup by prefix (8 char) │
│  2. Verify Argon2 hash                      │
│  3. Confirm tenant is active                │
│  4. Attach tenant_id to request             │
└──────────┬──────────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐  ┌────────┐    Each tenant gets:
│Tenant A│  │Tenant B│    • Dedicated Qdrant collection (tenant_{uuid})
│        │  │        │    • Isolated BM25 index in Redis
│ Docs   │  │ Docs   │    • Per-tenant rate limiting
│ Queries│  │ Queries│    • Scoped document & query history
│ Keys   │  │ Keys   │    • Independent usage analytics
└────────┘  └────────┘
```

---

## Technologies

### Backend

| Category | Technology |
|----------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 (async, asyncpg) |
| Database | PostgreSQL 16 |
| Vector Store | Qdrant |
| Cache | Redis 7 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2, 384-dim) |
| LLM | OpenAI-compatible API (gpt-4o-mini default) |
| Reranking | Cohere Rerank + CrossEncoder fallback |
| Sparse Search | BM25 (rank-bm25, index in Redis) |
| Fusion | Reciprocal Rank Fusion (RRF) |
| Document Parsing | PyMuPDF, pdfplumber, python-docx, BeautifulSoup4 |
| Auth | Argon2 (API key hashing) |
| Evaluation | RAGAS |
| Logging | structlog (JSON, correlation IDs) |
| Migrations | Alembic |
| Load Testing | Locust |

### Frontend

| Category | Technology |
|----------|-----------|
| Language | TypeScript |
| Framework | React 19 |
| Build | Vite |
| Styling | TailwindCSS |
| Routing | React Router v7 |
| HTTP | Axios |
| Charts | Recharts |
| Tables | TanStack React Table |
| Forms | React Hook Form |
| File Upload | react-dropzone |
| Icons | lucide-react |

### Infrastructure

| Category | Technology |
|----------|-----------|
| Containerization | Docker + Docker Compose |
| Services | PostgreSQL 16, Redis 7, Qdrant, FastAPI backend |
| Volumes | Persistent data for all three datastores |

---

## Features

- **Multi-Document Ingestion** — Upload PDF, DOCX, HTML, and Markdown files with automatic text extraction
- **3 Chunking Strategies** — Fixed-size (512 tokens), semantic (similarity-based splits), and parent-child (hierarchical retrieval)
- **Hybrid Search** — Dense vector search + BM25 sparse search combined via Reciprocal Rank Fusion
- **Intelligent Reranking** — Cohere Rerank API with CrossEncoder fallback for precision
- **Citation Generation** — Automatic `[Source N]` extraction with document name, page number, and relevance score
- **Streaming Responses** — Token-by-token delivery via Server-Sent Events (SSE)
- **Cost Tracking** — Per-query token counting and cost estimation with configurable pricing
- **Metadata Filtering** — Filter by document IDs, date ranges, and categories
- **RAGAS Evaluation** — Faithfulness, answer relevancy, context precision, and context recall
- **A/B Comparison** — Hybrid vs dense-only and reranking impact analysis
- **Per-Tenant Rate Limiting** — Configurable QPM with Redis sliding window
- **Query Cache** — Redis-based caching with configurable TTL
- **Low-Confidence Handling** — Graceful fallback when retrieval confidence is below threshold
- **Structured Logging** — JSON logs with correlation IDs for end-to-end traceability
- **Admin Dashboard** — Tenant provisioning, usage analytics, and evaluation management
- **Load Testing** — Locust framework for 100 concurrent query simulation

---

## Project Structure

```
Multi-Tenant RAG Platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── documents.py          # Upload, list, delete endpoints
│   │   │   │   ├── query.py              # Query and streaming endpoints
│   │   │   │   ├── admin.py              # Tenant provisioning, eval, usage
│   │   │   │   ├── health.py             # Health check
│   │   │   │   └── router.py             # Route aggregation
│   │   │   └── middleware/
│   │   │       ├── auth.py               # API key auth, tenant isolation
│   │   │       └── rate_limit.py         # Redis sliding window rate limiter
│   │   ├── models/                       # SQLAlchemy ORM models
│   │   ├── schemas/                      # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── pipeline.py           # Extract → Chunk → Embed → Store
│   │   │   │   ├── extractors/           # PDF, DOCX, HTML, Markdown
│   │   │   │   └── chunking/             # Fixed, semantic, parent-child
│   │   │   ├── retrieval/
│   │   │   │   ├── pipeline.py           # Dense + Sparse + Fusion + Rerank
│   │   │   │   ├── dense_retriever.py    # Qdrant vector search
│   │   │   │   ├── sparse_retriever.py   # BM25 search
│   │   │   │   ├── fusion.py             # Reciprocal Rank Fusion
│   │   │   │   └── reranker.py           # Cohere + CrossEncoder
│   │   │   ├── generation/
│   │   │   │   ├── llm_service.py        # LLM orchestration
│   │   │   │   ├── citation_builder.py   # Citation extraction
│   │   │   │   ├── streaming.py          # SSE handler
│   │   │   │   └── cost_tracker.py       # Token & cost tracking
│   │   │   └── evaluation/
│   │   │       ├── ragas_runner.py        # RAGAS metrics
│   │   │       └── ab_comparison.py       # Strategy comparison
│   │   ├── db/                           # Database session, base, migrations
│   │   ├── vector_store/                 # Qdrant client, embedding wrapper
│   │   ├── cache/                        # Redis client
│   │   ├── utils/                        # Logging, hashing, errors
│   │   ├── main.py                       # FastAPI entry point
│   │   └── config.py                     # Pydantic settings
│   ├── tests/
│   │   ├── unit/                         # Chunking, extractors, fusion, citations
│   │   ├── integration/                  # Pipelines, tenant isolation, API
│   │   └── load/                         # Locust load tests
│   ├── eval/                             # Evaluation scripts and datasets
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── pyproject.toml
│
└── frontend/
    ├── src/
    │   ├── pages/                        # Query, Documents, Eval, Tenants, Health
    │   ├── components/                   # UI components per domain
    │   ├── api/                          # Axios API clients
    │   ├── context/                      # Auth & Theme contexts
    │   ├── hooks/                        # Custom React hooks
    │   ├── types/                        # TypeScript interfaces
    │   └── App.tsx                       # Router & layout
    ├── package.json
    └── vite.config.ts
```

---

## API Endpoints

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents` | Upload a document (multipart: file, category, chunking_strategy) |
| `GET` | `/api/v1/documents` | List documents (paginated) |
| `GET` | `/api/v1/documents/{id}` | Get document details |
| `DELETE` | `/api/v1/documents/{id}` | Delete document and its vectors |

### Query

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Submit a query (returns full response) |
| `POST` | `/api/v1/query/stream` | Submit a query (streams tokens via SSE) |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/tenants` | Create tenant and generate API key |
| `GET` | `/api/v1/admin/tenants` | List all tenants |
| `GET` | `/api/v1/admin/tenants/{id}/usage` | Get tenant usage stats |
| `POST` | `/api/v1/admin/eval/run` | Trigger RAGAS evaluation run |
| `GET` | `/api/v1/admin/eval/results` | Get evaluation results |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health (PostgreSQL, Redis, Qdrant) |

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `tenants` | Tenant metadata (name, status, rate limit config) |
| `api_keys` | Hashed API keys per tenant (Argon2, prefix-indexed) |
| `documents` | Document metadata and ingestion status tracking |
| `query_logs` | Query history with token usage, cost, and latency breakdown |
| `eval_results` | RAGAS evaluation metrics per run |

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (or compatible LLM endpoint)
- Cohere API key (optional, for reranking)

### Setup

```bash
# Clone and navigate
cd backend

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Create your first tenant (via API or admin dashboard)
curl -X POST http://localhost:8000/api/v1/admin/tenants \
  -H "Authorization: Bearer admin-secret-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-tenant"}'
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173, proxies API to localhost:8000
```

### Running Tests

```bash
# Unit tests
docker compose exec backend pytest tests/unit/ -v

# Integration tests
docker compose exec backend pytest tests/integration/ -v

# Load tests
docker compose exec backend locust -f tests/load/locustfile.py
```

---

## Query Example

**Request:**
```json
POST /api/v1/query
{
  "question": "What are the main findings of the report?",
  "top_k": 20,
  "top_n": 5,
  "search_type": "hybrid",
  "filters": {
    "categories": ["report"]
  }
}
```

**Response:**
```json
{
  "answer": "The main findings include... [Source 1] ... [Source 2]",
  "citations": [
    {
      "source_number": 1,
      "document_name": "report.pdf",
      "page_number": 3,
      "chunk_text": "...",
      "relevance_score": 0.92
    }
  ],
  "query_metadata": {
    "latency": {
      "embedding_ms": 45,
      "retrieval_ms": 120,
      "reranking_ms": 300,
      "generation_ms": 2000,
      "total_ms": 2465
    },
    "tokens": {
      "prompt_tokens": 1200,
      "completion_tokens": 150,
      "total_tokens": 1350
    },
    "retrieval_strategy": "hybrid",
    "reranking_enabled": true
  }
}
```

---

## Evaluation

The platform includes a built-in evaluation framework using RAGAS metrics:

- **Faithfulness** — Is the answer grounded in the retrieved context?
- **Answer Relevancy** — Does the answer address the question?
- **Context Precision** — Are the retrieved chunks relevant?
- **Context Recall** — Are all necessary chunks retrieved?

Run evaluations via the admin API or the Eval page in the dashboard. The platform also supports A/B comparison between hybrid vs dense-only search and reranking impact analysis.
