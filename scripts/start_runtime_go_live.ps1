# CareerTrojan Go-Live Runtime Starter
# Canonical env source: careertrojan/.env

param(
    [switch]$SkipValidation,
    [int]$Port = 8500
)

$ErrorActionPreference = "Stop"

$AppRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$EnvFile = Join-Path $AppRoot ".env"

function Resolve-Python {
    $candidates = @(
        (Join-Path $AppRoot ".venv\Scripts\python.exe"),
        (Join-Path $AppRoot ".venv-j\Scripts\python.exe"),
        "J:\Python311\python.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "Python executable not found."
}

if (-not (Test-Path $EnvFile)) {
    throw "Missing canonical env file: $EnvFile"
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
    }
}

$env:PYTHONPATH = "."
$PythonExe = Resolve-Python

Write-Host "[INFO] Canonical env loaded from $EnvFile" -ForegroundColor Cyan

if (-not $SkipValidation) {
    Write-Host "[INFO] Validating runtime env..." -ForegroundColor Cyan
    & $PythonExe (Join-Path $AppRoot "scripts\validate_runtime_env.py") --env-file $EnvFile --strict
    if ($LASTEXITCODE -ne 0) {
        throw "Runtime env validation failed. Startup aborted."
    }
}

Write-Host "[INFO] Starting backend runtime on port $Port" -ForegroundColor Green
Set-Location $AppRoot
& $PythonExe -m uvicorn services.backend_api.main:app --host 0.0.0.0 --port $Port --reload
