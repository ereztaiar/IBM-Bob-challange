# Architecture Memory

## Service Topology

```
Browser (User)          Browser (Admin)
     │                        │
     ▼                        ▼
frontend-user:5173     frontend-admin:5174
     │                        │
     └──────────┬─────────────┘
                ▼
         backend:8000  (FastAPI)
          │        │
          │        └──► rag:8001  (FastAPI + pgvector)
          │                  │
          └──────────────────┴──► db:5432  (PostgreSQL + pgvector)

backend + rag also call:
  └──► Ollama on a separate VM ($OLLAMA_BASE_URL, port 11434)
       Models: llama3 (chat), nomic-embed-text (embeddings, 768-dim vectors)
```

## Database Schema (PostgreSQL + pgvector)

### `backend` service (via Alembic migrations)
- `scans` — id (UUID), url, status (pending/running/complete/failed), report (JSONB), created_at, deleted_at (soft-delete)
- `findings` — id, scan_id (FK), agent_name, severity (critical/high/medium/low/info), title, description, recommendation
- `admins` — id, username, hashed_password (unused at runtime — admin validated from env vars only)

### `rag` service (via Alembic migrations)
- `vulnerability_docs` — id, content, embedding (vector(768)), metadata (JSONB)
- `scan_embeddings` — id, scan_id, summary, embedding (vector(768)), metadata (JSONB)

**Critical:** vector columns are `vector(768)` — matched to `nomic-embed-text` output. Earlier revisions used 1536 (OpenAI-style); migration `a1b2c3d4e5f6` corrected this.

## LangGraph Agent Pipeline

Located in `backend/app/agents/`.

1. Eight `BaseCheck` subclasses run in parallel LangGraph nodes.
2. `supervisor.py` collects all findings into shared `ScanState`.
3. `rag_enricher.py` calls `rag:8001/knowledge/query` for each finding category to append CVE/advisory context.
4. `report_writer.py` calls Ollama (`llama3`) to synthesise a final JSON report.

`llm_factory.py` centralises all Ollama client construction — this is the **single swap-point** for moving to IBM watsonx.ai.

## RAG Service

Located in `rag/`.

- `/knowledge/ingest` — POST; embeds text with `nomic-embed-text` and upserts into `vulnerability_docs`. Duplicate detection added (hash-based, commit `7d429bd`).
- `/knowledge/query` — POST; vector-similarity search against `vulnerability_docs`.
- `/history/ingest` — POST; stores a completed scan summary embedding in `scan_embeddings`. Called by backend after scan completes (commit `990745a`).
- `/history/query` — POST; retrieves similar past scans.

Seed data: `rag/seeds/vulnerability_definitions.json` is loaded idempotently on container start via `rag/seeds/seed.py`.

## SSRF Protection

`backend/app/utils/url_validator.py` — blocks private/loopback IP ranges and non-HTTP(S) schemes before a scan is accepted.

## Auth

- Admin: single-user, credentials from `ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars. JWT signed with `JWT_SECRET`. JWT validation checks against env vars, **not** the `admins` table (fixed in commit `27d8c21`).
- No user-level authentication in v1.

## Frontend Shared Components (`ui-shared/`)

Added in the latest unmerged commit (`f87ddda`, branch `feat/ui-shared-consistent-styling`).  
Provides canonical `NavBar`, `FindingCard`, `ReportView`, `ScanSpinner` components and CSS design-token variables consumed by both `frontend-user` and `frontend-admin` via a Vite path alias (`ui-shared → ../ui-shared/src`).

## Docker Compose Startup Order

`db` → `rag` (waits for db health) → `backend` (waits for rag health) → frontends (wait for backend health). Migrations run at container start (`alembic upgrade head`).
