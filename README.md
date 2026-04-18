# Multi-Tenant RAG Platform

**Production-grade document Q&A with tenant isolation, hybrid search, and measurable retrieval quality.**

---

Every company has the same problem: critical knowledge is buried in PDFs, Word docs, and internal wikis. Teams waste hours searching for answers that exist somewhere in the organization's documents. Off-the-shelf RAG solutions get you a prototype in a weekend, but they fall apart when you need tenant isolation, verifiable citations, or any way to measure whether the answers are actually correct.

This platform solves that gap. It's a multi-tenant Retrieval-Augmented Generation system where organizations upload their documents and employees ask natural-language questions. Every answer cites specific source passages with page numbers. Every tenant's data is fully isolated — separate vector collections, separate BM25 indices, separate rate limits. And critically, retrieval quality is measured, not assumed: a built-in RAGAS evaluation framework benchmarks faithfulness, context recall, and answer relevancy against a 50-question evaluation set.

The retrieval pipeline goes beyond basic vector search. It combines dense embeddings with BM25 sparse retrieval via Reciprocal Rank Fusion, then applies neural reranking (Cohere Rerank with CrossEncoder fallback) before generation. This hybrid approach demonstrably outperforms dense-only search, and the platform includes A/B comparison tools to prove it with your own data.

---

## Screenshots

<table>
  <tr>
    <td><img src="docs/screenshots/query-playground.png" alt="Query Playground" width="100%"><br><strong>Query Playground</strong> — Real Q&A with <code>[Source N]</code> citations and a four-stage latency breakdown (embed, sparse, rerank, generate)</td>
    <td><img src="docs/screenshots/ragas-evaluation.png" alt="RAGAS Evaluation" width="100%"><br><strong>RAGAS Evaluation</strong> — Faithfulness 0.847, Answer Relevancy 0.860, Context Recall 0.877, Context Precision 0.780 over the 50-question eval set, with a score-history chart</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/health-dashboard.png" alt="Health Dashboard" width="100%"><br><strong>Health Dashboard</strong> — Real-time latency for PostgreSQL, Qdrant, and Redis with per-service status pills</td>
    <td><img src="docs/screenshots/tenant-management.png" alt="Tenant Management" width="100%"><br><strong>Tenant Management</strong> — Active tenants with per-tenant rate limits (QPM), creation dates, and health indicators</td>
  </tr>
</table>

---

## What Problems Does It Solve?

| Without this platform | With this platform |
|---|---|
| Knowledge trapped in unstructured documents across teams | Upload PDFs, DOCX, HTML, Markdown — ask questions in plain English |
| No way to verify if an AI answer is grounded in source material | Every answer includes `[Source N]` citations with document name, page number, and relevance score |
| Single-tenant solutions that can't serve multiple organizations | Full namespace isolation — each tenant gets dedicated vector collections, BM25 indices, and rate limits |
| "It seems to work" retrieval with no quality measurement | RAGAS evaluation suite measures faithfulness, context recall, precision, and relevancy against a curated test set |
| Dense-only vector search misses keyword-critical queries | Hybrid search (dense + BM25 + RRF) with neural reranking catches what embeddings miss |
| No visibility into cost per query or per tenant | Per-query token counting, cost estimation, and tenant-level usage analytics |
| Black-box retrieval — no idea which pipeline stage is slow | Full latency breakdown: embedding, retrieval, reranking, and generation measured separately |

---

## Who Is It For?

- **Platform engineers** building internal knowledge bases that need to serve multiple teams or clients with data isolation
- **AI/ML engineers** who need a reference implementation of production RAG with hybrid search, reranking, and evaluation
- **Technical leads** evaluating RAG architectures and need measurable comparisons between retrieval strategies
- **SaaS builders** who need multi-tenant document Q&A as a foundation for their product

---

## How It Works

The platform follows a three-stage pipeline: **Ingest**, **Retrieve**, **Generate**.

**1. Document Ingestion**
Upload a document (PDF, DOCX, HTML, or Markdown). The ingestion pipeline extracts text, splits it into chunks using your chosen strategy (fixed-size, semantic, or parent-child), generates 384-dimensional embeddings via `all-MiniLM-L6-v2`, and stores vectors in a tenant-scoped Qdrant collection. A BM25 index is simultaneously built in Redis for sparse retrieval.

**2. Hybrid Retrieval**
When a query arrives, it's embedded and sent to both the dense retriever (Qdrant, top-20) and the sparse retriever (BM25, top-20). Results are fused via Reciprocal Rank Fusion (k=60), filtered by metadata (document IDs, categories, date ranges), and reranked using Cohere Rerank (with CrossEncoder fallback) down to the top-5 most relevant chunks.

