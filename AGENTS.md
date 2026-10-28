# AGENTS.md — Website Vulnerability Checker

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

## Coding Standards

### Size Limits
- **Files:** max 300 lines. Extract to submodules when approaching the limit.
- **Functions/methods:** max 50 lines. Extract helpers rather than growing a function.

### Documentation
- **Python:** every function and class must have a docstring.
- **TypeScript:** every exported function and component must have a JSDoc comment.
- No undocumented public API surface.

### Python
- Type-annotate all function signatures.
- Use `async def` throughout the FastAPI layer.
- Pydantic v2 models for all request/response schemas.
- Naming: `snake_case` for variables and functions, `PascalCase` for classes.
- SOLID: single responsibility per module; use `BaseCheck` ABC for all agents.
- DRY: shared logic in `services/` or `utils/` — never copy-pasted.

### TypeScript / React
- Strict mode on; no `any`.
- Each React component in its own folder: `index.tsx` + CSS module + local types.
- Common hooks in `src/hooks/`, utilities in `src/utils/` — not duplicated per component.
- Naming: `camelCase` variables, `PascalCase` components and types.

### Frontend Styling (consistency rule)
- All shared visual components (`NavBar`, `FindingCard`, `ReportView`, `ScanSpinner`) must be imported from `ui-shared`, not re-implemented per frontend.
- CSS values (colours, spacing, font sizes) must use the design tokens in `ui-shared/src/styles/variables.css` — no hardcoded hex or pixel values in component CSS modules.
- Both `frontend-user` and `frontend-admin` are wired to `ui-shared` via the Vite alias `ui-shared → ../ui-shared/src`.

### Migrations
- Always generate an Alembic migration for every schema change; never alter the DB directly.
- Vector columns are `vector(768)` — matched to `nomic-embed-text`. Changing the embedding model requires a new migration.

### Tests
- Every new backend function/service needs a unit test.
- Mock all DB sessions and Ollama calls — no real network calls in tests.
- Frontend: Vitest + Testing Library; test each component and hook.

### Commits & Branches
- Conventional commits: `feat(scope):`, `fix(scope):`, `chore:`, `merge:`.
- Branch naming: `feat/<name>`, `fix/<name>`.

---

## Environment Variables

Copy `.env.example` to `.env`. Required:

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | PostgreSQL superuser password |
| `OLLAMA_BASE_URL` | Ollama VM URL, e.g. `http://192.168.1.50:11434` |
| `ADMIN_USERNAME` | Admin login (used for JWT validation — not the DB table) |
| `ADMIN_PASSWORD` | Admin password |
| `JWT_SECRET` | JWT signing secret (`openssl rand -hex 32`) |

See `.env.example` for the full list.
