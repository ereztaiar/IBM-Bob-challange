# Website Vulnerability Checker

A monorepo web application that lets any user submit a URL and receive a structured
vulnerability report. A multi-agent LangGraph pipeline backed by a locally-running
Ollama LLM performs the scan; a RAG layer enriches findings with a vulnerability
knowledge base and past-scan history; results are stored in PostgreSQL + pgvector.
Two React frontends (user-facing and admin dashboard) consume a single Python
FastAPI backend. Everything runs in Docker Compose.

---

## Architecture

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
  └──► ollama:11434  (local LLM — llama3 / nomic-embed-text)
```

### Vulnerability checks

| Agent | What it detects |
|---|---|
| `xss` | Reflected XSS via query-parameter reflection |
| `headers` | Missing security headers (HSTS, CSP, X-Frame-Options, …) |
| `ssl_tls` | Weak cipher suites, expired certificates, TLS version |
| `cors` | Overly permissive CORS (reflected Origin, wildcard + credentials) |
| `cookies` | Missing `HttpOnly`, `Secure`, or `SameSite` flags |
| `map_files` | Exposed `.js.map` / `.css.map` source-map files |
| `env_exposure` | Publicly accessible `.env` / `config.json` / credential files |
| `subdomain` | Subdomain takeover indicators (dangling DNS CNAMEs) |

---

## Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| Docker | 24+ with Compose v2 | `docker compose` (no hyphen) |
| Node.js | 20+ | For local frontend dev only |
| npm | 10+ | Bundled with Node 20 |
| Python | 3.12+ | For local backend dev only |

> **GPU / RAM:** The Ollama container downloads `llama3` (~4.7 GB) and
> `nomic-embed-text` (~300 MB) on first boot. Allow at least 8 GB of free RAM
> and expect the first startup to take several minutes.

---

## Quick start (Docker Compose)

### 1. Clone and configure

```bash
git clone git@github.com:ereztaiar/IBM-Bob-challange.git
cd IBM-Bob-challange

# Copy the example env file and set your own secrets
cp .env.example .env
```

Open `.env` and update at minimum:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Strong password for the PostgreSQL superuser |
| `ADMIN_USERNAME` | Admin dashboard login username |
| `ADMIN_PASSWORD` | Admin dashboard login password |
| `JWT_SECRET` | Long random string used to sign JWTs |

### 2. Start all services

```bash
docker compose up --build
```

Docker Compose starts six containers in dependency order:

| Container | URL | Purpose |
|---|---|---|
| `db` | `localhost:5432` | PostgreSQL + pgvector |
| `ollama` | `localhost:11434` | Local LLM (llama3 + nomic-embed-text) |
| `rag` | `http://localhost:8001` | RAG micro-service (seeds KB on first boot) |
| `backend` | `http://localhost:8000` | FastAPI REST API |
| `frontend-user` | `http://localhost:5173` | User-facing scanner UI |
| `frontend-admin` | `http://localhost:5174` | Admin dashboard |

> **First boot note:** `ollama` pulls ~5 GB of model data before it becomes
> healthy. The `rag`, `backend`, and frontend containers wait for their
> upstream dependencies to pass health checks before starting.

### 3. Verify health

```bash
curl http://localhost:8000/health   # {"status": "ok"}
curl http://localhost:8001/health   # {"status": "ok"}
```

### 4. Run a scan

1. Open `http://localhost:5173`
2. Acknowledge the responsible-use gate (valid for 30 minutes per session)
3. Enter a URL (e.g. `https://example.com`) and click **Scan**
4. The spinner polls every 3 seconds until the scan completes
5. The structured report renders in-page with severity-coded finding cards

---

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Copy env and point DATABASE_URL at a local Postgres instance
cp ../.env.example .env

uvicorn app.main:app --reload --port 8000
```

Run database migrations:

```bash
alembic upgrade head
```

### RAG service

```bash
cd rag
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Seed the knowledge base (requires the RAG service to be running):

```bash
python -m seeds.seed
```

### Frontend (user)

```bash
cd frontend-user
npm install
npm run dev   # http://localhost:5173
```

### Frontend (admin)

```bash
cd frontend-admin
npm install
npm run dev   # http://localhost:5174
```

---

## Running tests

### Backend (unit + integration)

```bash
cd backend
python -m pytest tests/ -v
```

36 tests: 31 unit + 5 integration. No database or Ollama required — all external
calls are mocked via SQLite (aiosqlite) and `unittest.mock`.