**3. Answer Generation**
If the top reranked chunk scores above the confidence threshold (0.3), the chunks are passed to the LLM (GPT-4o-mini) with a grounding prompt. The response includes inline `[Source N]` citations mapped to specific document passages. If confidence is too low, the system returns "insufficient information" without invoking the LLM — saving cost and avoiding hallucination.

```
Document Upload
    │
    ├── Extract text (PyMuPDF / python-docx / BeautifulSoup)
    ├── Chunk (fixed-size │ semantic │ parent-child)
    ├── Embed (all-MiniLM-L6-v2, 384-dim)
    ├── Store vectors (Qdrant, tenant-scoped collection)
    └── Build sparse index (BM25, Redis)

User Query
    │
    ├── Embed query
    ├── Dense search (Qdrant, top-20)
    ├── Sparse search (BM25, top-20)
    ├── Reciprocal Rank Fusion
    ├── Metadata filtering
    ├── Neural reranking (Cohere / CrossEncoder) → top-5
    ├── Confidence check (threshold: 0.3)
    │     ├── Below → "Insufficient information"
    │     └── Above → LLM generation with citations
    └── Response: { answer, citations[], latency_breakdown, token_usage }
```

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
    └───────────────────────────────┬────────────────────────────────────────────┘
                                    │ HTTP / SSE
                                    ▼
    ┌───────────────────────────────────────────────────────────────────────────┐
    │                          FastAPI Backend (Python)                         │
    │                                                                           │
    │  ┌─── API Layer ──────────────────────────────────────────────────────┐   │
    │  │  Auth Middleware (Argon2 API Keys) · Rate Limiter (Redis Sliding)  │   │
    │  │  /api/v1/documents · /api/v1/query · /api/v1/admin · /health      │   │
    │  └────────────────────────────────────────────────────────────────────┘   │
    │                                                                           │
    │  ┌─── Ingestion Pipeline ────┐   ┌─── Retrieval Pipeline ────────────┐   │
    │  │  Extractors:              │   │  Dense Retriever (Qdrant)         │   │
    │  │   PDF · DOCX · HTML · MD  │   │  Sparse Retriever (BM25/Redis)   │   │
    │  │  Chunkers:                │   │  Reciprocal Rank Fusion (k=60)   │   │
    │  │   Fixed · Semantic ·      │   │  Reranker:                       │   │
    │  │   Parent-Child            │   │   Cohere API + CrossEncoder      │   │
    │  │  Embeddings:              │   │  Metadata Filtering              │   │
    │  │   sentence-transformers   │   │  Low-Confidence Detection        │   │
    │  └───────────────────────────┘   └───────────────────────────────────┘   │
    │                                                                           │
    │  ┌─── Generation Pipeline ───┐   ┌─── Evaluation Pipeline ──────────┐   │
    │  │  LLM Service (OpenAI API) │   │  RAGAS Metrics                   │   │
    │  │  Citation Builder         │   │  A/B Comparison (Hybrid vs Dense)│   │
    │  │  SSE Streaming            │   │  Reranking Impact Analysis       │   │
    │  │  Cost Tracker             │   │  50-Question Eval Set            │   │
    │  └───────────────────────────┘   └──────────────────────────────────┘   │
    │                                                                           │
    └──────┬────────────────────┬──────────────────────┬───────────────────────┘
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

### Multi-Tenancy Isolation Model

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

## Real-World Scenarios

### Scenario 1: Legal Firm with Multiple Clients

A legal firm uploads case law PDFs and contracts for each client as a separate tenant. Lawyers ask questions like "What are the indemnification clauses in the Acme contract?" and receive answers citing specific paragraphs and page numbers. Client A's documents are never visible to Client B's queries — enforced at the vector store, BM25 index, and API middleware layers.

### Scenario 2: Enterprise Knowledge Base

A company uploads its internal documentation (HR policies, engineering runbooks, product specs) across different categories. Employees query "What's the PTO policy for employees in their first year?" and get a grounded answer with `[Source 1]` pointing to the HR handbook page 12. The admin monitors per-team usage and cost via the tenant usage dashboard.

### Scenario 3: Evaluating Retrieval Strategy Changes

An ML engineer wants to know if adding BM25 sparse retrieval improves answer quality over dense-only search. They run the RAGAS evaluation suite in both modes — hybrid and dense-only — against the 50-question evaluation set. The A/B comparison shows hybrid search achieves higher context recall (0.85+ vs 0.72), confirming the value of the sparse retrieval stage.

### Scenario 4: SaaS Platform with API-First Integration

