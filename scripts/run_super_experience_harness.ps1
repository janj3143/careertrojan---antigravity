[CmdletBinding()]
param(
    [switch]$RunTiers,
    [string]$ResumePath = "",
    [string]$PythonBin = "J:\Codec - runtime version\Antigravity\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { (Get-Location).Path }

if (-not (Test-Path $PythonBin)) {
    throw "Python executable not found at: $PythonBin"
}

$scriptPath = Join-Path $projectRoot "scripts\run_super_experience_harness.py"
if (-not (Test-Path $scriptPath)) {
    throw "Missing harness script: $scriptPath"
}

$args = @($scriptPath)
if ($RunTiers) { $args += "--run-tiers" }
if ($ResumePath) { $args += @("--resume-path", $ResumePath) }

Write-Host "Running super experience harness..." -ForegroundColor Cyan
& $PythonBin @args
exit $LASTEXITCODE
