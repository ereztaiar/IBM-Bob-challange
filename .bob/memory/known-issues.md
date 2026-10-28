# Known Issues & Gotchas Memory

Issues discovered and fixed during development. Useful context when debugging
regressions or related problems.

---

## Vector dimension mismatch (1536 vs 768)

**Status:** Fixed — migration `a1b2c3d4e5f6` in `rag/app/db/migrations/versions/`  
**Symptom:** pgvector INSERT fails with dimension mismatch error.  
**Root cause:** Initial schema used 1536 dimensions (OpenAI convention). `nomic-embed-text` produces 768-dim vectors.  
**Fix:** Alembic migration alters both `vulnerability_docs.embedding` and `scan_embeddings.embedding` to `vector(768)`.  
**Watch out for:** If a new embedding model is adopted, both columns and the `OLLAMA_EMBED_MODEL` env var must be updated together.

---

## Admin JWT validation against DB instead of env vars

**Status:** Fixed — commit `27d8c21`  
**Symptom:** Admin could log in successfully but subsequent API calls returned 401 after a container restart.  
**Root cause:** `auth_service.py` login checked env vars; token verification code checked the `admins` DB table, which may not be seeded identically after restart.  
**Fix:** Both login and verification now use `ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars exclusively.

---

## RAG scan history not populated

**Status:** Fixed — commit `990745a`  
**Symptom:** `/history/query` always returned empty results; RAG enrichment never used past scan data.  
**Root cause:** `scan_runner.py` completed scans but never called `rag:8001/history/ingest`.  
**Fix:** Added a POST call to `/history/ingest` with a scan summary string after the scan pipeline completes.

---

## Knowledge base duplicate embeddings on re-seed

**Status:** Fixed — commit `7d429bd`  
**Symptom:** Vector similarity scores degraded; duplicate results returned from `/knowledge/query`.  
**Root cause:** `rag/seeds/seed.py` is run on every container start. Without deduplication, every restart doubled the knowledge base.  
**Fix:** Content hash check in the `/knowledge/ingest` handler; entries with a matching hash are skipped.

---

## Frontend TypeScript build failures in Docker

**Status:** Fixed — commit `cfbfb07`  
**Symptom:** `docker compose up --build` failed at the frontend build stage with `tsc` errors.  
**Root cause:** Stricter `tsconfig` settings exposed type errors that were passing locally with `skipLibCheck`.  
**Fix:** Corrected the type errors in both `frontend-user` and `frontend-admin` source files.

---

## frontend-admin scan type misalignment with backend

**Status:** Fixed — commit `2ec4d25`  
**Symptom:** Admin dashboard showed incorrect or blank scan type labels.  
**Root cause:** Frontend TypeScript types for scan status/severity enums did not match the string literals returned by the backend API.  
**Fix:** Aligned `frontend-admin/src/types/scan.ts` with backend `schemas/scan.py`.

---

## Migrations not running on container start

**Status:** Fixed — commit `83ce412`  
**Symptom:** Backend container started but API calls failed with "relation does not exist" errors.  
**Root cause:** Docker entrypoint did not invoke `alembic upgrade head` before starting uvicorn.  
**Fix:** Backend `Dockerfile` / entrypoint runs migrations before starting the server.

---

## Frontend health checks in Docker Compose

**Status:** Fixed — commit `83ce412`  
**Symptom:** Backend container started before the frontend nginx was ready, causing misleading compose logs.  
**Root cause:** Frontend services had no `healthcheck` directive.  
**Fix:** Added `curl`-based health checks to frontend services in `docker-compose.yml`.

---

## ui-shared branch not yet merged

**Status:** Open — branch `feat/ui-shared-consistent-styling` (commit `f87ddda`)  
**Note:** The `ui-shared` shared component library and its Vite alias wiring exist only on this branch. `main` still has duplicated component implementations in each frontend. Merging this branch is required before `ui-shared` imports will resolve.

---

## Ollama network accessibility

**Symptom:** Backend or RAG service starts but all scan requests fail with connection refused.  
**Root cause:** Ollama defaults to binding `127.0.0.1:11434`. From the Docker host it is not reachable unless bound to `0.0.0.0`.  
**Fix:** On the VM: `sudo systemctl edit ollama` → add `Environment="OLLAMA_HOST=0.0.0.0:11434"` → `sudo systemctl restart ollama`. Then open TCP 11434 in the VM firewall to the Docker host only.  
**Verify:** `curl http://<vm-ip>:11434/api/tags` from the Docker host.
