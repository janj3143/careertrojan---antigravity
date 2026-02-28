$ErrorActionPreference = "Stop"

function Resolve-Python {
    $candidates = @(
        "J:\Python311\python.exe",
        (Join-Path $APP_ROOT ".venv-j\Scripts\python.exe"),
        (Join-Path $APP_ROOT ".venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$APP_ROOT = Resolve-Path (Join-Path $PSScriptRoot "..")
$hostValue = if ($env:CAREERTROJAN_HOST) { $env:CAREERTROJAN_HOST } else { "0.0.0.0" }
$portValue = if ($env:CAREERTROJAN_PORT) { $env:CAREERTROJAN_PORT } else { "8500" }

Write-Host "Starting CareerTrojan Backend Service..." -ForegroundColor Cyan
Write-Host "Root: $APP_ROOT" -ForegroundColor Yellow
Write-Host "Port: $portValue" -ForegroundColor Yellow
Write-Host "Host: $hostValue" -ForegroundColor Yellow
Write-Host "Environment: Runtime (J-drive)" -ForegroundColor Magenta

# 1. Set Environment Variables (J-drive relative)
$Env:PYTHONPATH = "$APP_ROOT"
if (-not $Env:CAREERTROJAN_DATA_ROOT) { $Env:CAREERTROJAN_DATA_ROOT = "L:\Codec-Antigravity Data set" }
if (-not $Env:CAREERTROJAN_AI_DATA) { $Env:CAREERTROJAN_AI_DATA = "L:\Codec-Antigravity Data set\ai_data_final" }
if (-not $Env:INTELLICV_DATA_ROOT) { $Env:INTELLICV_DATA_ROOT = $Env:CAREERTROJAN_AI_DATA }

# 2. Check Python
$PYTHON_PATH = Resolve-Python
if (-not $PYTHON_PATH) {
    Write-Error "Python not found. Expected J:\Python311\python.exe or project venv."
    exit 1
}

# 3. Ensure runtime directories exist
if (-not (Test-Path (Join-Path $APP_ROOT "tests"))) { New-Item -ItemType Directory -Force -Path (Join-Path $APP_ROOT "tests") | Out-Null }
if (-not (Test-Path (Join-Path $APP_ROOT "logs"))) { New-Item -ItemType Directory -Force -Path (Join-Path $APP_ROOT "logs") | Out-Null }

# 4. Launch Uvicorn
Set-Location $APP_ROOT
Write-Host "Launching Uvicorn with $PYTHON_PATH..." -ForegroundColor Green
& $PYTHON_PATH -m uvicorn services.backend_api.main:app --host $hostValue --port $portValue --reload --reload-dir "$APP_ROOT"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Service crashed or stopped." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
