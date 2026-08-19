# Sage Widget — integration guide

This is the canonical, framework-minimal (inline-styled, no Tailwind/CSS-
module dependency) implementation of the embeddable Sage UI (spec Section
7.5). **It is not published as an npm package this sprint** — QuietNoise
uses Tailwind/shadcn and Lorito uses CSS Modules with a different Next.js
major version, and setting up a real shared workspace package across two
independent repos wasn't worth the risk on a 3-day clock. Instead, `src/`
here is copied verbatim into each app's own component tree. Publishing
this as a real `@quasar/sage-widget` package (workspace or npm) is the
first fast-follow after launch — do it before a third integration is ever
needed.

## What each host app needs

1. **A same-origin server-side proxy route** that holds the tenant's Sage
   API key and forwards to the Gateway. The widget's browser code never
   sees the key. Shape:

   ```ts
   // POST { module, mode, user_message, context } -> Gateway's envelope JSON
   const gatewayResponse = await fetch(`${SAGE_GATEWAY_URL}/v1/completions`, {
     method: "POST",
     headers: {
       "Content-Type": "application/json",
       Authorization: `Bearer ${SAGE_API_KEY}`, // server-side env var only
     },
     body: JSON.stringify(await request.json()),
   });
   ```

2. **A copy of `src/` mounted in the app shell**, e.g.:

   ```tsx
   <SageWidget
     endpoint="/api/sage/completions"       // your proxy route from step 1
     initialContext={{ industry: "IIoT" }}   // whatever business context you have
   />
   ```

   `initialContext` is intentionally free-form — Visionary/Storyteller
   don't require any particular schema, just real values so
   `sourced_fields` grounding has something to point at.

## Files

- `SageWidget.tsx` — floating launcher + drawer, module tabs (Visionary/
  Storyteller enabled, others shown "Coming soon").
- `useSageCompletion.ts` — fetch hook against your proxy endpoint.
- `theme.ts` — Section 6 module colors.
- `types.ts` — TS mirror of the Gateway's request/response schemas
  (`gateway/app/schemas/`). If those change, update both.