### RAG service

```bash
cd rag
python -m pytest tests/ -v
```

6 tests.

### User frontend

```bash
cd frontend-user
npm test
```

17 tests (Vitest + Testing Library).

### Admin frontend

```bash
cd frontend-admin
npm test
```

22 tests (Vitest + Testing Library).

---

## Environment variables

See [`.env.example`](.env.example) for the full list with descriptions. Key variables:

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | — | **Required.** PostgreSQL password |
| `POSTGRES_DB` | `vulnchecker` | Database name |
| `DATABASE_URL` | — | Full async DSN for SQLAlchemy |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama service URL |
| `OLLAMA_MODEL` | `llama3` | Chat model name |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model name |
| `ADMIN_USERNAME` | — | **Required.** Admin login username |
| `ADMIN_PASSWORD` | — | **Required.** Admin login password |
| `JWT_SECRET` | — | **Required.** JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime in minutes |
| `RAG_SERVICE_URL` | `http://rag:8001` | RAG service URL (used by backend) |
| `FRONTEND_USER_URL` | `http://localhost:5173` | Allowed CORS origin (user frontend) |
| `FRONTEND_ADMIN_URL` | `http://localhost:5174` | Allowed CORS origin (admin frontend) |

---

## Project structure

```
/
├── docker-compose.yml          # All six services with health checks and ordering
├── .env.example                # Environment variable template
├── package.json                # Root npm workspace config
├── db/
│   └── init.sql                # pgvector extension bootstrap
│
├── backend/                    # Python FastAPI (port 8000)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── app/
│       ├── main.py             # create_app() factory
│       ├── config.py           # Pydantic Settings
│       ├── dependencies.py     # get_db, get_current_admin
│       ├── routers/            # health, auth, scans, admin
│       ├── schemas/            # Pydantic request/response models
│       ├── services/           # scan_service, auth_service, admin_service, scan_runner
│       ├── agents/             # LangGraph pipeline + 8 check agents
│       └── db/                 # SQLAlchemy models + Alembic migrations
│
├── rag/                        # Python FastAPI RAG service (port 8001)
│   ├── Dockerfile              # Seeds knowledge base on first boot
│   ├── requirements.txt
│   ├── seeds/
│   │   ├── seed.py             # Idempotent seed script
│   │   └── vulnerability_definitions.json
│   └── app/
│       ├── routers/            # knowledge (ingest/query), history
│       └── services/           # embedder, vector_store
│
├── frontend-user/              # React + Vite (port 5173)
│   ├── Dockerfile
│   └── src/
│       ├── components/         # NavBar, MetaTagGate, ScanForm, ScanSpinner, ReportView
│       ├── hooks/              # useScanPoller
│       ├── pages/              # HomePage
│       └── services/           # api.ts (submitScan, getScanStatus)
│
└── frontend-admin/             # React + Vite (port 5174)
    ├── Dockerfile
    └── src/
        ├── components/         # NavBar, LoginForm, ProtectedRoute, StatCard, ScanTable, ReportView
        ├── hooks/              # useAuth
        ├── pages/              # LoginPage, DashboardPage, ScanDetailPage
        └── services/           # api.ts (login, listScans, getScanDetail, getStats, deleteScan)
```

---

## API reference

### Public endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/auth/login` | Admin login → JWT |
| `POST` | `/scans` | Submit a URL for scanning |
| `GET` | `/scans/{id}` | Poll scan status / retrieve report |

### Admin endpoints (JWT required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/admin/scans` | Paginated scan list (filter by status) |
| `GET` | `/admin/scans/{id}` | Full scan detail including report JSON |
| `GET` | `/admin/stats` | Aggregate statistics (counts, severity breakdown) |
| `DELETE` | `/admin/scans/{id}` | Soft-delete a scan |

Interactive API docs are available at `http://localhost:8000/docs` when the
backend is running.

---

## Future roadmap

| Feature | Notes |
|---|---|
| User accounts | `users` table, JWT auth, "My Scans" history |
| IBM watsonx.ai | Swap `ChatOllama` / `OllamaEmbeddings` in `llm_factory.py` and `embedder.py` |
| Paid tiers | Rate-limiting, scan quotas, payment integration |
| Shareable reports | UUID-based public report URLs with optional expiry |
| Sub-page crawling | Follow links up to a configurable depth |
| WebSocket progress | Replace polling with real-time per-agent progress stream |
