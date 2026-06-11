---
description: Scaffold a new backend endpoint ($ARGUMENTS) with api→services→domain layering, JWT + rate limit + timeout + retry, then generate tests.
---

Scaffold a new Usta backend endpoint for: **$ARGUMENTS**

Follow the architecture and cross-cutting rules exactly.

## 1. Understand conventions
- Read existing endpoints to match patterns: Glob/Read under `backend/api/`, `backend/services/`, `backend/domain/`. Note the JWT dependency, the per-user rate limiter, timeout wrapper, and tenacity retry helpers already in use. REUSE them.

## 2. Implement with strict layering (no skipping layers)
- **api/**: route handler — request/response Pydantic models, dependency-injected auth + rate limit, delegates to a service. No business logic or DB access here.
- **services/**: orchestration/business logic; calls domain and any Claude client. If it calls Claude, persist `tokens_in`/`tokens_out` to the AISession.
- **domain/**: entities, repository/DB access (SQLAlchemy async), pure rules.
- api → services → domain only; never let api touch domain directly or skip services.

## 3. Cross-cutting requirements on the endpoint (mandatory)
- JWT auth (reject unauthenticated → 401).
- Per-user rate limit (exceed → 429).
- 30s timeout on the request handling / outbound AI call.
- tenacity retry(2) on the Claude/external call.
- If it produces a diagnosis, conform to the AI response schema (`tespit, guven, konum_tarifi, dogru_yer_mi, sonraki_adim, guvenlik_uyarisi, tamirciye_git_onerisi`) and respect safety rules (hedging, guvenlik_uyarisi triggers, no LPG modification, tamirciye-git option).

## 4. Generate tests
- Use the **test-writer** subagent to generate pytest tests for this endpoint: happy path + 401 + 429 + 422, with the Claude API mocked (no network), plus safety assertions where the endpoint yields a diagnosis (guvenlik_uyarisi present for hot-engine/jack/battery/fuel/cooling/brake; metalik_vuruntu → tamirciye_git_onerisi true; token counts persisted). Then run pytest and report.

## 5. Report
List files created/changed across api/services/domain, confirm JWT + rate limit + 30s timeout + retry(2) are wired, and give the test results.
