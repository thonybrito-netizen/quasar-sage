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

## Deploy (`gateway/`, GCP project `quasar-business-sage`)

`.github/workflows/deploy.yml` builds and deploys the Gateway to Cloud Run
on every push to `main` that touches `gateway/`, mirroring Lorito's own
WIF-based deploy.yml.

**One-time GCP setup — done, 2026-08-19/20:**
1. Billing linked (Firebase Payment account `0187E4-CB668C-19AF8C` -- the
   first two accounts tried both hit `Cloud billing quota exceeded`).
2. APIs enabled: Cloud Run, Artifact Registry, Secret Manager, IAM Credentials, STS, Cloud Resource Manager.
3. Artifact Registry repo `quasar-sage` created (us-central1, docker format).
4. WIF pool `quasar-sage-github-pool` + provider `quasar-sage-github-provider`,
   scoped to `thonybrito-netizen/quasar-sage` only (same attribute-condition
   pattern as Lorito's `colibri-github-pool`).
5. Deploy service account `quasar-sage-github-actions@quasar-business-sage.iam.gserviceaccount.com`,
   granted `roles/artifactregistry.writer` + `roles/run.developer` (same
   minimal role set Lorito's deploy SA actually uses, not `run.admin`) and
   bound for WIF impersonation from that repo.
6. Secrets created: `anthropic-api-key` (the real key) and
   `quasar-sage-tenant-keys` (real random per-tenant keys for `quietnoise`
   and `lorito`, not the `qn-dev-placeholder`/`col-dev-placeholder` dev
   values). Cloud Run's default compute service account
   (`250103471198-compute@developer.gserviceaccount.com`) granted
   `roles/secretmanager.secretAccessor` on both.

`WIF_PROVIDER`/`WIF_SA` in `deploy.yml` are filled in with real values --
push to `main` now actually deploys.

The matching real tenant keys still need to land in QuietNoise's
`SAGE_API_KEY` secret and Lorito's `QUASAR_SAGE_API_KEY` secret once the
Gateway's live URL is known (see each repo's PR checklist).

**Vertex fallback (optional):** if you'd rather not hold a raw Anthropic
API key in Secret Manager long-term, `VERTEX_PROJECT_ID` is the fallback
path (see `gateway/app/clients/anthropic_client.py`) -- but note the
executive-coach project's prior finding: Vertex's default quota for
Anthropic models is 0 on a fresh project and needs a manual Google-side
approval, so don't plan the launch around switching to it.
