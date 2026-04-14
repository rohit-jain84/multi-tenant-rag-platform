# Backend Implementation Plan

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point
│   ├── config.py                        # Settings via pydantic-settings (env vars)
│   ├── dependencies.py                  # Shared FastAPI dependencies
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py                # Aggregates all v1 routers
│   │   │   ├── documents.py             # POST/GET/DELETE /api/v1/documents
│   │   │   ├── query.py                 # POST /api/v1/query, /api/v1/query/stream
│   │   │   ├── admin.py                 # Tenant provisioning, usage, eval endpoints
│   │   │   └── health.py                # GET /health
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth.py                  # API key authentication middleware
│   │       └── rate_limit.py            # Redis-based per-tenant rate limiting
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py                    # Tenant SQLAlchemy model
│   │   ├── document.py                  # Document model (status, metadata)
│   │   ├── api_key.py                   # API key model (hashed keys)
│   │   ├── query_log.py                 # Query log & cost tracking model
│   │   └── eval_result.py              # RAGAS evaluation result model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── tenant.py                    # Pydantic schemas for tenant CRUD
│   │   ├── document.py                  # Upload request/response schemas
│   │   ├── query.py                     # Query request/response, citation schema
│   │   └── eval.py                      # Evaluation request/response schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tenant_service.py            # Tenant CRUD, API key generation
│   │   ├── document_service.py          # Document CRUD, status management
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py              # Orchestrates extraction -> chunking -> embedding -> store
│   │   │   ├── extractors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py              # Abstract base extractor
│   │   │   │   ├── pdf_extractor.py     # PDF text extraction (PyMuPDF + pdfplumber fallback)
│   │   │   │   ├── docx_extractor.py    # DOCX extraction (python-docx)
│   │   │   │   ├── html_extractor.py    # HTML extraction (BeautifulSoup)
│   │   │   │   └── markdown_extractor.py # Markdown extraction
│   │   │   └── chunking/
│   │   │       ├── __init__.py
│   │   │       ├── base.py              # Abstract base chunker
│   │   │       ├── fixed_size.py        # Fixed-size token chunking with overlap
│   │   │       ├── semantic.py          # Embedding similarity-based chunking
│   │   │       └── parent_child.py      # Hierarchical parent-child chunking
│   │   ├── retrieval/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py              # Orchestrates dense + sparse + fusion + rerank
│   │   │   ├── dense_retriever.py       # sentence-transformers embedding search via Qdrant
│   │   │   ├── sparse_retriever.py      # BM25 retrieval (rank_bm25)
│   │   │   ├── fusion.py               # Reciprocal Rank Fusion (RRF)
│   │   │   └── reranker.py             # Cohere Rerank + local cross-encoder fallback
│   │   ├── generation/
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py           # LLM call with grounding prompt
│   │   │   ├── citation_builder.py      # Build citation objects from source chunks
│   │   │   ├── streaming.py             # SSE streaming response handler
│   │   │   └── cost_tracker.py          # Token usage logging + cost estimation
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       ├── ragas_runner.py          # RAGAS evaluation pipeline
│   │       └── ab_comparison.py         # Hybrid vs. dense-only, with/without reranking
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py                   # SQLAlchemy async session factory
│   │   ├── base.py                      # Declarative base
│   │   └── migrations/                  # Alembic migrations
│   │       ├── env.py
│   │       └── versions/
│   │
│   ├── vector_store/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py             # Qdrant connection, namespace (collection) management
│   │   └── embedding.py                 # sentence-transformers embedding wrapper
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   └── redis_client.py              # Redis connection, query cache, rate limit counters
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py                   # JSON structured logging with correlation IDs
│       ├── hashing.py                   # API key hashing (argon2), document content hashing
│       └── errors.py                    # Consistent error response format
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Fixtures: test DB, test client, tenant factory
│   ├── unit/
│   │   ├── test_chunking.py
│   │   ├── test_extractors.py
│   │   ├── test_fusion.py
│   │   ├── test_citation_builder.py
│   │   └── test_cost_tracker.py
│   ├── integration/
│   │   ├── test_ingestion_pipeline.py
│   │   ├── test_retrieval_pipeline.py
│   │   ├── test_tenant_isolation.py     # Cross-tenant isolation verification
│   │   └── test_api_endpoints.py
│   └── load/
│       └── locustfile.py                # 100 concurrent query load test
│
├── eval/
│   ├── eval_set.json                    # 50-question eval set with ground-truth answers
│   ├── run_ragas.py                     # Script: run RAGAS evaluation
│   ├── run_ab_comparison.py             # Script: hybrid vs. dense-only comparison
│   └── run_rerank_analysis.py           # Script: before/after reranking metrics
│
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml                   # PostgreSQL, Redis, Qdrant, backend app
├── .env.example
└── README.md
```

---

## Phase 1 — Foundation (Core Infrastructure)

### 1.1 Project Setup & Docker Compose

| Task | Details |
|------|---------|
| Initialize Python project | `pyproject.toml` with all dependencies (see dependency list below) |
| Docker Compose | Services: `postgres:16`, `redis:7-alpine`, `qdrant/qdrant:latest`, `backend` (app) |
| Environment config | `app/config.py` using `pydantic-settings` loading from `.env`; `.env.example` with all vars documented |
| FastAPI app skeleton | `main.py` with lifespan handler (startup: connect DB/Redis/Qdrant, shutdown: disconnect) |
| Alembic setup | DB migrations with async SQLAlchemy |

**Dependencies:**
```
fastapi[standard]
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
pydantic-settings
redis[hiredis]
qdrant-client
sentence-transformers
llama-index
rank-bm25
cohere
ragas
PyMuPDF
pdfplumber
python-docx
beautifulsoup4
markdown
argon2-cffi
structlog
httpx
sse-starlette
python-multipart
pytest
pytest-asyncio
locust
```

### 1.2 Database Models & Tenant System

| Task | Details |
|------|---------|
| **Tenant model** | `id (UUID)`, `name`, `created_at`, `is_active`, `rate_limit_qpm` |
| **ApiKey model** | `id`, `tenant_id (FK)`, `key_hash (argon2)`, `key_prefix (first 8 chars for identification)`, `created_at`, `is_active` |
| **Document model** | `id (UUID)`, `tenant_id (FK)`, `filename`, `format`, `category`, `status (enum: queued/processing/completed/failed)`, `error_message`, `content_hash (SHA-256)`, `page_count`, `chunk_count`, `upload_date`, `created_at` |
| **QueryLog model** | `id`, `tenant_id (FK)`, `query_text`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `estimated_cost`, `latency_ms`, `latency_breakdown (JSON)`, `created_at` |
| **EvalResult model** | `id`, `run_id`, `strategy (hybrid/dense_only)`, `reranking_enabled`, `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `created_at` |
| Initial Alembic migration | Generate and apply |

