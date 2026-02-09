# ═══════════════════════════════════════════════════════════════
# Start-And-Map.ps1  — CareerTrojan Runtime Launcher (Windows)
# ═══════════════════════════════════════════════════════════════
# 1. Validates drive connections (L:, E:, C:\careertrojan)
# 2. Verifies data-mount junctions
# 3. Ensures USER DATA directory structure exists
# 4. Starts the sync trap (L: ↔ E: user data mirror)
# 5. Starts the FastAPI backend
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$APP_ROOT = "C:\careertrojan"
$ENV_FILE = Join-Path $APP_ROOT ".env"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   CareerTrojan — Runtime Start & Map         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. Load .env ──────────────────────────────────────────────
if (Test-Path $ENV_FILE) {
    Get-Content $ENV_FILE | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
    Write-Host "[OK] Loaded .env" -ForegroundColor Green
} else {
    Write-Host "[WARN] No .env file found at $ENV_FILE" -ForegroundColor Yellow
}

# ── 2. Validate Drive Connections ─────────────────────────────
$drives = @{
    "L: (Source of Truth)" = "L:\VS ai_data final - version"
    "E: (Mirror Backup)"  = "E:\CareerTrojan"
    "C: (App Root)"        = $APP_ROOT
}

$allDrivesOK = $true
foreach ($label in $drives.Keys) {
    $path = $drives[$label]
    if (Test-Path $path) {
        Write-Host "[OK] $label → $path" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $label → $path NOT FOUND" -ForegroundColor Red
        $allDrivesOK = $false
    }
}

if (-not $allDrivesOK) {
    Write-Host ""
    Write-Host "[WARN] Some drives are not connected. Runtime may be degraded." -ForegroundColor Yellow
}

# ── 3. Verify Data-Mount Junctions ───────────────────────────
$mounts = @{
    "ai-data"   = Join-Path $APP_ROOT "data-mounts\ai-data"
    "parser"    = Join-Path $APP_ROOT "data-mounts\parser"
    "user-data" = Join-Path $APP_ROOT "data-mounts\user-data"
}

foreach ($name in $mounts.Keys) {
    $mp = $mounts[$name]
    if (Test-Path $mp) {
        $item = Get-Item $mp
        if ($item.LinkType -eq "Junction") {
            Write-Host "[OK] Junction: $name → $($item.Target)" -ForegroundColor Green
        } else {
            Write-Host "[OK] Directory: $name (not a junction)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[MISS] Mount not found: $name ($mp)" -ForegroundColor Red
    }
}

# ── 4. Ensure USER DATA Structure ────────────────────────────
$userDataDirs = @(
    "sessions", "profiles", "interactions", "cv_uploads",
    "ai_matches", "session_logs", "admin_2fa", "test_accounts",
    "trap_profiles", "trap_reports", "user_registry", "quarantine"
)

$primaryUD = $env:CAREERTROJAN_USER_DATA
$mirrorUD  = $env:CAREERTROJAN_USER_DATA_MIRROR

foreach ($root in @($primaryUD, $mirrorUD)) {
    if ($root -and (Test-Path (Split-Path $root -Parent))) {
        foreach ($sub in $userDataDirs) {
            $dir = Join-Path $root $sub
            if (-not (Test-Path $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
            }
        }
        Write-Host "[OK] User data structure ensured: $root" -ForegroundColor Green
    }
}

# ── 5. Start Sync Trap (background) ──────────────────────────
$PYTHON = if (Test-Path "C:\careertrojan\infra\python\python.exe") {
    "C:\careertrojan\infra\python\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} else {
    $null
}

if ($PYTHON) {
    $syncScript = Join-Path $APP_ROOT "scripts\sync_user_data.py"
    if (Test-Path $syncScript) {
        Write-Host "[START] Sync trap (L: ↔ E:)..." -ForegroundColor Cyan
        Start-Process -FilePath $PYTHON -ArgumentList $syncScript, "--daemon" `
            -WindowStyle Hidden -PassThru | Out-Null
        Write-Host "[OK] Sync trap running in background" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] Sync script not found: $syncScript" -ForegroundColor Yellow
    }
} else {
    Write-Host "[SKIP] Python not found — cannot start sync trap" -ForegroundColor Yellow
}

# ── 6. Start FastAPI Backend ─────────────────────────────────
$Host_ = $env:CAREERTROJAN_HOST
if (-not $Host_) { $Host_ = "0.0.0.0" }
$Port = $env:CAREERTROJAN_PORT
if (-not $Port) { $Port = "8500" }

Write-Host ""
Write-Host "[START] FastAPI backend on ${Host_}:${Port}" -ForegroundColor Cyan
Set-Location $APP_ROOT

& $PYTHON -m uvicorn services.backend_api.main:app --host $Host_ --port $Port --reload

