---
description: Generate the full pytest matrix (mocked Claude) for module/endpoint $ARGUMENTS with safety assertions, then run pytest.
---

Generate tests for: **$ARGUMENTS**

## Workflow
1. Use the **test-writer** subagent targeting **$ARGUMENTS** (an endpoint or module). It must:
   - Mock the Claude API completely — no real network calls.
   - Use `httpx.AsyncClient` + `pytest-asyncio` against the FastAPI app with an in-memory/SQLite test DB and dependency overrides for DB + auth.
   - Generate the full 4-case matrix per endpoint: **happy path, 401 (no/invalid JWT), 429 (rate limit), 422 (validation)**.
   - Add mandatory safety assertions where a diagnosis is produced:
     - hot-engine / kriko / akü / yakıt / soğutma / fren diagnosis → `guvenlik_uyarisi` non-null.
     - `metalik_vuruntu` → `tamirciye_git_onerisi == True` + urgent.
     - hedging ("büyük ihtimalle") passed through where expected.
     - `tokens_in`/`tokens_out` persisted to AISession where applicable.
   - Reuse existing `conftest.py` fixtures; add only what is missing.
2. Run `pytest` on the new tests and report results.

## Output
List test files written, confirm all 4 cases + which safety assertions are present, the mock strategy, and the pytest pass/fail output. If the test environment cannot run (missing deps/collection error), report that explicitly rather than claiming success.
