<#
.SYNOPSIS
    CareerTrojan — Run All API Health Checks
.DESCRIPTION
    Triggers the /api/admin/v1/api-health/run-all endpoint, formats results,
    and writes a timestamped summary to logs/api_health/.
.EXAMPLE
    .\scripts\run_all.ps1
    .\scripts\run_all.ps1 -BaseUrl http://localhost:8500
#>

param(
    [string]$BaseUrl = "http://localhost:8500"
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logDir = Join-Path $PSScriptRoot "..\logs\api_health"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir "run_all_$timestamp.json"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        CareerTrojan — API Health Check: Run All             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Base URL:  $BaseUrl" -ForegroundColor DarkGray
Write-Host "  Log File:  $logFile" -ForegroundColor DarkGray
Write-Host ""

# ── Step 1: Quick health ping ────────────────────────────
Write-Host "[1/3] Checking /health ..." -ForegroundColor Yellow
try {
    $healthResp = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10
    Write-Host "      ✓ Backend is alive" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Backend not reachable at $BaseUrl" -ForegroundColor Red
    Write-Host "      Start the backend first:  python -m uvicorn services.backend_api.main:app --port 8500" -ForegroundColor DarkGray
    exit 1
}

# ── Step 2: Trigger run-all ──────────────────────────────
Write-Host "[2/3] Running full endpoint probe ..." -ForegroundColor Yellow
try {
    $result = Invoke-RestMethod -Uri "$BaseUrl/api/admin/v1/api-health/run-all" -Method POST -TimeoutSec 120
} catch {
    Write-Host "      ✗ run-all failed: $_" -ForegroundColor Red
    exit 1
}

# ── Step 3: Display results ──────────────────────────────
$probed  = $result.probed
$passed  = $result.passed
$failed  = $result.failed
$skipped = $result.skipped
$rate    = $result.pass_rate
$avgMs   = $result.avg_response_ms
$total   = $result.total_endpoints

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                      RESULTS SUMMARY                        ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host ("║  Total Endpoints:  {0,-5}                                    ║" -f $total) -ForegroundColor White
Write-Host ("║  Probed (GET):     {0,-5}                                    ║" -f $probed) -ForegroundColor White
Write-Host ("║  Passed:           {0,-5}                                    ║" -f $passed) -ForegroundColor Green
Write-Host ("║  Failed:           {0,-5}                                    ║" -f $failed) -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ("║  Skipped:          {0,-5}  (POST/PUT/DELETE/parameterised)   ║" -f $skipped) -ForegroundColor DarkGray
Write-Host ("║  Pass Rate:        {0}%                                     ║" -f $rate) -ForegroundColor $(if ($rate -ge 90) { "Green" } elseif ($rate -ge 70) { "Yellow" } else { "Red" })
Write-Host ("║  Avg Response:     {0} ms                                   ║" -f $avgMs) -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Failed endpoints detail ──────────────────────────────
$failures = $result.results | Where-Object { $_.status -notin @("pass", "auth-required", "missing-params") }
if ($failures.Count -gt 0) {
    Write-Host "  FAILED ENDPOINTS:" -ForegroundColor Red
    Write-Host "  ─────────────────" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host ("    [{0}] {1}  →  {2} ({3}ms)" -f $f.status_code, $f.path, $f.status, $f.response_time_ms) -ForegroundColor Red
        if ($f.excerpt) {
            Write-Host ("           {0}" -f ($f.excerpt.Substring(0, [Math]::Min(120, $f.excerpt.Length)))) -ForegroundColor DarkRed
        }
    }
    Write-Host ""
}

# ── Slow endpoints (>500ms) ──────────────────────────────
$slow = $result.results | Where-Object { $_.response_time_ms -gt 500 }
if ($slow.Count -gt 0) {
    Write-Host "  SLOW ENDPOINTS (>500ms):" -ForegroundColor Yellow
    Write-Host "  ────────────────────────" -ForegroundColor Yellow
    foreach ($s in $slow) {
        Write-Host ("    {0}  →  {1}ms" -f $s.path, $s.response_time_ms) -ForegroundColor Yellow
    }
    Write-Host ""
}

# ── Save full JSON log ───────────────────────────────────
$result | ConvertTo-Json -Depth 10 | Out-File -FilePath $logFile -Encoding utf8
Write-Host "[3/3] Full results saved to: $logFile" -ForegroundColor Green
Write-Host ""

# ── Exit code ────────────────────────────────────────────
if ($failed -gt 0) {
    Write-Host "  ⚠ $failed endpoint(s) need attention." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "  ✓ All probed endpoints healthy." -ForegroundColor Green
    exit 0
}
