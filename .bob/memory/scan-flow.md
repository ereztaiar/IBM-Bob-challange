# Scan Flow Memory

Complete step-by-step trace of how a URL submitted in the user frontend travels
through the backend, LangGraph agent pipeline, RAG service, and PostgreSQL —
ending with the report visible in the admin frontend.

---

## Phase 1 — User Frontend (port 5173)

1. `ScanForm/index.tsx` — user enters URL, client-side validation, calls `submitScan(url)` in `services/api.ts:19`.
2. `POST /scans` — payload `{url}`, returns `{scan_id, status:"pending"}`.
3. `useScanPoller.ts:28` — polls `GET /scans/{id}` every **3 seconds**. Stops on `status = "completed" | "failed"`.
4. `ScanSpinner` (from `ui-shared`) shown while running. Replaced by `ReportView` on completion.

---

## Phase 2 — Backend Request Layer (FastAPI, port 8000)

1. `routers/scans.py:submit_scan():57` — validates URL, calls `scan_service.create_scan(url, db)`, enqueues background task `scan_runner.run_scan(scan_id, url)`. Returns `status="pending"` immediately.
2. **DB WRITE** — `scans` row: `id` (UUID), `url`, `status="pending"`, `created_at`, `report_json=NULL`.
3. `routers/scans.py:get_scan_status():96` — each poll reads current row, returns `report_json` once set.

---

## Phase 3 — Background Task (scan_runner.py)

1. `scan_runner.run_scan():26` — **DB WRITE** `status="running"`, then calls `graph.build_scan_graph()` and `await graph.ainvoke()`.
2. On success: **DB WRITE** `status="completed"`, `completed_at`, full `report_json` (JSONB).
3. On error: **DB WRITE** `status="failed"`, `error_message`.
4. Fire-and-forget: `POST /rag/history/ingest` after completion.

---

## Phase 4 — LangGraph Pipeline (agents/graph.py)

Graph: `START → supervisor_node → [8 parallel check agents] → merge → rag_enricher → report_writer → END`

- `graph.build_scan_graph():70` — constructs the graph.
- `supervisor.supervisor_node():14` — initialises `AgentState`: `url, raw_responses=[], findings=[], rag_context=[], report=None`.

**8 parallel check agents** (all append to `state["findings"]` via `_merge_list` reducer):

| Agent | File | Detects |
|---|---|---|
| `XSSAgent` | `checks/xss.py` | Reflected XSS via query-param probes; missing CSP |
| `HeadersAgent` | `checks/headers.py` | Missing HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy |
| `SSLTLSAgent` | `checks/ssl_tls.py` | Cert validity/expiry, weak TLS versions, HTTP-only URLs |
| `CORSAgent` | `checks/cors.py` | Wildcard+credentials, origin reflection, null origin via OPTIONS preflight |
| `CookiesAgent` | `checks/cookies.py` | Missing HttpOnly, Secure, SameSite flags on Set-Cookie headers |
| `MapFilesAgent` | `checks/map_files.py` | Exposed `.js.map`/`.css.map` source-map files |
| `EnvExposureAgent` | `checks/env_exposure.py` | Publicly accessible `.env`, `config.json`, `.git/config`; regex credential detection |
| `SubdomainAgent` | `checks/subdomain.py` | Dangling CNAME takeover fingerprints (GitHub Pages, Heroku, AWS S3, Netlify, Azure…) |

All agents extend `BaseCheckAgent` (`checks/base.py`) — async httpx, 10 s timeout, spoofed UA.

---

## Phase 5 — RAG Enrichment (rag_enricher.py → RAG service, port 8001)

1. `rag_enricher.rag_enricher_node():72` — extracts unique finding categories from state.
2. Per category: `POST /rag/knowledge/query` → `vector_store.query_knowledge():58` — pgvector cosine search on `vulnerability_docs` table (embeds query via `nomic-embed-text`, 768-dim, `LIMIT 3`).
3. Per domain: `POST /rag/history/query` → `vector_store.query_scan_history():156` — pgvector cosine search on `scan_embeddings` table.
4. Results stored in `state["rag_context"]` as list of strings.

---

## Phase 6 — LLM Report Generation (report_writer.py → Ollama llama3)

1. `report_writer.report_writer_node():136` — extracts `findings` + `rag_context`.
2. `_build_prompt():23` — role: "senior web-application security analyst"; injects RAG snippets; requests JSON: `{url, summary, risk_score (0–100), findings[], recommendations[]}`.
3. `get_llm().ainvoke():159` — `llm_factory.py` returns `ChatOllama(llama3)`. **Single swap point for watsonx.ai.**
4. `_extract_json():68` — tries markdown code fence → raw JSON → first `{…}` block.
5. `_fallback_report():102` — if LLM fails: sorts by severity, `risk_score = critical×30 + high×15`, top-3 remediations.
6. Result → `state["report"]`.

---

## Phase 7 — Database Writes

1. **DB WRITE** `scans` — `status="completed"`, `completed_at`, `report_json` (full JSONB report).
2. Fire-and-forget `POST /rag/history/ingest` (`scan_runner.py:81`) — payload `{scan_id, domain, summary}`.
3. `vector_store.ingest_scan_embedding():126` — embeds summary via `nomic-embed-text` → writes `scan_embeddings` row: `scan_id, domain, summary, embedding (vector(768)), created_at`. Powers future RAG history lookups.

---

## Phase 8 — User Frontend Report Display

1. Next poll returns `status="completed"` + `report_json`. `useScanPoller.ts:46` clears interval.
2. `ui-shared/ReportView/index.tsx:39` renders: risk score badge (red ≥70 / amber ≥35 / green), summary, recommendations, findings sorted critical→info via `FindingCard`.

---

## Phase 9 — Admin Frontend (port 5174)

1. `loginAdmin()` → `POST /auth/admin/login` → JWT stored in session storage.
2. `DashboardPage` → `GET /admin/stats` → `admin_service.get_stats():126` → `{total, by_severity{}, today}` shown in `StatCard` components.
3. `useScanTable.ts` → `GET /admin/scans?page=…&status=…&severity=…` → `admin_service.list_scans():27` (paginated, filtered) → rendered in `ScanTable/index.tsx`.
4. Click "View" → navigate to `/scans/:id` → `ScanDetailPage`.
5. `getScanDetail(id)` → `GET /admin/scans/{id}` → `admin_service.get_scan_detail():93` → `SELECT * FROM scans WHERE id=? AND deleted_at IS NULL` → returns full `report_json`.
6. `ui-shared/ReportView` renders identical report view as user frontend.

---

## Key API Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/scans` | None | Submit URL for scanning |
| GET | `/scans/{id}` | None | Poll scan status + report |
| GET | `/admin/scans` | JWT | Paginated scan list with filters |
| GET | `/admin/scans/{id}` | JWT | Full scan detail + report_json |
| GET | `/admin/stats` | JWT | Aggregate severity counts |
| DELETE | `/admin/scans/{id}` | JWT | Soft-delete a scan |
| POST | `/rag/knowledge/query` | None | Vector search on vulnerability docs |
| POST | `/rag/history/query` | None | Vector search on past scan summaries |
| POST | `/rag/history/ingest` | None | Store new scan summary embedding |
