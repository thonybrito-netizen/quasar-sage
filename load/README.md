# Sage concurrent-user load test

`locustfile.py` simulates 100 concurrent users interacting with Sage
across all three real entry points at once (QuietNoise's proxy route,
Lorito's authenticated backend, and the Gateway directly) rather than
hammering one synthetic target. Read the full docstring at the top of
that file before running it -- it covers env vars, expected latency
targets, and a real cost/rate-limit warning that matters before running
at full scale (every request is a real Anthropic API call).

**Validated 2026-08-21** with a small real run (6 users, 90s, against
production): 6/6 requests succeeded across the QuietNoise and Gateway
paths, latencies 12-52s. The full 100-user run has not been executed --
that's a real-cost decision left to whoever runs it, with a timing window
of their choosing. See the docstring's warning section.

## Quick start

```
cd load
pip install locust
export SAGE_GATEWAY_TENANT_KEY="<real key from Secret Manager: quasar-sage-tenant-keys>"
export LORITO_TEST_TOKEN="Bearer <real Firebase ID token, or ck_... API key>"

# Sanity check first -- small and short
locust -f locustfile.py --headless -u 5 -r 1 --run-time 2m

# Full 100-user run
locust -f locustfile.py --headless -u 100 -r 5 --run-time 10m --html load_report.html
```

Omit `LORITO_TEST_TOKEN` to run without `LoritoSageUser` (it raises
cleanly in `on_start` and Locust logs it as that user's error without
affecting the other two user types -- confirmed in the validation run
above).