A SaaS company embeds document Q&A into their product. They provision tenants via the admin API, distribute API keys to each customer, and call the query endpoint from their own frontend. Rate limiting prevents any single customer from overwhelming the system, and per-query cost tracking feeds into their billing pipeline.

---

## Tech Stack

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

## Quick Start

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

## Integration Guide

Full API workflow from tenant provisioning to querying documents.

### Step 1: Create a Tenant

```bash
curl -X POST http://localhost:8000/api/v1/admin/tenants \
  -H "Authorization: Bearer admin-secret-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"name": "acme-corp", "rate_limit_qpm": 60}'
```

**Response:**
```json
{
  "tenant": {
    "id": "a1b2c3d4-...",
    "name": "acme-corp",
    "is_active": true,
    "rate_limit_qpm": 60,
    "created_at": "2026-04-15T10:30:00Z"
  },
  "api_key": "rag_53EoMzpUxRhUfntgi4z..."
}
```

> Save the `api_key` — it is shown only once.

### Step 2: Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer rag_53EoMzpUxRhUfntgi4z..." \
  -F "file=@report.pdf" \
  -F "category=reports" \
  -F "chunking_strategy=semantic"
```

**Response:**
```json
{
  "id": "d5e6f7g8-...",
  "filename": "report.pdf",
  "format": "pdf",
  "category": "reports",
  "status": "queued",
  "upload_date": "2026-04-15T10:31:00Z"
}
```

Supported formats: `.pdf`, `.docx`, `.html`, `.htm`, `.md`, `.markdown` (max 100 MB).
Chunking strategies: `fixed` (512 tokens), `semantic` (similarity-based), `parent_child` (hierarchical).

### Step 3: Check Document Status

```bash
curl http://localhost:8000/api/v1/documents/d5e6f7g8-... \
  -H "Authorization: Bearer rag_53EoMzpUxRhUfntgi4z..."
```

**Response:**
```json
{
  "id": "d5e6f7g8-...",
  "tenant_id": "a1b2c3d4-...",
  "filename": "report.pdf",
  "format": "pdf",
  "category": "reports",
  "status": "completed",
  "page_count": 42,
  "chunk_count": 87,
  "chunking_strategy": "semantic",
  "upload_date": "2026-04-15T10:31:00Z",
  "created_at": "2026-04-15T10:31:00Z"
}
```

Status transitions: `queued` → `processing` → `completed` / `failed`.

### Step 4: Query Your Documents

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer rag_53EoMzpUxRhUfntgi4z..." \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main findings of the report?",
    "top_k": 20,
    "top_n": 5,
    "search_type": "hybrid",
    "filters": {
      "categories": ["reports"]
    }
  }'
```

**Response:**
```json
{
  "answer": "The main findings include... [Source 1] ... [Source 2]",
  "citations": [
    {
      "source_number": 1,
      "document_name": "report.pdf",
      "document_id": "d5e6f7g8-...",
      "page_number": 3,
      "chunk_text": "The analysis reveals that...",
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
      "total_tokens": 1350,
      "estimated_cost": 0.00025
    },
    "retrieval_strategy": "hybrid",
    "reranking_enabled": true
  }
}
```

### Step 5: Stream Responses (SSE)

```bash
curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Authorization: Bearer rag_53EoMzpUxRhUfntgi4z..." \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the key recommendations"}'
```

**SSE Events:**
```
data: {"type": "token", "content": "The"}
data: {"type": "token", "content": " key"}
data: {"type": "token", "content": " recommendations"}
...
data: {"type": "citations", "content": [{"source_number": 1, ...}]}
data: {"type": "metadata", "content": {"latency": {...}, "tokens": {...}}}
data: {"type": "done"}
```

### Step 6: Check Tenant Usage

```bash
curl http://localhost:8000/api/v1/admin/tenants/a1b2c3d4-.../usage \
  -H "Authorization: Bearer admin-secret-key-change-me"
```

**Response:**
```json
{
  "tenant_id": "a1b2c3d4-...",
  "tenant_name": "acme-corp",
  "total_queries": 142,
  "total_prompt_tokens": 85000,
  "total_completion_tokens": 12000,
  "total_tokens": 97000,
  "total_estimated_cost": 0.0156,
  "document_count": 23
}
```

### Step 7: Run RAGAS Evaluation

```bash
curl -X POST http://localhost:8000/api/v1/admin/eval/run \
  -H "Authorization: Bearer admin-secret-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"strategy": "hybrid", "reranking_enabled": true}'
```

