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
WIF-based deploy.yml. One-time GCP setup needed before the first run
(none of this is scripted -- do it once in the Cloud Console / gcloud):

1. **Artifact Registry repo**: `gcloud artifacts repositories create quasar-sage --repository-format=docker --location=us-central1`
2. **Workload Identity Federation**: a pool + provider trusting this GitHub
   repo, and a deploy service account with `roles/run.admin` +
   `roles/artifactregistry.writer` + `roles/iam.serviceAccountUser` --
   same shape as Lorito's `colibri-github-pool` setup. Fill the resulting
   provider path and service account email into `WIF_PROVIDER`/`WIF_SA` at
   the top of `deploy.yml`.
3. **Secrets** (Secret Manager): `anthropic-api-key` (the real key from
   `gateway/.env`, never commit it) and `quasar-sage-tenant-keys` (the
   real JSON tenant-key map -- generate fresh random keys for prod, don't
   reuse the `qn-dev-placeholder`/`col-dev-placeholder` dev values). Once
   the real prod tenant keys exist, update `SAGE_API_KEY` in QuietNoise's
   `apphosting.yaml` secret and `QUASAR_SAGE_API_KEY` in Lorito's
   `deploy.yml` secret to match.
4. **Vertex fallback (optional)**: if you'd rather not hold a raw
   Anthropic API key in Secret Manager long-term, `VERTEX_PROJECT_ID` is
   the fallback path (see `gateway/app/clients/anthropic_client.py`) --
   but note the executive-coach project's prior finding: Vertex's default
   quota for Anthropic models is 0 on a fresh project and needs a manual
   Google-side approval, so don't plan the launch around switching to it.
