"""
Quasar Sage concurrent-user load test -- 100 concurrent users target.

Tests Sage under realistic load through its THREE real entry points, not
one synthetic target -- this is meant to answer "can the platform handle
100 people using Sage at once," not just "can the Gateway handle 100
requests":

  - QuietNoiseSageUser  -> quietnoise.me's same-origin proxy route
    (POST /api/sage/completions). No login needed -- the tenant key is
    server-side, matching exactly what any visitor's browser calls.
  - LoritoSageUser       -> api.lorito.net's authenticated passthrough
    (POST /api/v1/sage/completions). Needs a real Firebase ID token or an
    X-API-Key for a real Lorito user (see "Env vars" below) -- matches
    what a logged-in seller's browser calls.
  - GatewayDirectUser    -> the Gateway itself (POST /v1/completions) with
    a real per-tenant bearer key. Isolates Gateway-only capacity from
    either app's own request-handling overhead.

Each class has its own `host`, so ONE run exercises all three
simultaneously -- no --host flag needed. Weights (4 / 3 / 3) approximate
realistic traffic: most real usage goes through the two apps, not
straight at the Gateway.

*** COST AND RATE-LIMIT WARNING -- READ BEFORE RUNNING AT FULL SCALE ***
Every request that reaches a live module (all 5 are live) is a REAL
Anthropic API call: real tokens, real dollars, subject to your
organization's real rate limits. There is deliberately no dry-run/mock
mode -- mocking would test nothing about real-world capacity, which is
the entire point of this file. At steady state, 100 users each submitting
roughly every 15-45s is on the order of 130-400 real Claude calls/minute.
Before running at -u 100:
  - Confirm your Anthropic org's rate limit (requests/min, tokens/min)
    actually covers this, or you'll see 429s that look like platform
    failures but are actually your own account's ceiling.
  - Budget for the token spend.
  - Prefer a quiet traffic window if running against production (all
    three hosts below default to production -- there is no staging
    environment for this platform as of 2026-08).
Always sanity-check small first: -u 5 -r 1 --run-time 2m before -u 100.

Usage
-----
1. Install:  pip install locust
2. Set env vars (see below).
3. Run headless (ramp to 100 users at 5/s, hold 10 minutes):
     locust -f locustfile.py --headless -u 100 -r 5 --run-time 10m \
       --html load_report.html
4. Or open the web UI (default http://localhost:8089):
     locust -f locustfile.py

Env vars
--------
  SAGE_GATEWAY_TENANT_KEY  A real per-tenant Gateway key, for
                           GatewayDirectUser (Secret Manager:
                           quasar-sage-tenant-keys in quasar-business-sage
                           -- the "quietnoise" or "lorito" value).
  LORITO_TEST_TOKEN        "Bearer eyJ..." (a real Firebase ID token) or
                           "ck_..." (an X-API-Key) for a real Lorito user.
                           See services/api/tests/load/locustfile.py in
                           the Colibri_CRM repo for how to grab a Firebase
                           token from DevTools -- same method applies here.
  QUIETNOISE_HOST / LORITO_HOST / GATEWAY_HOST
                           Override any of the three default prod hosts
                           below, e.g. to point at a local dev instance.

Expected targets
-----------------
Spec Section 3.6 defines aspirational p50/p95 assuming fast model
response; real observed latency for a genuine multi-paragraph strategic
reply is 15-90s depending on whether an Invisible Retry fires (a second
full Claude round-trip). Targets here are calibrated to that measured
reality, not the spec's own numbers -- those predate real production
traffic and are worth revisiting against this test's own results:
  p50  < 30s   (first-attempt, no retry)
  p95  < 95s   (covers one Invisible Retry)
  error rate < 2% -- NOTE: a live module correctly declining to generate
  (e.g. Storyteller refusing without positioning context) is still HTTP
  200 with a real strategic_critique, and is NOT an error; only non-200
  responses and malformed JSON count against this target. See
  _check_response() below.
"""

import json
import os
import random

from locust import HttpUser, between, task

GATEWAY_HOST = os.environ.get("GATEWAY_HOST", "https://quasar-sage-gateway-lnexpzgv5a-uc.a.run.app")
QUIETNOISE_HOST = os.environ.get("QUIETNOISE_HOST", "https://quietnoise.me")
LORITO_HOST = os.environ.get("LORITO_HOST", "https://api.lorito.net")

GATEWAY_TENANT_KEY = os.environ.get("SAGE_GATEWAY_TENANT_KEY", "")
LORITO_TOKEN = os.environ.get("LORITO_TEST_TOKEN", "")

REQUEST_TIMEOUT = 100  # seconds -- comfortably above the Gateway's own 90s gunicorn timeout

