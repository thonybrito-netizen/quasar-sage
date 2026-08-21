# Quasar Sage — standalone app

Sage's own first-party product surface — not embedded in QuietNoise or
Lorito, a real standalone Next.js application carrying Quasar Sage's own
identity (spec Section 6: the pulsar mark, dark navy field, per-module
accent colors).

Built for the Heriot-Watt University meeting (2026-08-21+): the primary
use case is an **instructor demonstrating or grading student work**
against Sage's five frameworks -- paste in a student's positioning
statement/email draft/deal summary, get Sage's structured critique
(`strategic_critique`, `missing_variables`, and `sourced_fields` for
grounded-claim transparency), same rigor as the embedded widget but as a
full workspace, not a floating drawer.

## Pages

- `/` -- landing/pitch page: the five modules, their named frameworks,
  a CTA into the workspace.
- `/workspace` -- the actual tool: pick a module, paste student work plus
  any known facts (`key: value` lines -> a real context object for the
  Gateway's Grounding Check), run it, see the full envelope response.

## Local dev

```
cd app
npm install
copy .env.example .env.local   # fill in SAGE_DEMO_TENANT_KEY
npm run dev   # http://localhost:3100
```

`SAGE_DEMO_TENANT_KEY` is a real per-tenant Gateway key (Secret Manager:
`sage-demo-tenant-key` in `quasar-business-sage`, tenant id
`quasar-sage-app` inside `quasar-sage-tenant-keys`) -- server-side only,
via `/api/completions`, same never-touches-the-browser principle as every
other Sage integration.

## Deploy

Builds and deploys via the same `.github/workflows/deploy.yml` as the
Gateway (triggers on `app/**` changes too), to Cloud Run service
`quasar-sage-app` in `quasar-business-sage`.
