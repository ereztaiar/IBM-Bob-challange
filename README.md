# Website Vulnerability Checker

A monorepo web application that lets any user submit a URL and receive a structured
vulnerability report. An AI agent pipeline (LangChain / LangGraph) backed by a locally-running
Ollama LLM performs the scan; a RAG layer enriches findings with a vulnerability knowledge base
and past-scan history; results are stored in PostgreSQL + pgvector. Two React frontends
(user-facing and admin dashboard) consume a single Python FastAPI backend. Everything runs in
Docker Compose.

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

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Docker | 24+ with Compose v2 (`docker compose`) |
| Node.js | 20+ |
| pnpm | 9+ |
| Python | 3.12+ (for local dev outside Docker) |

---

## Setup

### 1. Clone and configure environment

```bash
git clone git@github.com:ereztaiar/IBM-Bob-challange.git
cd IBM-Bob-challange
cp .env.example .env
# Edit .env — at minimum change POSTGRES_PASSWORD, ADMIN_PASSWORD, and JWT_SECRET
```

### 2. Install Node dependencies (for local frontend dev)

```bash
npm install -g pnpm   # skip if pnpm is already installed
pnpm install
```

### 3. Start all services with Docker Compose

```bash
docker compose up --build
```

This starts six containers:

| Container | URL |
|---|---|
| `db` | `localhost:5432` |
| `ollama` | `localhost:11434` |
| `backend` | `http://localhost:8000` |
| `rag` | `http://localhost:8001` |
| `frontend-user` | `http://localhost:5173` |
| `frontend-admin` | `http://localhost:5174` |

> **Note:** The `ollama` container pulls `llama3` and `nomic-embed-text` on first boot.
> This can take several minutes depending on your internet connection.

### 4. Verify health

```bash
curl http://localhost:8000/health   # {"status": "ok"}
curl http://localhost:8001/health   # {"status": "ok"}
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### RAG service

```bash
cd rag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend (user)

```bash
cd frontend-user
pnpm install
pnpm dev   # http://localhost:5173
```

### Frontend (admin)

```bash
cd frontend-admin
pnpm install
pnpm dev   # http://localhost:5174
```

---

## Scripts (root workspace)

| Script | Description |
|---|---|
| `pnpm dev` | Start all frontend packages in dev mode |
| `pnpm lint` | Lint all frontend packages |
| `pnpm test` | Run all frontend test suites |

---

## Environment Variables

See [`.env.example`](.env.example) for the full list with descriptions.

---

## Project Structure

```
/
├── docker-compose.yml
├── .env.example
├── pnpm-workspace.yaml
├── package.json
├── frontend-user/        # React + Vite (port 5173)
├── frontend-admin/       # React + Vite (port 5174)
├── backend/              # Python FastAPI (port 8000)
├── rag/                  # Python FastAPI RAG service (port 8001)
└── db/
    └── init.sql          # pgvector extension bootstrap
```
