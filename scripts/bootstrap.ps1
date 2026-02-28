<#
.SYNOPSIS
    Bootstrap script for the CareerTrojan runtime on J: only.
    Handles environment validation, path setup, and staged Docker startup.
#>

param(
    [switch]$StartDocker
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    $candidates = @(
        "J:\Python311\python.exe",
        (Join-Path $RUNTIME_ROOT ".venv-j\Scripts\python.exe"),
        (Join-Path $RUNTIME_ROOT ".venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

# --- Configuration ---
$RUNTIME_ROOT = Resolve-Path (Join-Path $PSScriptRoot "..")
$WORKING_ROOT = Join-Path $RUNTIME_ROOT "working"
$WORKING_COPY_ROOT = Join-Path $WORKING_ROOT "working_copy"
$USER_DATA_ROOT = Join-Path $RUNTIME_ROOT "user_data"
$LOG_ROOT = Join-Path $RUNTIME_ROOT "logs"
$COMPOSE_PROJECT_NAME = if ($env:CAREERTROJAN_COMPOSE_PROJECT_NAME) { $env:CAREERTROJAN_COMPOSE_PROJECT_NAME } else { "codec-antigravity" }
$DATA_ROOT_DEFAULT = "L:\Codec-Antigravity Data set"
$AI_DATA_PATH = if ($env:CAREERTROJAN_DATA_ROOT) { $env:CAREERTROJAN_DATA_ROOT } else { $DATA_ROOT_DEFAULT }
$PYTHON_BIN = Resolve-Python

Write-Host "--- CareerTrojan Runtime Bootstrap (J-drive) ---" -ForegroundColor Cyan
Write-Host "Runtime Root: $RUNTIME_ROOT" -ForegroundColor Yellow

# 1. Pre-flight Checks
Write-Host "[1/5] Pre-flight Validation..." -NoNewline
try {
    if (-not (Test-Path $AI_DATA_PATH)) {
        throw "CRITICAL: Data root not found at $AI_DATA_PATH. Ensure drive mapping is available."
    }

    foreach ($path in @($WORKING_ROOT, $WORKING_COPY_ROOT, $USER_DATA_ROOT, $LOG_ROOT)) {
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }

    if (-not $PYTHON_BIN) {
        throw "Python not found. Expected J:\Python311\python.exe or a project-local venv."
    }

    Write-Host " [OK]" -ForegroundColor Green
}
catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Error $_.Exception.Message
    exit 1
}

# 2. Environment Setup
Write-Host "[2/5] Setting up Environment Variables..." -NoNewline
$env:CAREERTROJAN_DATA_ROOT = $AI_DATA_PATH
$env:CAREERTROJAN_WORKING_ROOT = $WORKING_COPY_ROOT
$env:CAREERTROJAN_RUNTIME_ROOT = "$RUNTIME_ROOT"
$env:CAREERTROJAN_USER_DATA_ROOT = $USER_DATA_ROOT
$env:CAREERTROJAN_LOG_ROOT = $LOG_ROOT
$env:CAREERTROJAN_PYTHON_BIN = $PYTHON_BIN
$env:CAREERTROJAN_COMPOSE_PROJECT_NAME = $COMPOSE_PROJECT_NAME
$env:ALLOW_MOCK_DATA = "false"
$env:ALLOW_FALLBACKS = "false"
$env:TEST_USER_BOOTSTRAP_ENABLED = "true"
Write-Host " [OK]" -ForegroundColor Green

# 3. Test User Seeding (Phase 1 Stub)
Write-Host "[3/5] Seeding Test User (janj3143)..." -NoNewline
$seedFile = Join-Path $USER_DATA_ROOT "users.json"
$testUser = @{
    username = "janj3143"
    role     = "premium"
    email    = "janj3143@careertrojan.internal"
    status   = "active"
    is_mock  = $true
}
$testUser | ConvertTo-Json | Out-File $seedFile -Encoding utf8
Write-Host " [SEEDED]" -ForegroundColor Green

# 4. Infrastructure Check
Write-Host "[4/5] Validating Infrastructure..."
$composePath = Join-Path $RUNTIME_ROOT "infra\docker\compose.yaml"
if (-not (Test-Path $composePath)) {
    Write-Host " (!) Warning: compose.yaml not found at $composePath." -ForegroundColor Yellow
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host " (!) Warning: docker command not found in PATH. Docker startup will be skipped." -ForegroundColor Yellow
}

# 5. Launching Runtime (optional)
Write-Host "[5/5] Runtime Launch Stage"
if ($StartDocker -and (Test-Path $composePath) -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    try {
        Set-Location -Path (Join-Path $RUNTIME_ROOT "infra\docker")
        Write-Host "   Starting Docker services (project: $COMPOSE_PROJECT_NAME)..." -ForegroundColor Cyan
        docker compose -p $COMPOSE_PROJECT_NAME -f $composePath up -d
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose up failed with exit code $LASTEXITCODE"
        }
        Write-Host "   Docker services started." -ForegroundColor Green
    }
    catch {
        Write-Warning "Failed to launch docker services: $_"
    }
} else {
    Write-Host "   Docker launch skipped. Use -StartDocker to launch if docker is available." -ForegroundColor Gray
}

Write-Host "`nCareerTrojan Bootstrap Completed." -ForegroundColor Green
Write-Host "Target Environment:"
Write-Host " - Data Root: $env:CAREERTROJAN_DATA_ROOT"
Write-Host " - User Data: $env:CAREERTROJAN_USER_DATA_ROOT"
Write-Host " - Logs: $env:CAREERTROJAN_LOG_ROOT"
Write-Host " - Python: $env:CAREERTROJAN_PYTHON_BIN"
