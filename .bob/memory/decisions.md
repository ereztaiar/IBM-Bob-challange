# Decisions Memory

Recorded decisions made during development, derived from git history, commit
messages, plan documents, and build notes.

---

## Ollama runs on a separate VM (not in Docker Compose)

**Commit:** `1794ea1` — `feat(compose): use external Ollama server on a VM`  
**Reason:** Ollama requires significant RAM (8 GB+ for llama3) and optionally a GPU. Running it inside Docker Compose on a dev machine would be impractical.  
**Implementation:** `OLLAMA_BASE_URL` env var points to the VM's IP. `rag` and `backend` refuse to start if this variable is unset.  
**Security note:** Ollama has no authentication — port 11434 must **not** be exposed to the internet; firewall to the Docker host only.

---

## Admin authentication uses env vars, not the `admins` DB table

**Commit:** `27d8c21` — `fix(backend): validate admin JWT against ADMIN_USERNAME, not the admins table`  
**Reason:** The `admins` table was seeded but the JWT validation code was checking env vars at login time yet the DB at verify time, causing a mismatch after restarts.  
**Decision:** `ADMIN_USERNAME` / `ADMIN_PASSWORD` are the sole source of truth. The `admins` table remains but is not used for auth in v1.

---

## Vector dimension is 768, not 1536

**Commit:** `ea46665` / migration `a1b2c3d4e5f6` — `fix: resize vector columns from 1536 to 768 for nomic-embed-text`  
**Reason:** Initial implementation used 1536 (matching OpenAI's `text-embedding-ada-002`). The project uses `nomic-embed-text` via Ollama, which outputs 768-dimensional vectors. Mismatched dimensions caused pgvector insert failures.  
**Action taken:** Alembic migration added to `ALTER COLUMN` both vector columns in `rag` service.

---

## Scan history is posted to RAG after completion

**Commit:** `990745a` — `fix: post scan summary to RAG history ingest after scan completes`  
**Reason:** The RAG service has a `/history/ingest` endpoint for storing past scan embeddings so future scans can retrieve similar previous results. The backend was not calling it.  
**Implementation:** `scan_runner.py` calls `rag:8001/history/ingest` with a scan summary after a scan reaches `complete` status.

---

## Knowledge ingest endpoint has duplicate detection

**Commit:** `7d429bd` — `fix: add duplicate detection to knowledge ingest endpoint`  
**Reason:** Re-seeding the knowledge base (e.g., on container restart) was creating duplicate embeddings, inflating vector search results.  
**Implementation:** Hash of the content string is checked before inserting; existing entries are skipped.

---

## Five services in Compose, not six

**Commit:** `83ce412` — README correction: "All six services" → "All five services"  
**Reason:** Ollama was briefly planned as a Compose service but was moved to the VM. The README incorrectly said six.

---

## Shared UI component library (`ui-shared`)

**Commit:** `f87ddda` — `feat: add ui-shared package for consistent styling across frontends`  
**Reason:** `frontend-user` and `frontend-admin` duplicated `NavBar`, `FindingCard`, `ReportView`, and `ScanSpinner` with diverging styles (different hex values, badge casing, padding).  
**Implementation:** New pnpm workspace package `ui-shared` with CSS design tokens (`variables.css`). Both frontends import via Vite alias `ui-shared → ../ui-shared/src`. This commit is on branch `feat/ui-shared-consistent-styling` and is **not yet merged** to `main`.

---

## SSRF protection before scan execution

**Plan:** Sub-Task 4  
**Implementation:** `backend/app/utils/url_validator.py` rejects private/loopback IP ranges and non-HTTP(S) schemes at scan submission time, before any network request is made by the agent pipeline.

---

## LangGraph chosen for agent orchestration

**Plan:** Sub-Task 6  
**Reason:** LangGraph provides explicit state management and parallel node execution, which maps cleanly to running all 8 check agents concurrently then aggregating into a single report.

---

## `llm_factory.py` as single watsonx.ai swap point

**Plan:** Sub-Task 6 / Future roadmap  
**Decision:** All Ollama client construction (`ChatOllama`, `OllamaEmbeddings`) is isolated in `backend/app/agents/llm_factory.py` and `rag/app/services/embedder.py`. Migrating to IBM watsonx.ai requires changes only in these two files.

---

## Soft-delete for scans

**Commit:** `5fdf7b4` / migration `c3f1d89a4b22` — `feat(backend): ST9 admin endpoints`  
**Reason:** Admin `DELETE /admin/scans/{id}` should not destroy report data permanently (audit trail).  
**Implementation:** `deleted_at` timestamp column added to `scans`; list queries filter `WHERE deleted_at IS NULL`.

---

## MetaTagGate responsible-use gate (30-minute session)

**Plan:** Sub-Task 7  
**Reason:** Prevent accidental or automated scanning; requires an explicit acknowledgment before the scan form is shown. Valid for 30 minutes per browser session (sessionStorage).
