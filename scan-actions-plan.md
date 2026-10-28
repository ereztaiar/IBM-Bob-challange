# Plan: Scan Actions Bar + User Prompt with Dual-Agent Sanitisation

## Overview

Two distinct user-facing improvements are combined here:

1. **Always-visible scan actions** — replace the single buried "← Scan another URL" button
   at the bottom of the report with an always-visible bar above the report that offers both
   "Scan again" (same URL, one click) and a new-URL input. The buried button is removed.

2. **User evaluation prompt** — add an optional collapsible free-text area below the URL
   input where the user can describe what they want the scan to focus on (e.g. "check for
   payment-page issues"). This prompt travels through the backend pipeline and influences
   the LLM report narrative. Before it reaches the LLM, two sequential sanitisation agents
   validate it so the pipeline cannot be manipulated via prompt injection.

**Out of scope:** There is no existing share/export feature anywhere in the codebase —
confirmed by code search. Nothing to remove on that front.

---

## Design Decisions (confirmed)

| # | Decision |
|---|---|
| D1 | The `user_prompt` textarea is inside a **collapsible section** below the URL field, collapsed by default. |
| D2 | If Ollama is unreachable during the LLM sanitisation guard, the user is shown a non-blocking warning, the textarea is **disabled**, and the scan proceeds without the prompt (graceful fallback). |

---

## Architecture Diagram

```
ScanForm
  └─ URL input + Scan button
  └─ [▶ Advanced / Focus (collapsed by default)]
       └─ textarea: "What should we focus on?" (300 char max)
            │
            ▼  on submit
POST /scans { url, user_prompt? }
            │
            ▼
scan_runner.run_scan(scan_id, url, user_prompt)
            │
            ▼  (before graph.ainvoke)
sanitise_user_prompt(raw)
  ├─ Agent 1: rule_filter()          — deterministic, no LLM
  └─ Agent 2: llm_guard()            — LLM semantic check
        │ Ollama down?
        ├─ YES → warn frontend (via scan status), return None
        └─ NO  → sanitised string or None if rejected
            │
            ▼
graph.ainvoke({ url, user_prompt, ... })
            │
            ▼
report_writer_node
  └─ _build_prompt(url, findings, rag_context, user_prompt?)
       └─ inserts "USER FOCUS REQUEST:" block when present
```

---

## Sub-Tasks

---

### Sub-Task 1 — Track the scanned URL in `HomePage` state

**Intent**
Store the URL that was just scanned so the "Scan again" button can re-submit it without
the user retyping it. This is a prerequisite for Sub-Tasks 5 and 6.

**Expected Outcomes**
- `HomePage` holds a `scannedUrl: string | null` state variable.
- `handleSubmit` stores the submitted URL after the API call succeeds.
- `handleReset` clears `scannedUrl` back to `null`.

**Todo List**
1. Add `const [scannedUrl, setScannedUrl] = useState<string | null>(null);` in `HomePage`.
2. Inside `handleSubmit`, call `setScannedUrl(url)` immediately after `setScanId(result.scan_id)`.
3. Inside `handleReset`, add `setScannedUrl(null)`.

**Relevant Context**
- File: `frontend-user/src/pages/HomePage/index.tsx`
- `handleSubmit` starts at line 39; `handleReset` starts at line 50.
- No other files are touched in this sub-task.

**Status:** `[ ] pending`

---

### Sub-Task 2 — Add the collapsible `user_prompt` field to `ScanForm`

**Intent**
Extend the scan-submission form with an optional collapsible section containing a short
textarea for the user to describe what they want evaluated. The collapse/expand is handled
with a plain `<details>`/`<summary>` HTML element — no JS state needed. A character counter
shows remaining characters as the user types. The value is forwarded to `onSubmit`.

**Expected Outcomes**
- `ScanForm` has a `<details>` block below the URL input row, collapsed by default, labelled
  "Focus area (optional)".
- Inside it: a `<textarea>` with `maxLength={300}`, placeholder
  `"e.g. check the payment page for injection issues"`, and a live `X / 300` counter.
- The textarea can be **disabled** via a new `promptDisabled?: boolean` prop. When disabled,
  a small inline notice reads: "Focus area unavailable — AI service is offline."
- `onSubmit` callback signature changes from `(url: string) => void` to
  `(url: string, prompt: string) => void`; passes the trimmed textarea value (empty string
  when the section is collapsed or blank).
- Styling uses design tokens only (`ui-shared/src/styles/variables.css`).
- JSDoc on the component and all exported members; strict TypeScript, no `any`.

**Todo List**
1. Add `promptDisabled?: boolean` to `ScanFormProps`.
2. Add `const [prompt, setPrompt] = useState("")` inside `ScanForm`.
3. Add `<details className={styles.focusDetails}>` block below the input row.
4. Add `<textarea>` with `maxLength={300}`, `disabled={promptDisabled ?? false}`,
   `value={prompt}`, `onChange`.
5. Add character counter `<span>{300 - prompt.length} / 300</span>`.
6. When `promptDisabled` is true render the inline "AI service offline" notice.
7. Update `handleSubmit` to call `onSubmit(trimmed, prompt.trim())`.
8. Add CSS for `.focusDetails`, `.focusTextarea`, `.charCounter`, `.offlineNotice` using
   design tokens only.

**Relevant Context**
- File: `frontend-user/src/components/ScanForm/index.tsx` — full file is 86 lines.
- File: `frontend-user/src/components/ScanForm/ScanForm.module.css` — add new classes here.
- Design tokens: `ui-shared/src/styles/variables.css`.

**Status:** `[ ] pending`

---

### Sub-Task 3 — Extend the API layer and backend schema to carry `user_prompt`

**Intent**
Thread the `user_prompt` value from the frontend `submitScan` call through to the backend
`run_scan` background task, so later sub-tasks can sanitise and use it.

**Expected Outcomes**
- `frontend-user/src/services/api.ts` → `submitScan(url, prompt)` includes `user_prompt`
  in the POST body only when `prompt` is non-empty.
- `HomePage.handleSubmit` signature becomes `(url: string, prompt: string)` and forwards
  both to `submitScan`.
- Backend `ScanSubmitRequest` gains `user_prompt: str | None = Field(None, max_length=300)`.
- Router `submit_scan` passes `request.user_prompt` to `scan_runner.run_scan`.
- `scan_runner.run_scan(scan_id, url)` → `run_scan(scan_id, url, user_prompt: str | None)`;
  passes `user_prompt` in the initial `AgentState` dict.
- `AgentState` TypedDict gains `user_prompt: str | None`.

**Todo List**
1. Update `submitScan` in `frontend-user/src/services/api.ts` to accept and send `prompt`.
2. Update `HomePage.handleSubmit` to accept `(url, prompt)` and forward both.
3. Add `user_prompt: str | None = Field(None, max_length=300)` to `ScanSubmitRequest`
   in `backend/app/schemas/scan.py`. Import `Field` from pydantic.
4. Update `submit_scan` in `backend/app/routers/scans.py`: change the
   `background_tasks.add_task` call to pass `request.user_prompt`.
5. Update `run_scan` signature in `backend/app/services/scan_runner.py`; add `user_prompt`
   to the `graph.ainvoke({...})` dict.
6. Add `user_prompt: str | None` to `AgentState` in `backend/app/agents/state.py`.

**Relevant Context**
- `frontend-user/src/services/api.ts` — `submitScan` at line 19.
- `frontend-user/src/pages/HomePage/index.tsx` — `handleSubmit` at line 39.
- `backend/app/schemas/scan.py` — `ScanSubmitRequest` at line 10.
- `backend/app/routers/scans.py` — `background_tasks.add_task` at line 91.
- `backend/app/services/scan_runner.py` — `graph.ainvoke` at line 48.
- `backend/app/agents/state.py` — `AgentState` at line 51.

**Status:** `[ ] pending`

---

### Sub-Task 4 — Build the dual-agent prompt sanitisation module

**Intent**
Create `backend/app/agents/prompt_sanitiser.py` with two sequential guards:

- **Agent 1 — `rule_filter(raw)`** — deterministic, no LLM. Strips HTML tags, rejects null
  bytes, and rejects strings containing known injection phrases (`ignore previous`,
  `disregard`, `you are now`, `act as`, `[INST]`, `<<SYS>>`, `system:`, etc.) or
  excessively repeated characters (>30 of the same char). Returns the cleaned string or
  raises `ValueError` if fundamentally unsafe.

- **Agent 2 — `llm_guard(cleaned)`** — sends the rule-cleaned string to Ollama with a
  tight system prompt: classify as a legitimate security-scan focus request; respond with
  a sanitised one-sentence restatement, or respond with exactly `UNSAFE` if it is not.
  - If the LLM returns `UNSAFE` or an empty response → return `""` (rejected).
  - If Ollama is **unreachable** (any connection/timeout error) → raise
    `PromptServiceUnavailableError` (a custom exception defined in this module).

- **Orchestrator — `sanitise_user_prompt(raw)`** — calls both agents in sequence:
  - `None` input → returns `None` immediately.
  - `rule_filter` raises → returns `None` (logged as warning).
  - `llm_guard` raises `PromptServiceUnavailableError` → re-raises so the caller can react.
  - `llm_guard` returns `""` → returns `None` (semantically rejected).
  - Otherwise → returns the sanitised string.

**Expected Outcomes**
- New file `backend/app/agents/prompt_sanitiser.py` under 150 lines.
- `PromptServiceUnavailableError` exception class exported from the module.
- Unit tests in `backend/tests/test_prompt_sanitiser.py`:
  - `None` input → `None`.
  - Clean benign input passes both agents → sanitised string returned.
  - Input with injection phrase → rule filter catches it → `None` returned.
  - `llm_guard` returns `"UNSAFE"` → `None` returned.
  - Ollama unreachable → `PromptServiceUnavailableError` raised.

**Todo List**
1. Create `backend/app/agents/prompt_sanitiser.py`.
2. Define `PromptServiceUnavailableError(Exception)`.
3. Implement `rule_filter(raw: str) -> str`.
4. Implement `async llm_guard(cleaned: str) -> str`.
5. Implement `async sanitise_user_prompt(raw: str | None) -> str | None`.
6. Create `backend/tests/test_prompt_sanitiser.py` with mocked `get_llm()`.

**Relevant Context**
- LLM access: `backend/app/agents/llm_factory.py` → `get_llm()`.
- Connection error types to catch: `httpx.ConnectError`, `httpx.TimeoutException`, and
  the LangChain wrapper equivalents (`langchain_core.exceptions` or bare `Exception`
  with message inspection). Catching the base `Exception` and checking for connectivity
  keywords is acceptable here.
- Keep module under 150 lines (project file-size rule is 300 lines; 150 is the target here
  because this module is purely functional).

**Status:** `[ ] pending`

---

### Sub-Task 5 — Wire `sanitise_user_prompt` into `scan_runner` with service-down handling

**Intent**
Call the sanitiser before invoking the graph. If Ollama is unreachable, set a flag in the
scan state so the frontend can show the "AI service offline" notice and disable the
textarea on re-scans.

**Expected Outcomes**
- `scan_runner.run_scan` calls `sanitise_user_prompt(user_prompt)` before `graph.ainvoke`.
- If `PromptServiceUnavailableError` is raised:
  - `user_prompt` is set to `None` (scan continues without the focus hint).
  - A new boolean field `prompt_service_down: bool` is set to `True` in the initial state.
- `AgentState` gains `prompt_service_down: bool` (defaults `False`).
- `ScanStatusResponse` / `ScanReportResponse` schemas gain
  `prompt_service_down: bool = False` so the frontend can read it.
- `scan_service.create_scan` and `scan_service.update_scan_status` are updated to store /
  return the `prompt_service_down` flag (DB column `prompt_service_down BOOLEAN DEFAULT FALSE`).
- An Alembic migration is generated for the new column.
- Frontend `ScanResponse` type gains `prompt_service_down: boolean`.
- `HomePage` reads `scan.prompt_service_down` and passes `promptDisabled` to `ScanForm`
  when the bar is shown and the field is disabled.

**Todo List**
1. Add `prompt_service_down: bool` to `AgentState` in `backend/app/agents/state.py`.
2. In `scan_runner.run_scan`, wrap the `sanitise_user_prompt` call; on
   `PromptServiceUnavailableError` set `user_prompt = None` and `prompt_service_down = True`.
3. Pass `prompt_service_down` in the initial state dict to `graph.ainvoke`.
4. Add `prompt_service_down: bool = False` to `ScanStatusResponse` and `ScanReportResponse`
   in `backend/app/schemas/scan.py`.
5. Add `prompt_service_down` column to the `scans` DB model in `backend/app/db/models.py`.
6. Generate an Alembic migration: `alembic revision --autogenerate -m "add_prompt_service_down"`.
7. Update `scan_service.create_scan` to accept and persist `prompt_service_down`.
8. Update `scan_service.update_scan_status` to return the flag in the response.
9. Update `_scan_to_status_response` and `_scan_to_report_response` in the router to
   include `prompt_service_down`.
10. Add `prompt_service_down: boolean` to `ScanResponse` in
    `frontend-user/src/types/scan.ts`.
11. In `HomePage`, when `scan?.prompt_service_down` is `true`, pass `promptDisabled={true}`
    to `ScanForm`.

**Relevant Context**
- `backend/app/services/scan_runner.py` — `run_scan` at line 26.
- `backend/app/db/models.py` — `Scan` ORM model.
- `backend/app/services/scan_service.py` — `create_scan`, `update_scan_status`.
- `backend/app/routers/scans.py` — response converters at lines 16-54.
- `frontend-user/src/types/scan.ts` — `ScanResponse` interface.
- `frontend-user/src/pages/HomePage/index.tsx`.

**Status:** `[ ] pending`

---

### Sub-Task 6 — Wire `user_prompt` into the report writer LLM prompt

**Intent**
When a sanitised `user_prompt` is present in state, include it in the LLM prompt so the
report narrative reflects the user's stated focus area.

**Expected Outcomes**
- `_build_prompt` in `report_writer.py` accepts `user_prompt: str | None` as a parameter.
- When `user_prompt` is non-empty, the formatted LLM prompt includes a clearly delimited
  section after the findings block:
  ```
  USER FOCUS REQUEST:
  {user_prompt}
  ```
- `report_writer_node` reads `state.get("user_prompt")` and passes it to `_build_prompt`.
- The fallback report path (`_fallback_report`) is unchanged.
- `_build_prompt` docstring is updated.

**Todo List**
1. Update `_build_prompt` signature: add `user_prompt: str | None = None`.
2. Append the `USER FOCUS REQUEST` block to the f-string only when `user_prompt` is truthy.
3. Update `report_writer_node` to read `state.get("user_prompt")` and pass it.
4. Update the `_build_prompt` docstring.

**Relevant Context**
- `backend/app/agents/report_writer.py`:
  - `_build_prompt` at line 23.
  - `report_writer_node` at line 162.
- The `USER FOCUS REQUEST` block should appear between the `RAW FINDINGS` block and the
  `Your response MUST be valid JSON` instruction — so the LLM sees it as context before
  receiving the output format constraint.

**Status:** `[ ] pending`

---

### Sub-Task 7 — Build the `ScanActionsBar` component

**Intent**
Create a new component that is always visible above the spinner/report once a first scan
has been submitted. It provides "Scan again" (same URL, one click) and a new-URL input.
This replaces the buried reset button at the bottom of the shared `ReportView`.

**Expected Outcomes**
- New component at `frontend-user/src/components/ScanActionsBar/index.tsx` with a
  matching `ScanActionsBar.module.css`.
- Props:
  - `currentUrl: string` — shown on the "Scan again" button label.
  - `onScanAgain: () => void` — re-submits the same URL.
  - `onScanNew: (url: string) => void` — submits a different URL.
  - `isScanning: boolean` — disables all controls while a scan is running.
- The new-URL input uses the same `http`/`https` validation logic as `ScanForm`.
- Styling uses design tokens only.
- Full JSDoc; strict TypeScript, no `any`.

**Todo List**
1. Create `frontend-user/src/components/ScanActionsBar/index.tsx`.
2. Create `ScanActionsBar.module.css` with design tokens only.
3. Implement URL validation inline (same rules as `ScanForm` lines 35-50).
4. Wire `onScanAgain` to the "↺ Scan again" button.
5. Wire `onScanNew` to the new-URL form submit.

**Relevant Context**
- URL validation pattern: `frontend-user/src/components/ScanForm/index.tsx` lines 35-50.
- Design tokens: `ui-shared/src/styles/variables.css`.

**Status:** `[ ] pending`

---

### Sub-Task 8 — Wire `ScanActionsBar` into `HomePage` and remove the old reset button

**Intent**
Mount the action bar in `HomePage` whenever `scannedUrl` is set (i.e. after the first
successful submission), and permanently remove the now-redundant bottom reset button from
the shared `ReportView`.

**Expected Outcomes**
- `ScanActionsBar` renders above the spinner and report whenever `scannedUrl !== null`.
- "Scan again" → `handleRescan(scannedUrl)`: resets state then immediately re-submits.
- "Scan new URL" → `handleRescan(newUrl)`.
- While `isScanning` is true the bar stays visible but its controls are disabled.
- The `{onReset && <button>}` JSX block is removed from
  `ui-shared/src/components/ReportView/index.tsx`.
- The `onReset?` prop is removed from `ReportViewProps` in `ui-shared`.
- The `resetButton` CSS class is removed from
  `ui-shared/src/components/ReportView/ReportView.module.css`.
- `frontend-user/src/components/ReportView/index.tsx` no longer passes `onReset` to
  `SharedReportView` (prop no longer exists on the shared component).
- The local `frontend-user` `ReportView` wrapper's own `onReset` prop is also removed
  (it is no longer needed — `HomePage` owns the bar).
- Admin frontend is unaffected (it never used `onReset`).

**Todo List**
1. Import `ScanActionsBar` in `HomePage`; render it when `scannedUrl !== null`.
2. Add `handleRescan(url: string)` helper: `setScanId(null)` + `setScannedUrl(null)` +
   `handleSubmit(url, "")`.
3. Pass `currentUrl={scannedUrl}`, `onScanAgain={() => handleRescan(scannedUrl!)}`,
   `onScanNew={handleRescan}`, `isScanning` to `<ScanActionsBar>`.
4. Remove `onReset` prop, button JSX, and `resetButton` CSS from shared `ReportView`.
5. Update `frontend-user/src/components/ReportView/index.tsx` to drop `onReset` from
   its own props and from the `<SharedReportView>` call.
6. Grep `frontend-admin/src` for any `onReset` usage and confirm zero results.

**Relevant Context**
- `frontend-user/src/pages/HomePage/index.tsx` lines 69-88.
- `ui-shared/src/components/ReportView/index.tsx` lines 96-100.
- `ui-shared/src/components/ReportView/ReportView.module.css` lines 120-135.
- `frontend-user/src/components/ReportView/index.tsx` line 43.

**Status:** `[ ] pending`

---

## Execution Order

Sub-tasks are designed to be implemented in order. Each is independently reviewable.

```
1 → 5 → 7 → 8      (frontend scan-actions bar track)
2 → 3 → 4 → 5 → 6  (backend prompt track)
3 → 5              (service-down flag feeds into ScanForm promptDisabled prop)
```

Practical sequence for a single implementation session:
**1 → 2 → 3 → 4 → 5 → 6 → 7 → 8**
