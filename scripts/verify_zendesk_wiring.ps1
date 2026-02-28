param(
    [string]$BaseUrl = "http://localhost:8500",
    [switch]$Strict,
    [switch]$Deep
)

$ErrorActionPreference = "Stop"

function Invoke-JsonGet {
    param([string]$Url)
    try {
        return Invoke-RestMethod -Method Get -Uri $Url -TimeoutSec 20
    }
    catch {
        Write-Host "[FAIL] GET $Url" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor DarkRed
        throw
    }
}

function Invoke-JsonPost {
    param(
        [string]$Url,
        [object]$Body
    )
    try {
        return Invoke-RestMethod -Method Post -Uri $Url -TimeoutSec 20 -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 8)
    }
    catch {
        Write-Host "[FAIL] POST $Url" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor DarkRed
        throw
    }
}

$base = $BaseUrl.TrimEnd("/")
$healthUrl = "$base/health"
$providersUrl = "$base/api/support/v1/providers"
$readinessUrl = "$base/api/support/v1/readiness"
$statusUrl = "$base/api/support/v1/status"
$tokenUrl = "$base/api/support/v1/token"
$widgetUrl = "$base/api/support/v1/widget-config?portal=user&user_id=verify-user&user_email=verify@example.com"

Write-Host "Checking Zendesk wiring against $base ..." -ForegroundColor Cyan

try {
    $health = Invoke-JsonGet -Url $healthUrl
    $healthStatus = [string]$health.status
    if ($healthStatus -notin @("ok", "healthy")) {
        Write-Host "[WARN] Backend /health responded, but status is '$healthStatus'." -ForegroundColor DarkYellow
    }
}
catch {
    Write-Host "[FAIL] Backend health check failed at $healthUrl" -ForegroundColor Red
    Write-Host "Start backend first, then rerun this script." -ForegroundColor DarkYellow
    Write-Host "Suggested command: Push-Location careertrojan; ..\\.venv\\Scripts\\python.exe -m uvicorn services.backend_api.main:app --host 0.0.0.0 --port 8500" -ForegroundColor DarkYellow
    if ($Strict) {
        exit 3
    }
    else {
        exit 1
    }
}

try {
    $providers = Invoke-JsonGet -Url $providersUrl
    $readiness = Invoke-JsonGet -Url $readinessUrl
    $status = Invoke-JsonGet -Url $statusUrl
}
catch {
    Write-Host "[FAIL] Support endpoints are not available from this API instance." -ForegroundColor Red
    Write-Host "If backend is running, ensure the support router is mounted and service config is loaded." -ForegroundColor DarkYellow
    Write-Host "Recheck: GET $base/health and GET $base/api/support/v1/status" -ForegroundColor DarkYellow
    if ($Strict) {
        exit 4
    }
    else {
        exit 1
    }
}

Write-Host "`n== Providers ==" -ForegroundColor Yellow
$providers | ConvertTo-Json -Depth 8

Write-Host "`n== Readiness ==" -ForegroundColor Yellow
$readiness | ConvertTo-Json -Depth 8

Write-Host "`n== Status ==" -ForegroundColor Yellow
$status | ConvertTo-Json -Depth 8

if ($Deep) {
    Write-Host "`n== Deep Checks ==" -ForegroundColor Yellow
    try {
        $tokenResp = Invoke-JsonPost -Url $tokenUrl -Body @{
            subject = "verify-user"
            email = "verify@example.com"
            name = "Verifier"
            ttl_seconds = 300
        }
        Write-Host "[OK] POST /token returned status=$($tokenResp.status), mode=$($tokenResp.mode)" -ForegroundColor Green
    }
    catch {
        if ($Strict) { exit 5 }
    }

    try {
        $widgetResp = Invoke-JsonGet -Url $widgetUrl
        Write-Host "[OK] GET /widget-config returned status=$($widgetResp.status), mode=$($widgetResp.mode)" -ForegroundColor Green
    }
    catch {
        if ($Strict) { exit 6 }
    }
}

$provider = [string]($providers.active.provider)
$mode = [string]($providers.active.mode)
$ready = [bool]$readiness.ready

$failed = $false

if ($provider -ne "zendesk") {
    Write-Host "`n[WARN] Active provider is '$provider' (expected 'zendesk')." -ForegroundColor DarkYellow
    if ($Strict) { $failed = $true }
}

if ($mode -ne "zendesk") {
    Write-Host "[WARN] Active mode is '$mode' (expected 'zendesk')." -ForegroundColor DarkYellow
    if ($Strict) { $failed = $true }
}

if (-not $ready) {
    Write-Host "[WARN] Readiness is false; missing config detected:" -ForegroundColor DarkYellow
    $missing = @($readiness.missing)
    if ($missing.Count -gt 0) {
        $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor DarkYellow }
    }
    if ($Strict) { $failed = $true }
}

if ($failed) {
    Write-Host "`n[FAIL] Zendesk wiring verification failed in strict mode." -ForegroundColor Red
    exit 2
}

Write-Host "`n[OK] Zendesk wiring verification completed." -ForegroundColor Green
exit 0
