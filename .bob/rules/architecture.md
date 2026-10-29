# Architecture Rules

Derived from `AGENTS.md` and `.bob/memory/architecture.md`.

---

## Service Boundaries

Five Docker Compose services + one external VM:

| Service         | Port  | Responsibility                                      |
|-----------------|-------|-----------------------------------------------------|
| `db`            | 5432  | PostgreSQL + pgvector — data store only             |
| `rag`           | 8001  | RAG micro-service: knowledge base + scan history    |
| `backend`       | 8000  | FastAPI REST API + LangGraph scan pipeline          |
| `frontend-user` | 5173  | User-facing scanner (React/Vite)                    |
| `frontend-admin`| 5174  | Admin dashboard (React/Vite)                        |
| Ollama (VM)     | 11434 | External — referenced via `OLLAMA_BASE_URL` env var |

Startup order: `db → rag → backend → frontends` (health-checked in Compose).

---

## Agent Pipeline

Eight parallel `BaseCheck` agents → LangGraph supervisor → RAG enricher → report writer.

All Ollama client construction is in `backend/app/agents/llm_factory.py` and
`rag/app/services/embedder.py`. These are the **only** files that need to change when
migrating to IBM watsonx.ai — do not construct LLM clients anywhere else.

---

## Database Schema Rules

- `scans` rows use **soft-delete** (`deleted_at`); list queries must filter
  `WHERE deleted_at IS NULL`.
- Vector columns are `vector(768)` everywhere — do not use 1536.
- Admin auth uses `ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars, **not** the `admins` table.

---

## RAG Service Contract

- `/knowledge/ingest` — idempotent; content hash prevents duplicates (commit `7d429bd`).
- `/history/ingest` — called by `scan_runner.py` after every completed scan (commit `990745a`).
  Failures are logged as warnings and must **not** cause the scan to be marked `failed`.
- `/knowledge/query` and `/history/query` return vector-similarity results used by
  `rag_enricher.py` to enrich findings before the report writer runs.

---

## Security Rules

- All scan URLs pass through `backend/app/utils/url_validator.py` before any network
  request is made. This blocks private/loopback IPs and non-HTTP(S) schemes (SSRF protection).
- Ollama has **no authentication** — port 11434 must not be exposed to the internet; firewall
  to the Docker host only.

---

## Shared UI Rules

- `ui-shared/` is the **canonical** home for `NavBar`, `FindingCard`, `ReportView`,
  `ScanSpinner`. These components must not be re-implemented in `frontend-user` or
  `frontend-admin`.
- `ui-shared/src/styles/variables.css` is the **single source of truth** for design tokens
  (colours, spacing, font sizes).
- The `ui-shared` branch (`feat/ui-shared-consistent-styling`) must be merged before
  `ui-shared` imports resolve on `main`.