### 1.3 Auth Middleware & Tenant Provisioning

| Task | Details |
|------|---------|
| **Auth middleware** | Extract `Authorization: Bearer <key>` header. Hash incoming key, look up in `api_keys` table. Reject with `401` if invalid/missing. Attach `tenant_id` to request state |
| **Admin: create tenant** | `POST /api/v1/admin/tenants` — creates tenant row, generates random API key, hashes & stores it, provisions Qdrant collection (namespace), returns plaintext key once |
| **Health endpoint** | `GET /health` — checks PostgreSQL, Redis, Qdrant connectivity; returns status per service |

### 1.4 Basic Document Upload & Dense Retrieval

| Task | Details |
|------|---------|
| **Upload endpoint** | `POST /api/v1/documents` — multipart form: file + category. Validates format, saves metadata, queues ingestion |
| **PDF extractor** | PyMuPDF for text extraction with page number tracking; pdfplumber fallback for tables |
| **Fixed-size chunker** | Configurable `chunk_size=512`, `overlap=50` tokens. Tokenizer: tiktoken or simple whitespace |
| **Embedding pipeline** | sentence-transformers `all-MiniLM-L6-v2`, embed chunks, upsert to Qdrant with metadata payload |
| **Dense retrieval** | Embed query, search Qdrant collection (scoped to tenant namespace), return top-K chunks |
| **Simple query endpoint** | `POST /api/v1/query` — dense-only retrieval, return raw chunks (no LLM generation yet) |

