# Coding Standards

Rules derived from `AGENTS.md`. Apply to every file touched in this project.

---

## File & Function Size Limits

- **Files:** max **300 lines**. Extract to submodules before hitting the limit.
- **Functions/methods:** max **50 lines**. Extract helpers rather than growing a function.

---

## Documentation

- **Python:** every function and class **must** have a docstring.
- **TypeScript:** every exported function and component **must** have a JSDoc comment.
- No undocumented public API surface.

---

## Python

- Type-annotate **all** function signatures.
- Use `async def` throughout the FastAPI layer.
- Pydantic v2 models for all request/response schemas.
- Naming: `snake_case` for variables/functions, `PascalCase` for classes.
- SOLID: single responsibility per module; all new check agents **must** subclass `BaseCheck`
  (`backend/app/agents/checks/base.py`).
- DRY: shared logic lives in `services/` or `utils/` — never copy-paste.

---

## TypeScript / React

- Strict mode on; **no `any`**.
- Each React component lives in its own folder: `index.tsx` + CSS module + local types.
- Common hooks in `src/hooks/`, utilities in `src/utils/` — not duplicated per component.
- Naming: `camelCase` variables, `PascalCase` components and types.

---

## Frontend Styling

- All shared visual components (`NavBar`, `FindingCard`, `ReportView`, `ScanSpinner`)
  **must** be imported from `ui-shared`, not re-implemented per frontend.
- CSS values (colours, spacing, font sizes) **must** use design tokens from
  `ui-shared/src/styles/variables.css` — no hardcoded hex or pixel values in CSS modules.
- Both frontends are wired to `ui-shared` via the Vite alias `ui-shared → ../ui-shared/src`.

---

## Database Migrations

- Always generate an **Alembic migration** for every schema change; never alter the DB directly.
- Vector columns are `vector(768)` — matched to `nomic-embed-text`. Changing the embedding
  model requires a new migration for both `vulnerability_docs.embedding` and
  `scan_embeddings.embedding`.

---

## Tests

- Every new backend function/service needs a **unit test**.
- Mock all DB sessions and Ollama calls — **no real network calls** in tests.
- Frontend: Vitest + Testing Library; test each component and hook.

---

## Commits & Branches

- Conventional commits: `feat(scope):`, `fix(scope):`, `chore:`, `merge:`.
- Branch naming: `feat/<name>`, `fix/<name>`.
