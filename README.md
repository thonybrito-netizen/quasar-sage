# Quasar Sage

The Quasar Marketing/Business Sage — an embedded AI CRO co-pilot for
QuietNoise and Lorito. This repo is the API Gateway (`gateway/`) and the
embeddable widget UI (`widget/`) described in the master spec's Sections 3
and 7.5.

**Launch scope (Aug 22):** Visionary and Storyteller are live (real Claude
calls). Dealmaker, Negotiator, and Locker Room are scaffolded — correct API
shape, deterministic "not yet enabled" response, no generation. See
`gateway/app/modules/` for each module's system prompt and
`C:\Users\totob\.claude\plans\synthetic-dazzling-piglet.md` for the full
sprint plan and everything explicitly deferred past launch.

## Gateway (`gateway/`)

FastAPI service implementing spec Section 3 (API Gateway & Parsing Rules):
prompt assembly, the JSON response envelope, and the validation/retry/
fallback pipeline.

```
cd gateway
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env   # fill in ANTHROPIC_API_KEY and TENANT_API_KEYS
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8090
```

(8090, not 8080 -- something else on this dev machine already owns 8080. Cloud Run
deploys still bind to the container's own $PORT=8080 per the Dockerfile; this is a
local-only choice, and both QuietNoise's and Lorito's local `.env` files already
point at 8090 to match.)

Run tests: `.venv\Scripts\python -m pytest tests -v` (uses a fake Claude
client — no API key or network access needed).

With the Gateway running, `.\scripts\smoke_test.ps1` hits it over real
HTTP and reports pass/fail for health, module listing, auth rejection, and
both live modules. It works with or without a real `ANTHROPIC_API_KEY` set
(it tells you which regime it ran in) — the fastest way to confirm the
real key works once you drop it into `.env` is to re-run this script.

## Widget (`widget/`)

The embeddable Sage UI, mounted into both QuietNoise and Lorito. See
`widget/README.md` for the integration contract both apps follow.
