<#
.SYNOPSIS
    Executes the full CareerTrojan testing pyramid plus local physical terminal checks.

.DESCRIPTION
    Tier 1: Preflight runtime review (via full_harness -> agent_manager)
    Tier 2: Unit tests
    Tier 3: Integration tests
    Tier 4: E2E tests
    Physical: Live endpoint/login/coaching uptime checks against host port 8600+

.EXAMPLE
    .\scripts\run_testing_pyramid_all_tiers.ps1
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = $(if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { (Get-Location).Path }),
    [string]$PythonBin = "J:\Python311\python.exe",
    [string]$BaseUrl = "http://127.0.0.1:8600",
    [double]$MinPassRate = 80.0,
    [switch]$Require100
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$Candidate)
    if ($Candidate -and (Test-Path $Candidate)) { return $Candidate }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "Python executable not found. Set -PythonBin explicitly."
}

$project = (Resolve-Path $ProjectRoot).Path
$python = Resolve-Python -Candidate $PythonBin
$fullHarness = Join-Path $project "scripts\full_harness.ps1"
$uptimeScript = Join-Path $project "scripts\coaching_endpoint_uptime_check.py"
$resultsDir = Join-Path $project "logs\test_results"
$physicalLog = Join-Path $resultsDir "physical_checks_output.txt"

if (-not (Test-Path $resultsDir)) {
    New-Item -Path $resultsDir -ItemType Directory -Force | Out-Null
}

if (-not (Test-Path $fullHarness)) { throw "Missing script: $fullHarness" }
if (-not (Test-Path $uptimeScript)) { throw "Missing script: $uptimeScript" }

Write-Host "Running full testing pyramid (tiers 1-4)..." -ForegroundColor Cyan
if ($Require100) {
    & $fullHarness -ProjectRoot $project -Require100
} else {
    & $fullHarness -ProjectRoot $project -MinPassRate $MinPassRate
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tiered harness failed. Skipping physical checks." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Running physical terminal checks against $BaseUrl ..." -ForegroundColor Cyan
& $python $uptimeScript --base-url $BaseUrl 2>&1 | Tee-Object -FilePath $physicalLog

if ($LASTEXITCODE -ne 0) {
    Write-Host "Physical checks failed. See: $physicalLog" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "All testing pyramid tiers + physical checks passed." -ForegroundColor Green
exit 0