---

## Phase 2 — Ingestion & Retrieval Pipeline

### 2.1 Additional Document Extractors

| Task | Details |
|------|---------|
| **DOCX extractor** | `python-docx` — extract paragraphs with heading detection for section metadata |
| **HTML extractor** | `BeautifulSoup` — strip tags, preserve heading hierarchy as section metadata |
| **Markdown extractor** | `markdown` lib — parse headings as section boundaries, extract plain text |
| **Extractor factory** | Map file extension to extractor class; raise `UnsupportedFormat` for unknown types |
| **Metadata enrichment** | Every chunk carries: `tenant_id`, `document_id`, `document_name`, `page_number`, `section_heading`, `upload_date`, `category`, `chunk_index`, `chunking_strategy` |

### 2.2 Advanced Chunking Strategies

| Task | Details |
|------|---------|
| **Semantic chunking** | Embed sentences with sentence-transformers. Compute cosine similarity between consecutive sentences. Split where similarity drops below threshold (configurable, default: 0.75). Merge small chunks up to max token limit |
| **Parent-child chunking** | Create large parent chunks (~2048 tokens). Split each parent into small child chunks (~256 tokens). Store child chunks in Qdrant for retrieval. At query time, retrieve children but return parent chunk for generation context |
| **Strategy selector** | Ingestion accepts `chunking_strategy` param: `fixed`, `semantic`, `parent_child`. Default: `semantic` |
| **Document list endpoint** | `GET /api/v1/documents` — paginated list for tenant. `GET /api/v1/documents/{id}` — detail + status |
| **Document delete** | `DELETE /api/v1/documents/{id}` — remove from PostgreSQL + delete chunks from Qdrant + update BM25 index |

### 2.3 Sparse Retrieval & Hybrid Search

| Task | Details |
|------|---------|
| **BM25 index** | Per-tenant BM25 index using `rank_bm25`. Rebuild on document ingestion/deletion. Store tokenized corpus in Redis (serialized) for persistence across restarts |
| **Sparse retriever** | Tokenize query, score against tenant's BM25 index, return top-K chunks with BM25 scores |
| **RRF fusion** | `RRF_score(d) = Σ 1/(k + rank_i(d))` where `k=60` (standard). Merge dense and sparse result sets. Configurable `alpha` weight parameter |
| **Hybrid retrieval pipeline** | `query → [dense_retriever, sparse_retriever] → RRF fusion → candidate set` |

### 2.4 Reranking

| Task | Details |
|------|---------|
| **Cohere Rerank** | Call Cohere Rerank API with query + candidate chunks. Reorder by relevance score. Configurable `top_n` (default: 5) results after reranking |
| **Local cross-encoder fallback** | `cross-encoder/ms-marco-MiniLM-L-6-v2` via sentence-transformers. Auto-fallback if Cohere API fails or is not configured |
| **Reranker interface** | Abstract base; `CohereReranker` and `CrossEncoderReranker` implementations. Config flag to choose primary |

### 2.5 Metadata Filtering

| Task | Details |
|------|---------|
| **Filter schema** | Query accepts optional `filters`: `{ "document_ids": [...], "date_range": {"start": ..., "end": ...}, "categories": [...] }` |
| **Qdrant filtering** | Translate filter schema to Qdrant `Filter` conditions. Apply at vector search level (not post-filter) |
| **BM25 filtering** | Pre-filter BM25 corpus to matching documents before scoring |

