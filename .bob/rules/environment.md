# Environment & Configuration Rules

Derived from `AGENTS.md`.

---

## Required Environment Variables

Copy `.env.example` to `.env` before running. These variables must be set:

| Variable            | Description                                                   |
|---------------------|---------------------------------------------------------------|
| `POSTGRES_PASSWORD` | PostgreSQL superuser password                                 |
| `OLLAMA_BASE_URL`   | Ollama VM URL, e.g. `http://192.168.1.50:11434`               |
| `ADMIN_USERNAME`    | Admin login — used for JWT validation, not the `admins` table |
| `ADMIN_PASSWORD`    | Admin password                                                |
| `JWT_SECRET`        | JWT signing secret (`openssl rand -hex 32`)                   |

- `.env` is **gitignored** — never commit secrets.
- `backend` and `rag` refuse to start if `OLLAMA_BASE_URL` is unset.

---

## Ollama VM Setup

Ollama defaults to binding `127.0.0.1:11434`. To make it reachable from Docker:

```
sudo systemctl edit ollama
# Add: Environment="OLLAMA_HOST=0.0.0.0:11434"
sudo systemctl restart ollama
```

Verify from the Docker host: `curl http://<vm-ip>:11434/api/tags`

Open TCP 11434 in the VM firewall to the Docker host **only**.

---

## Embedding Model

`OLLAMA_EMBED_MODEL = "nomic-embed-text"` produces **768-dimensional** vectors.
If this model is ever changed, update:
1. Both vector columns via a new Alembic migration.
2. `rag/app/config.py` → `OLLAMA_EMBED_MODEL`.

---

## Plans Folder

`plans/*.md` are **gitignored** — local working documents only.
The `plans/` folder itself is tracked via `plans/.gitkeep`.
