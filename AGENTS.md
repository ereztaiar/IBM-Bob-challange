# AGENTS.md — Website Vulnerability Checker

## Bob Memory

Project-specific memory is stored in `.bob/memory/` and is read by Bob at the
start of each session to restore context without re-exploring the codebase.

| File | Contents |
|---|---|
| `architecture.md` | Service topology, DB schema, LangGraph pipeline overview, auth, Docker startup order |
| `decisions.md` | Recorded design and technology decisions with commit references |
| `known-issues.md` | Fixed bugs and open issues with root-cause notes |
| `scan-flow.md` | Complete step-by-step trace of a scan: user frontend → agents → RAG → DB → admin report |

---

## Project

A monorepo web application: users submit a URL and receive a structured
vulnerability report. A multi-agent LangGraph pipeline (Ollama LLM) performs
the scan; a RAG layer enriches findings; results are stored in PostgreSQL +
pgvector. Two React frontends consume a single FastAPI backend, all in Docker
Compose.

**Stack:** Python 3.12 · FastAPI · LangGraph · Ollama (`llama3` + `nomic-embed-text`) · PostgreSQL + pgvector · React + Vite + TypeScript · pnpm workspaces

---

## Services & Ports

| Service | Port | Purpose |
|---|---|---|
| `db` | 5432 | PostgreSQL + pgvector |
| `rag` | 8001 | RAG micro-service (knowledge base + scan history) |
| `backend` | 8000 | FastAPI REST API + LangGraph scan pipeline |
| `frontend-user` | 5173 | User-facing scanner |
| `frontend-admin` | 5174 | Admin dashboard |
| Ollama | 11434 | External VM — set `OLLAMA_BASE_URL` in `.env` |

Start: `docker compose up --build`

---

## Repository Structure

```
/
├── docker-compose.yml
├── .env.example
├── db/init.sql                     # pgvector bootstrap
├── backend/app/
│   ├── main.py                     # create_app() factory
│   ├── config.py                   # Pydantic Settings
│   ├── dependencies.py             # get_db, get_current_admin
│   ├── routers/                    # health, auth, scans, admin
│   ├── schemas/                    # Pydantic request/response models
│   ├── services/                   # scan_service, auth_service, admin_service, scan_runner
│   ├── agents/                     # LangGraph pipeline + 8 check agents
│   └── db/                         # SQLAlchemy models + Alembic migrations
├── rag/app/
│   ├── routers/                    # knowledge (ingest/query), history
│   └── services/                   # embedder, vector_store
├── frontend-user/src/
│   ├── components/                 # NavBar, MetaTagGate, ScanForm, ScanSpinner, ReportView
│   ├── hooks/                      # useScanPoller
│   ├── pages/                      # HomePage
│   └── services/                   # api.ts
├── frontend-admin/src/
│   ├── components/                 # NavBar, LoginForm, ProtectedRoute, StatCard, ScanTable, ReportView
│   ├── hooks/                      # useAuth
│   ├── pages/                      # LoginPage, DashboardPage, ScanDetailPage
│   └── services/                   # api.ts
└── ui-shared/src/
    ├── components/                 # NavBar, FindingCard, ReportView, ScanSpinner (canonical)
    └── styles/                     # variables.css (design tokens), base.css
```

---

## Agent Pipeline (`backend/app/agents/`)

Eight parallel check agents → LangGraph supervisor → RAG enricher → Ollama report writer.

| File | Detects |
|---|---|
| `checks/xss.py` | Reflected XSS via query-parameter reflection |
| `checks/headers.py` | Missing security headers (HSTS, CSP, X-Frame-Options) |
| `checks/ssl_tls.py` | Weak cipher suites, expired certs, TLS version |
| `checks/cors.py` | Overly permissive CORS |
| `checks/cookies.py` | Missing `HttpOnly`, `Secure`, `SameSite` flags |
| `checks/map_files.py` | Exposed `.js.map` / `.css.map` source-map files |
| `checks/env_exposure.py` | Publicly accessible `.env` / `config.json` / credential files |
| `checks/subdomain.py` | Subdomain takeover via dangling DNS CNAMEs |

Key files:
- `graph.py` — LangGraph node wiring
- `supervisor.py` — collects agent outputs
- `rag_enricher.py` — enriches findings with RAG context
- `report_writer.py` — calls Ollama to generate final report
- `llm_factory.py` — **single swap point for watsonx.ai** (`ChatOllama` / `OllamaEmbeddings`)
- `state.py` — shared LangGraph state
- `checks/base.py` — `BaseCheck` abstract class

---

## Rules

Enforceable coding standards, architecture constraints, and environment setup
are defined in `.bob/rules/` and are automatically loaded by Bob in every session:

- `.bob/rules/coding-standards.md` — size limits, docs, Python, TypeScript, tests, commits
- `.bob/rules/architecture.md` — service boundaries, agent pipeline, DB rules, RAG contract
- `.bob/rules/environment.md` — required env vars, Ollama VM setup, embedding model