---

## Phase 3 — Generation & Citations

### 3.1 LLM Integration

| Task | Details |
|------|---------|
| **LLM service** | Configurable LLM provider (OpenAI API compatible). System prompt enforces grounded responses: "Answer ONLY using the provided context. If the context doesn't contain the answer, say so. Cite sources using [Source N] format." |
| **Context formatting** | Format reranked chunks as numbered sources: `[Source 1] (doc_name, p.X): <chunk_text>` |
| **"I don't know" handling** | If top reranking score < configurable threshold (default: 0.3), return "insufficient information" response without calling LLM |

### 3.2 Citation Generation

| Task | Details |
|------|---------|
| **Citation builder** | Parse LLM response for `[Source N]` references. Map to citation objects: `{ "source_number": N, "document_name": "...", "page_number": X, "chunk_text": "...(truncated)", "relevance_score": 0.XX }` |
| **Query response schema** | `{ "answer": "...", "citations": [...], "query_metadata": { "latency_ms": {...}, "tokens": {...}, "retrieval_strategy": "hybrid" } }` |

### 3.3 SSE Streaming

| Task | Details |
|------|---------|
| **Streaming endpoint** | `POST /api/v1/query/stream` — returns `text/event-stream`. Events: `data: {"type": "token", "content": "..."}` during generation. Final event: `data: {"type": "citations", "citations": [...]}` |
| **sse-starlette** | Use `sse-starlette` for SSE response. Async generator yields token events from LLM streaming response |

### 3.4 Cost Tracking

| Task | Details |
|------|---------|
| **Token counting** | Count prompt tokens (context + query) and completion tokens from LLM response |
| **Cost estimation** | Configurable price per 1K tokens (prompt/completion). Calculate per-query cost |
| **Query logging** | Every query logged to `query_logs` table with: tenant_id, query_text, token counts, cost, latency breakdown |
| **Usage endpoint** | `GET /api/v1/admin/tenants/{id}/usage` — aggregated: total queries, total tokens, total cost, breakdown by date |

### 3.5 Rate Limiting

| Task | Details |
|------|---------|
| **Redis rate limiter** | Sliding window counter per tenant. Key: `rate:{tenant_id}:{minute_bucket}`. Check against `tenant.rate_limit_qpm` |
| **429 response** | Exceeding limit returns `429 Too Many Requests` with `Retry-After` header |

---

## Phase 4 — Evaluation & Optimization

### 4.1 Evaluation Dataset

| Task | Details |
|------|---------|
| **Curate eval set** | 50 questions in `eval/eval_set.json`: `{ "question": "...", "ground_truth": "...", "source_document": "...", "source_page": N }` |
| **Eval corpus** | Upload a set of test documents (varied formats) to a dedicated eval tenant |

### 4.2 RAGAS Evaluation Pipeline

