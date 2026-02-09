<#
.SYNOPSIS
    Bootstrap script for the CareerTrojan Runtime.
    Handles environment validation, disk mount checks, and container startup.
#>

$ErrorActionPreference = "Stop"

# --- Configuration ---
$DATA_ROOT_NAME = "antigravity_version_ai_data_final"
$RUNTIME_ROOT = "C:\careertrojan"
$WORKING_ROOT = Join-Path $RUNTIME_ROOT "working"
$USER_DATA_ROOT = Join-Path $RUNTIME_ROOT "user_data"
$LOG_ROOT = Join-Path $RUNTIME_ROOT "logs"

Write-Host "--- CareerTrojan Runtime Bootstrap (Phase 1) ---" -ForegroundColor Cyan

# 1. Pre-flight Checks
Write-Host "[1/5] Pre-flight Validation..." -NoNewline
try {
    # Check for Docker
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        throw "Docker is not installed or not in PATH."
    }
    
    # Check for ai_data_final (Disk L: mount)
    $ai_data_path = "L:\$DATA_ROOT_NAME"
    if (-not (Test-Path $ai_data_path)) {
        throw "CRITICAL: CareerTrojan Data Root not found at $ai_data_path. Ensure Drive L: is mapped correctly."
    }

    # Check for working directories
    if (-not (Test-Path $WORKING_ROOT)) {
        New-Item -ItemType Directory -Path $WORKING_ROOT -Force | Out-Null
    }
    
    $working_copy_path = Join-Path $WORKING_ROOT "working_copy"
    if (-not (Test-Path $working_copy_path)) {
        New-Item -ItemType Directory -Path $working_copy_path -Force | Out-Null
        Write-Host " (Created working_copy)" -NoNewline
    }

    # Check/Create User Data Root
    if (-not (Test-Path $USER_DATA_ROOT)) {
        New-Item -ItemType Directory -Path $USER_DATA_ROOT -Force | Out-Null
        Write-Host " (Created user_data)" -NoNewline
    }

    # Check/Create Logs Root
    if (-not (Test-Path $LOG_ROOT)) {
        New-Item -ItemType Directory -Path $LOG_ROOT -Force | Out-Null
        Write-Host " (Created logs)" -NoNewline
    }

    # Check for Self-Contained Python
    $python_dir = Join-Path $RUNTIME_ROOT "infra\python"
    $python_bin = Join-Path $python_dir "python.exe"
    if (-not (Test-Path $python_bin)) {
        Write-Warning "Python environment not found at $python_dir"
        Write-Warning "Strict Runtime Mode requires self-contained Python 3.11."
        # For now, we warn. In production, this should throw.
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
$env:CAREERTROJAN_DATA_ROOT = $ai_data_path
$env:CAREERTROJAN_WORKING_ROOT = $working_copy_path
$env:CAREERTROJAN_RUNTIME_ROOT = $RUNTIME_ROOT
$env:CAREERTROJAN_USER_DATA_ROOT = $USER_DATA_ROOT
$env:CAREERTROJAN_LOG_ROOT = $LOG_ROOT
$env:CAREERTROJAN_PYTHON_BIN = $python_bin
$env:ALLOW_MOCK_DATA = "false"
$env:ALLOW_FALLBACKS = "false"
$env:TEST_USER_BOOTSTRAP_ENABLED = "true" # Phase 1 Testing
Write-Host " [OK]" -ForegroundColor Green

# 3. Test User Seeding (Phase 1 Stub)
Write-Host "[3/5] Seeding Test User (janj3143)..." -NoNewline
if (-not (Test-Path $USER_DATA_ROOT)) { New-Item -ItemType Directory -Path $USER_DATA_ROOT -Force | Out-Null }
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
$dockerfile_path = Join-Path $RUNTIME_ROOT "infra\docker\compose.yaml"
if (-not (Test-Path $dockerfile_path)) {
    Write-Host " (!) Warning: compose.yaml not found at $dockerfile_path. Deployment may fail." -ForegroundColor Yellow
}

# 5. Launching Runtime
Write-Host "[5/5] Launching CareerTrojan Runtime..."
try {
    if (Test-Path $dockerfile_path) {
        Set-Location -Path (Join-Path $RUNTIME_ROOT "infra\docker")
        Write-Host "   Starting Docker services..." -ForegroundColor Cyan
        # In a real run, we would execute this:
        # docker-compose up -d
        Write-Host "   (Docker command staged - usage: docker-compose up -d)" -ForegroundColor Gray
    }
}
catch {
    Write-Warning "Failed to launch services: $_"
}

Write-Host "`nCareerTrojan Phase 1 Initialized." -ForegroundColor Green
Write-Host "Target Environment:"
Write-Host " - Data Root: $env:CAREERTROJAN_DATA_ROOT"
Write-Host " - User Data: $env:CAREERTROJAN_USER_DATA_ROOT (Writable)"
Write-Host " - Logs: $env:CAREERTROJAN_LOG_ROOT"
Write-Host " - Python: $env:CAREERTROJAN_PYTHON_BIN"
Write-Host "Test Identity:"
Write-Host " - User: janj3143"
Write-Host " - Status: Premium"
