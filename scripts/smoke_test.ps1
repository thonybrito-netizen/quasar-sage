# Quasar Sage Gateway smoke test. Assumes the Gateway is already running
# locally (see README.md) and its .env's TENANT_API_KEYS includes a
# "quietnoise" key matching -ApiKey below.
#
# Usage: .\scripts\smoke_test.ps1 [-GatewayUrl http://localhost:8090] [-ApiKey qn-dev-placeholder]
#
# With no real ANTHROPIC_API_KEY configured, the completions calls are
# expected to return resolved_via="graceful_fallback" with an explicit
# "no model backend configured" message -- that's a PASS for this script
# (it proves the pipeline runs end-to-end), not a failure. Once a real key
# is set, the same calls should return resolved_via="first_attempt" (or
# "invisible_retry") with non-empty generated_content -- this script flags
# that distinction so you can tell which regime you're testing in.

param(
    [string]$GatewayUrl = "http://localhost:8090",
    [string]$ApiKey = "qn-dev-placeholder"
)

$ErrorActionPreference = "Stop"
$failures = 0

function Check($name, $block) {
    try {
        & $block
        Write-Host "[PASS] $name" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $name -- $_" -ForegroundColor Red
        $script:failures++
    }
}

Check "GET /health" {
    $r = Invoke-RestMethod -Uri "$GatewayUrl/health"
    if ($r.status -ne "ok") { throw "unexpected body: $($r | ConvertTo-Json -Compress)" }
}

Check "GET /v1/modules lists all five, Visionary+Storyteller live" {
    $r = Invoke-RestMethod -Uri "$GatewayUrl/v1/modules" -Headers @{ Authorization = "Bearer $ApiKey" }
    if ($r.Count -ne 5) { throw "expected 5 modules, got $($r.Count)" }
    $byId = @{}
    foreach ($m in $r) { $byId[$m.module_id] = $m }
    if (-not $byId["visionary"].live) { throw "visionary should be live" }
    if (-not $byId["storyteller"].live) { throw "storyteller should be live" }
    if ($byId["dealmaker"].live) { throw "dealmaker should not be live yet" }
}

Check "POST /v1/completions rejects a bad key with 401" {
    try {
        Invoke-RestMethod -Uri "$GatewayUrl/v1/completions" -Method Post `
            -Headers @{ Authorization = "Bearer not-a-real-key" } -ContentType "application/json" `
            -Body (@{ module = "visionary"; user_message = "hi"; context = @{} } | ConvertTo-Json)
        throw "expected a 401, request succeeded"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }
    }
}

foreach ($module in @("visionary", "storyteller")) {
    Check "POST /v1/completions ($module)" {
        $body = @{ module = $module; user_message = "Give me a sample response for a smoke test."; context = @{ enemy = "legacy tooling" } } | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$GatewayUrl/v1/completions" -Method Post `
            -Headers @{ Authorization = "Bearer $ApiKey" } -ContentType "application/json" -Body $body
        if ($r.module -ne $module) { throw "module mismatch: $($r.module)" }
        if ($r.resolved_via -eq "graceful_fallback" -and $r.strategic_critique -like "*no model backend configured*") {
            Write-Host "        (no ANTHROPIC_API_KEY set yet -- clean fallback confirmed, not a real generation)" -ForegroundColor Yellow
        } elseif (-not $r.generated_content) {
            throw "expected non-empty generated_content for resolved_via=$($r.resolved_via)"
        } else {
            Write-Host "        real completion received (resolved_via=$($r.resolved_via))" -ForegroundColor Cyan
        }
    }
}

Check "POST /v1/completions (dealmaker stub never calls Claude)" {
    $body = @{ module = "dealmaker"; mode = "enterprise"; user_message = "test"; context = @{} } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$GatewayUrl/v1/completions" -Method Post `
        -Headers @{ Authorization = "Bearer $ApiKey" } -ContentType "application/json" -Body $body
    if ($r.resolved_via -ne "graceful_fallback") { throw "expected graceful_fallback, got $($r.resolved_via)" }
    if ($r.generated_content) { throw "stub module should never generate content" }
}

Write-Host ""
if ($failures -eq 0) {
    Write-Host "All checks passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "$failures check(s) failed." -ForegroundColor Red
    exit 1
}
