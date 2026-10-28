# RAG Bug Fixes Plan

## Top-Level Overview

Three bugs prevent the RAG pipeline from working end-to-end:

1. **Vector dimension mismatch** — all `Vector(1536)` columns and the Alembic migration need to be changed to `Vector(768)` to match `nomic-embed-text` output. Until this is fixed, every `ingest` call will raise a pgvector dimension-check error.
2. **Scan history is never written** — after a scan completes, `scan_runner.py` does not call `POST /rag/history/ingest`, so `scan_embeddings` remains empty and history context is always absent from reports.
3. **Duplicate knowledge documents** — the `/rag/knowledge/ingest` endpoint docstring promises duplicate detection (HTTP 200) but the router never calls `document_exists`. Two identical POST requests insert two identical rows.

The fixes are minimal and surgical: no new abstractions, no redesign.

---

## Sub-Tasks

---

### Sub-task 1 — Fix vector dimension: 1536 → 768

**Intent**  
`nomic-embed-text` emits 768-dimension vectors. Every `Vector(1536)` declaration must become `Vector(768)` so pgvector accepts rows from the embedder. There are three places: two ORM models and the Alembic migration.

Because the initial migration has already been applied to any running database, a second migration is needed to `ALTER` the existing columns rather than recreating them from scratch.

**Expected Outcomes**
- `rag/app/db/models/vulnerability_doc.py` uses `Vector(768)`.
- `rag/app/db/models/scan_embedding.py` uses `Vector(768)`.
- The initial migration `ed96e6207148` is updated to use `Vector(768)` (covers fresh installs).
- A new Alembic migration (e.g. `fix_vector_dimension_768`) runs `ALTER COLUMN … TYPE vector(768)` for both tables and downgrades back to `vector(1536)` (covers existing databases).
- Calling `/rag/knowledge/ingest` no longer raises a pgvector dimension error.

**Todo List**
- [ ] Change `Vector(1536)` to `Vector(768)` in `rag/app/db/models/vulnerability_doc.py` line 34.
- [ ] Change `Vector(1536)` to `Vector(768)` in `rag/app/db/models/scan_embedding.py` line 34.
- [ ] Change `Vector(1536)` to `Vector(768)` in `rag/app/db/migrations/versions/ed96e6207148_initial_schema.py` lines 31 and 47 (covers clean install).
- [ ] Create a new Alembic migration file (e.g. `rag/app/db/migrations/versions/a1b2c3d4e5f6_fix_vector_dim_768.py`) that ALTERs both columns to `vector(768)` in upgrade and back to `vector(1536)` in downgrade.
- [ ] Update docstrings in both model files to say "768-dimensional" instead of "1536-dimensional".

**Relevant Context**
- `rag/app/db/models/vulnerability_doc.py` — `VulnerabilityDoc.embedding` line 34
- `rag/app/db/models/scan_embedding.py` — `ScanEmbedding.embedding` line 34
- `rag/app/db/migrations/versions/ed96e6207148_initial_schema.py` — lines 31, 47
- `rag/app/config.py` — confirms `OLLAMA_EMBED_MODEL = "nomic-embed-text"`

**Status** — `[ ] pending`

---

### Sub-task 2 — Write scan history after each completed scan

**Intent**  
`scan_runner.py` transitions a scan to `completed` but never posts the scan summary to `POST /rag/history/ingest`. The fix is to call that endpoint inside `run_scan` after the report is available, passing `scan_id`, the extracted domain, and the report's `summary` string.

The call should be fire-and-forget with a logged warning on failure — a history-write error must not cause the scan itself to be marked `failed`.

**Expected Outcomes**
- After a scan completes successfully, a `POST /rag/history/ingest` is made to the RAG service.
- `scan_embeddings` accumulates rows; subsequent scans of the same domain receive historical context.
- A failure in the history POST is logged as a warning and does not propagate.

**Todo List**
- [ ] In `backend/app/services/scan_runner.py`, after the `update_scan_status(..., "completed", ...)` call, add an async helper (or inline block) that:
  - Extracts the domain from `url` using `urlparse`.
  - Reads `report.get("summary", "")`.
  - POSTs to `f"{settings.RAG_SERVICE_URL}/rag/history/ingest"` with `scan_id`, `domain`, and `summary`.
  - Catches all exceptions and logs a warning without re-raising.
- [ ] Add `from urllib.parse import urlparse` and `import httpx` imports to `scan_runner.py`.
- [ ] Add `from app.config import settings` import to `scan_runner.py`.

**Relevant Context**
- `backend/app/services/scan_runner.py` — `run_scan` function, completion block lines 59–68
- `backend/app/agents/rag_enricher.py` — shows the expected JSON payload shape (`{"scan_id": ..., "domain": ..., "summary": ...}`)
- `rag/app/routers/history.py` — the `/rag/history/ingest` endpoint
- `rag/app/schemas.py` — `HistoryIngestRequest` fields: `scan_id: str`, `domain: str`, `summary: str`
- `backend/app/config.py` — `settings.RAG_SERVICE_URL`

**Status** — `[ ] pending`

---

### Sub-task 3 — Add duplicate detection to the knowledge ingest endpoint

**Intent**  
The `/rag/knowledge/ingest` router docstring advertises duplicate detection (returns HTTP 200) but the code skips it entirely — `vector_store.document_exists` exists but is never called. Two POST requests with the same payload insert two identical rows.

The fix is to call `document_exists` before `ingest_document` in the router; if it returns `True`, query and return the existing document with HTTP 200.

**Expected Outcomes**
- A second POST to `/rag/knowledge/ingest` with the same `category` + `title` returns HTTP 200 (not 201) and does not insert a duplicate row.
- The docstring now matches the actual behavior.
- The seed script's own HTTP-level duplicate check remains (belt-and-suspenders); no changes needed there.

**Todo List**
- [ ] In `rag/app/routers/knowledge.py`, before calling `ingest_document`, call `vector_store.document_exists(category, title)`.
- [ ] If `document_exists` returns `True`, perform a `query_knowledge` for the title (top_k=1) to retrieve the existing doc, and return `KnowledgeIngestResponse` with `status_code=200`.
- [ ] Alternatively (simpler): query directly via `AsyncSessionLocal` in `vector_store` — add a `get_document_by_category_title` helper that returns the doc or `None`, then use that in the router.
- [ ] Ensure the response for a duplicate sets `status_code=status.HTTP_200_OK` on the `Response` object (requires adding a `Response` parameter to the endpoint or using `JSONResponse`).
- [ ] Update the router's `status_code` on the decorator to stay 201 (the default for new inserts); only the duplicate path returns 200.

**Relevant Context**
- `rag/app/routers/knowledge.py` — `ingest_knowledge` function lines 24–53
- `rag/app/services/vector_store.py` — `document_exists` function lines 81–98; `ingest_document` lines 26–55
- FastAPI pattern: inject `response: Response` parameter and set `response.status_code = 200` to override the decorator default

**Status** — `[ ] pending`
