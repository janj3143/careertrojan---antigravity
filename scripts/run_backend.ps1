$ErrorActionPreference = "Stop"

Write-Host "Starting CareerTrojan Backend Service..." -ForegroundColor Cyan
Write-Host "Port: 8500" -ForegroundColor Yellow
Write-Host "Host: 0.0.0.0" -ForegroundColor Yellow
Write-Host "Environment: Production/Runtime" -ForegroundColor Magenta

# 1. Set Environment Variables
$Env:PYTHONPATH = "C:\careertrojan"
$Env:CAREERTROJAN_DATA_ROOT = "L:\antigravity_version_ai_data_final\ai_data_final"
$Env:INTELLICV_DATA_ROOT = "L:\antigravity_version_ai_data_final\ai_data_final"

# 2. Check Python
$PYTHON_PATH = "C:\Python\python.exe"
if (-not (Test-Path $PYTHON_PATH)) {
    Write-Error "Python not found at $PYTHON_PATH"
    exit 1
}

# 3. Ensure Directories Exist (Fixes Uvicorn Watcher Crash)
if (-not (Test-Path "$Env:PYTHONPATH\tests")) { New-Item -ItemType Directory -Force -Path "$Env:PYTHONPATH\tests" | Out-Null }
if (-not (Test-Path "$Env:PYTHONPATH\logs")) { New-Item -ItemType Directory -Force -Path "$Env:PYTHONPATH\logs" | Out-Null }

# 4. Launch Uvicorn
Write-Host "Launching Uvicorn..." -ForegroundColor Green
& $PYTHON_PATH -m uvicorn services.backend_api.main:app --host 0.0.0.0 --port 8500 --reload --reload-dir "$Env:PYTHONPATH"

# Keep window open if it crashes immediately
if ($LASTEXITCODE -ne 0) {
    Write-Host "Service crashed or stopped." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