**Response:**
```json
{
  "id": "e9f0a1b2-...",
  "run_id": "eval-20260415-103500",
  "strategy": "hybrid",
  "reranking_enabled": true,
  "faithfulness": 0.84,
  "answer_relevancy": 0.79,
  "context_precision": 0.81,
  "context_recall": 0.88,
  "created_at": "2026-04-15T10:35:00Z"
}
```

---

## Comparison with Alternatives

| Feature | This Platform | LangChain + Chroma | LlamaIndex Cloud | Vercel AI SDK + Pinecone |
|---|---|---|---|---|
| Multi-tenant isolation | Dedicated vector collections + BM25 indices per tenant | Manual — requires custom namespace management | Managed — but vendor lock-in | Manual — requires custom implementation |
| Hybrid search (dense + sparse) | Built-in: Qdrant + BM25 + RRF fusion | Requires custom assembly | Supported via managed pipeline | Dense-only by default |
| Neural reranking | Cohere + CrossEncoder fallback | Plugin-based, no fallback | Managed reranker | Not included |
| Citation generation | Automatic `[Source N]` with page numbers and scores | Manual prompt engineering | Basic source nodes | Manual implementation |
| Evaluation framework | Built-in RAGAS with A/B comparison | Separate integration needed | Basic evaluation | No built-in evaluation |
| Cost tracking | Per-query token counting with tenant-level aggregation | Not included | Platform-level only | Not included |
| Rate limiting | Per-tenant Redis sliding window | Not included | Platform-managed | Not included |
| Streaming | SSE with structured events (token, citations, metadata) | Basic streaming | Managed streaming | Built-in streaming |
| Self-hosted | Fully self-hosted via Docker Compose | Self-hosted | Cloud-managed (SaaS) | Cloud-dependent |
| Chunking strategies | 3 built-in (fixed, semantic, parent-child) | Multiple via plugins | Managed | Manual implementation |

**Key differentiator:** This platform is the only option that combines multi-tenant isolation, hybrid search with reranking, automatic citations, and built-in RAGAS evaluation in a single self-hosted package. Managed solutions (LlamaIndex Cloud) trade control for convenience. Framework-only solutions (LangChain, Vercel AI SDK) require assembling these capabilities yourself.

---

## Key Metrics & Success Criteria

These targets are validated against a 50-question evaluation set using the RAGAS framework:

| Metric | Target | What It Measures |
|---|---|---|
| Context Recall | > 0.85 | Are all necessary source chunks retrieved? |
| Faithfulness | > 0.80 | Is the answer grounded in the retrieved context (no hallucination)? |
| Answer Relevancy | > 0.75 | Does the answer actually address the question asked? |
| Context Precision | > 0.75 | Are the retrieved chunks relevant (low noise)? |
| Retrieval Latency | < 3 seconds | End-to-end retrieval excluding LLM generation |
| Concurrent Load | 100 queries | System handles 100 concurrent queries without failure |
| Hybrid vs Dense-Only | Hybrid wins | A/B comparison demonstrates hybrid search outperforms dense-only |
| Reranking Impact | Measurable gain | Reranking demonstrably improves precision over un-reranked results |
| Tenant Isolation | Zero leakage | Tenant A's queries never return Tenant B's documents |

---

## Scope / What This Does NOT Do

This platform is intentionally scoped. The following are explicitly **out of scope**:

- **User-level authentication within tenants** — Only tenant-level API keys are implemented. There is no concept of individual users within a tenant.
- **Billing and payment processing** — Cost tracking is provided for integration with external billing systems, but no payment flows are built in.
- **Document versioning** — Uploading a new version of a document requires deleting the old one and re-uploading. There is no edit history.
- **Multi-language support** — The platform is English-only. Embeddings, BM25 tokenization, and evaluation are tuned for English text.
- **Fine-tuning or custom model training** — The platform uses pre-trained models (sentence-transformers for embeddings, OpenAI-compatible API for generation). No training pipelines are included.
- **User-facing authentication UI** — The frontend is an admin/developer tool. Tenant API keys are managed via the admin API or the Tenants page — there is no login flow for end users.

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
| `GET` | `/api/v1/admin/config/chunking-strategies` | Get available chunking strategies |

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

## Evaluation

The platform includes a built-in evaluation framework using RAGAS metrics:

- **Faithfulness** — Is the answer grounded in the retrieved context?
- **Answer Relevancy** — Does the answer address the question?
- **Context Precision** — Are the retrieved chunks relevant?
- **Context Recall** — Are all necessary chunks retrieved?

Run evaluations via the admin API or the Eval page in the dashboard. The platform also supports A/B comparison between hybrid vs dense-only search and reranking impact analysis.