# Realistic weighted distribution across modules. Visionary/Storyteller
# see the most traffic (every new campaign or asset starts there);
# Negotiator/Locker Room see the least (only at specific pipeline
# stages). Each scenario's context is deliberately complete enough that
# the module can generate a real answer rather than decline for missing
# variables -- a load test should mostly exercise the expensive path
# (full generation), not the cheap early-refusal path.
_MODULE_SCENARIOS = [
    {
        "module": "visionary",
        "weight": 30,
        "message": "Help me position our new inventory automation platform.",
        "context": {
            "enemy": "manual spreadsheet tracking",
            "why": "we believe inventory decisions should never wait on a spreadsheet refresh",
        },
    },
    {
        "module": "storyteller",
        "weight": 30,
        "message": "Draft a cold email about our automation platform.",
        "context": {
            "enemy": "manual spreadsheet tracking",
            "positioning": "we believe inventory decisions should never wait on a spreadsheet refresh",
            "downtime_cost": "6 hours/week reconciling counts by hand",
        },
    },
    {
        "module": "dealmaker",
        "mode": "enterprise",
        "weight": 20,
        "message": "Help me prep a proposal for this deal.",
        "context": {"economic_buyer": "VP Operations", "deal_value": 85000, "last_activity_days_ago": 3},
    },
    {
        "module": "negotiator",
        "weight": 10,
        "message": "They're asking for a 10% discount on renewal, how should I respond?",
        "context": {
            "walk_away_value": 50000,
            "plausible_range": "50000-65000",
            "counterpart_position": "10% discount",
        },
    },
    {
        "module": "locker_room",
        "weight": 10,
        "message": "Is this campaign ready to launch?",
        "context": {"kill_criteria_target": "15 new orders in 30 days", "days_elapsed": 2},
    },
]
_SCENARIO_WEIGHTS = [s["weight"] for s in _MODULE_SCENARIOS]


def _pick_scenario() -> dict:
    return random.choices(_MODULE_SCENARIOS, weights=_SCENARIO_WEIGHTS, k=1)[0]


def _build_payload(scenario: dict) -> dict:
    payload = {"module": scenario["module"], "user_message": scenario["message"], "context": scenario["context"]}
    if "mode" in scenario:
        payload["mode"] = scenario["mode"]
    return payload


def _check_response(response, label: str) -> None:
    """Shared success/failure logic for all three user types -- a 200 with
    a real strategic_critique is success regardless of whether
    generated_content is empty (see module docstring)."""
    if response.status_code != 200:
        response.failure(f"{label}: HTTP {response.status_code}")
        return
    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError):
        response.failure(f"{label}: response was not valid JSON")
        return
    if not data.get("strategic_critique"):
        response.failure(f"{label}: 200 but missing strategic_critique -- malformed envelope")
        return
    response.success()


class QuietNoiseSageUser(HttpUser):
    """Simulates a QuietNoise dashboard visitor using the Sage widget."""

    host = QUIETNOISE_HOST
    weight = 4
    wait_time = between(15, 45)  # realistic think-time: read the response, decide what to ask next

    @task
    def ask_sage(self):
        scenario = _pick_scenario()
        with self.client.post(
            "/api/sage/completions",
            json=_build_payload(scenario),
            name=f"QuietNoise /api/sage/completions ({scenario['module']})",
            catch_response=True,
            timeout=REQUEST_TIMEOUT,
        ) as r:
            _check_response(r, "QuietNoise")


class LoritoSageUser(HttpUser):
    """Simulates a logged-in Lorito seller/manager using the Sage widget."""

    host = LORITO_HOST
    weight = 3
    wait_time = between(15, 45)

    def on_start(self) -> None:
        if not LORITO_TOKEN:
            raise RuntimeError(
                "LORITO_TEST_TOKEN is not set -- LoritoSageUser needs a real Firebase ID token "
                "('Bearer eyJ...') or API key ('ck_...'). See the module docstring."
            )

    def _headers(self) -> dict:
        if LORITO_TOKEN.startswith("ck_"):
            return {"X-API-Key": LORITO_TOKEN}
        if LORITO_TOKEN.startswith("Bearer "):
            return {"Authorization": LORITO_TOKEN}
        return {"Authorization": f"Bearer {LORITO_TOKEN}"}

    @task
    def ask_sage(self):
        scenario = _pick_scenario()
        with self.client.post(
            "/api/v1/sage/completions",
            json=_build_payload(scenario),
            headers=self._headers(),
            name=f"Lorito /api/v1/sage/completions ({scenario['module']})",
            catch_response=True,
            timeout=REQUEST_TIMEOUT,
        ) as r:
            _check_response(r, "Lorito")


class GatewayDirectUser(HttpUser):
    """Hits the Gateway directly, isolating its own capacity from either
    host app's request-handling overhead."""

    host = GATEWAY_HOST
    weight = 3
    wait_time = between(15, 45)

    def on_start(self) -> None:
        if not GATEWAY_TENANT_KEY:
            raise RuntimeError(
                "SAGE_GATEWAY_TENANT_KEY is not set -- GatewayDirectUser needs a real per-tenant "
                "bearer key (Secret Manager: quasar-sage-tenant-keys in quasar-business-sage)."
            )

    @task
    def ask_sage(self):
        scenario = _pick_scenario()
        with self.client.post(
            "/v1/completions",
            json=_build_payload(scenario),
            headers={"Authorization": f"Bearer {GATEWAY_TENANT_KEY}"},
            name=f"Gateway /v1/completions ({scenario['module']})",
            catch_response=True,
            timeout=REQUEST_TIMEOUT,
        ) as r:
            _check_response(r, "Gateway")