| Task | Details |
|------|---------|
| **RAGAS runner** | `eval/run_ragas.py` — loads eval set, runs each question through query pipeline, collects: `question`, `answer`, `contexts`, `ground_truth`. Runs RAGAS metrics: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall` |
| **Result storage** | Save results to `eval_results` table with `run_id`, strategy, and scores |
| **Admin eval endpoints** | `POST /api/v1/admin/eval/run` — trigger eval. `GET /api/v1/admin/eval/results` — fetch historical results |

### 4.3 A/B Comparison & Reranking Analysis

| Task | Details |
|------|---------|
| **Hybrid vs. dense-only** | `eval/run_ab_comparison.py` — run eval set twice (hybrid, dense-only). Produce per-question and aggregate comparison. Store both result sets |
| **Reranking impact** | `eval/run_rerank_analysis.py` — run eval set with and without reranking. Log precision@5 and MRR before/after. Document improvement |

### 4.4 Performance Tuning

| Task | Details |
|------|---------|
| **Latency logging** | Per-query timing breakdown: `embedding_ms`, `retrieval_ms`, `reranking_ms`, `generation_ms`, `total_ms`. Include in response metadata |
| **Structured logging** | `structlog` JSON logs with `correlation_id` per request, propagated through all pipeline stages |
| **Parameter tuning** | Iterate on: `chunk_size`, `overlap`, `top_k`, `top_n`, `rrf_k`, `alpha`, `rerank_threshold` to hit RAGAS targets |

### 4.5 Load Testing

| Task | Details |
|------|---------|
| **Locust test** | `tests/load/locustfile.py` — simulate 100 concurrent users submitting queries. Assert: zero failures, p95 latency < 3s (excluding LLM) |
| **Report** | Generate load test report with latency distribution and error rates |

---

## Phase 5 — Polish & Documentation

### 5.1 Tenant Isolation Verification

| Task | Details |
|------|---------|
| **Isolation test** | `tests/integration/test_tenant_isolation.py` — create 2 tenants, upload distinct documents, run 100 cross-queries, assert zero foreign results |

### 5.2 Duplicate Detection (Could Have)

| Task | Details |
|------|---------|
| **Content hashing** | SHA-256 hash of file content on upload. Check against existing hashes for tenant. Return `409 Conflict` if duplicate |

### 5.3 Query Cache (Could Have)

| Task | Details |
|------|---------|
| **Redis cache** | Cache key: `cache:{tenant_id}:{hash(query+filters)}`. TTL configurable (default: 5 min). Log cache hit/miss |

### 5.4 Graceful Degradation

| Task | Details |
|------|---------|
| **Reranker fallback** | If Cohere API unreachable, auto-switch to local cross-encoder. Log warning |
| **Ingestion safety** | Failed ingestion rolls back: partial chunks deleted from Qdrant, document status set to `failed` with error message |

### 5.5 Documentation

| Task | Details |
|------|---------|
| **README.md** | Setup instructions, architecture diagram, API overview, eval results |
| **.env.example** | All env vars with descriptions and sensible defaults |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Qdrant over pgvector** as primary | Native namespace support maps cleanly to multi-tenancy; better hybrid search support. pgvector as documented lightweight alternative |
| **Async throughout** | FastAPI + asyncpg + async Qdrant client for concurrency under load |
| **Argon2 for API keys** | More resistant to GPU attacks than bcrypt; recommended by OWASP |
| **BM25 in Redis** | Serialized per-tenant index avoids memory loss on restart while keeping retrieval fast |
| **Configurable LLM** | OpenAI-compatible API means works with OpenAI, Claude (via proxy), local models (Ollama), etc. |
| **Parent chunk for generation** | Retrieve on precise child chunks but pass larger parent context to LLM — better answers with better precision |
| **Correlation IDs** | Every request gets a UUID propagated through logs for end-to-end traceability |

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/ragplatform

# Redis
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# LLM
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_PRICE_PROMPT_PER_1K=0.00015
LLM_PRICE_COMPLETION_PER_1K=0.0006

# Reranker
COHERE_API_KEY=...
RERANKER_TYPE=cohere  # or "cross_encoder"
CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Retrieval Defaults
DEFAULT_TOP_K=20
DEFAULT_TOP_N=5
RRF_K=60
RERANK_SCORE_THRESHOLD=0.3

# Chunking Defaults
DEFAULT_CHUNK_SIZE=512
DEFAULT_CHUNK_OVERLAP=50
DEFAULT_CHUNKING_STRATEGY=semantic
SEMANTIC_SIMILARITY_THRESHOLD=0.75

# Rate Limiting
DEFAULT_RATE_LIMIT_QPM=60

# Cache
QUERY_CACHE_TTL_SECONDS=300

# Admin
ADMIN_API_KEY=...  # Separate key for admin endpoints
```
