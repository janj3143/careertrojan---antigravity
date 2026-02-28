$ErrorActionPreference = "Stop"

function Resolve-Python {
    $appRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
    $candidates = @(
        "J:\Python311\python.exe",
        (Join-Path $appRoot ".venv-j\Scripts\python.exe"),
        (Join-Path $appRoot ".venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$APP_ROOT = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$PYTHON = Resolve-Python
if (-not $PYTHON) {
    Write-Error "Python not found. Expected J:\Python311\python.exe or project-local venv."
    exit 1
}

$env:PYTHONPATH = "$APP_ROOT"
Set-Location $PSScriptRoot
& $PYTHON -m uvicorn main:app --app-dir $PSScriptRoot --reload --port 8000
