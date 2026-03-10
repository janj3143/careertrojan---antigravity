<#
.SYNOPSIS
    Runs the complete CareerTrojan harness on J-drive and writes summary artifacts.

.DESCRIPTION
    - Enforces J-drive project root usage.
    - Executes agent_manager in full mode (runtime review + unit/integration/E2E).
    - Parses junit XML results and latest runtime-review score.
    - Writes summary JSON and Markdown to logs/test_results.
    - Exits non-zero if gating thresholds are not met.

.EXAMPLE
    .\scripts\full_harness.ps1

.EXAMPLE
    .\scripts\full_harness.ps1 -Require100

.EXAMPLE
    .\scripts\full_harness.ps1 -MinPassRate 90
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = $(if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { (Get-Location).Path }),
    [double]$MinPassRate = 80.0,
    [switch]$Require100,
    [switch]$SkipRouteGovernance,
    [int]$MaxAddedRoutes = 50,
    [int]$MaxRemovedRoutes = 5,
    [int]$MaxHighChurnBuckets = 10,
    [int]$MaxDuplicateSemanticRoutes = 10
)

$ErrorActionPreference = "Stop"

function Get-JunitMetrics {
    param([Parameter(Mandatory = $true)][string]$XmlPath)

    $default = [pscustomobject]@{
        Tests = 0
        Failures = 0
        Errors = 0
        Skipped = 0
        PassRate = 0.0
        Exists = $false
    }

    if (-not (Test-Path $XmlPath)) {
        return $default
    }

    [xml]$doc = Get-Content -Path $XmlPath
    $suite = $null

    if ($doc.testsuites -and $doc.testsuites.testsuite) {
        $suite = $doc.testsuites.testsuite
    } elseif ($doc.testsuite) {
        $suite = $doc.testsuite
    } else {
        return $default
    }

    $tests = [int]$suite.tests
    $failures = [int]$suite.failures
    $errors = [int]$suite.errors
    $skipped = if ($suite.skipped -ne $null) { [int]$suite.skipped } else { 0 }
    $passRate = if ($tests -gt 0) {
        [math]::Round((($tests - $failures - $errors) / $tests) * 100, 1)
    } else {
        0.0
    }

    return [pscustomobject]@{
        Tests = $tests
        Failures = $failures
        Errors = $errors
        Skipped = $skipped
        PassRate = $passRate
        Exists = $true
    }
}

function Get-LatestRuntimeScore {
    param([Parameter(Mandatory = $true)][string]$LogsRoot)

    $latest = Get-ChildItem -Path $LogsRoot -Filter "agent_manager_*.log" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $latest) {
        return $null
    }

    $line = Select-String -Path $latest.FullName -Pattern "RUNTIME REVIEW SCORE:\s*(\d+)\s*/\s*(\d+)\s*\(([\d\.]+)%\)" |
        Select-Object -Last 1

    if (-not $line) {
        return $null
    }

    $match = [regex]::Match($line.Line, "RUNTIME REVIEW SCORE:\s*(\d+)\s*/\s*(\d+)\s*\(([\d\.]+)%\)")
    if (-not $match.Success) {
        return $null
    }

    return [pscustomobject]@{
        Score = [int]$match.Groups[1].Value
        Max = [int]$match.Groups[2].Value
        Percent = [double]$match.Groups[3].Value
        LogPath = $latest.FullName
    }
}

function Resolve-Python {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectRootPath
    )

    $candidates = @(
        (Join-Path $ProjectRootPath "..\.venv\Scripts\python.exe"),
        (Join-Path $ProjectRootPath ".venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        try {
            $resolved = (Resolve-Path $candidate -ErrorAction SilentlyContinue)
            if ($resolved) {
                return $resolved.Path
            }
        }
        catch {
        }
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    throw "Python executable not found for route governance scripts."
}

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root does not exist: $ProjectRoot"
}

$normalizedRoot = (Resolve-Path $ProjectRoot).Path
if (-not $normalizedRoot.StartsWith("J:\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to run outside J-drive. ProjectRoot must be on J:\. Got: $normalizedRoot"
}

$agentScript = Join-Path $PSScriptRoot "agent_manager.ps1"
if (-not (Test-Path $agentScript)) {
    throw "Missing harness dependency: $agentScript"
}

$resultsDir = Join-Path $normalizedRoot "logs\test_results"
if (-not (Test-Path $resultsDir)) {
    New-Item -Path $resultsDir -ItemType Directory -Force | Out-Null
}

$threshold = if ($Require100) { 100.0 } else { $MinPassRate }
$pythonExe = Resolve-Python -ProjectRootPath $normalizedRoot
$routeGovScript = Join-Path $normalizedRoot "scripts\route_governance_report.py"
$routeGovGateScript = Join-Path $normalizedRoot "scripts\validate_route_governance.py"

if (-not (Test-Path $routeGovScript)) {
    throw "Missing harness dependency: $routeGovScript"
}
if (-not (Test-Path $routeGovGateScript)) {
    throw "Missing harness dependency: $routeGovGateScript"
}

Write-Host "Running full harness on J-drive..." -ForegroundColor Cyan
Write-Host "Project root: $normalizedRoot" -ForegroundColor Yellow
Write-Host "Pass threshold: $threshold%" -ForegroundColor Yellow

& $agentScript -Mode all -ProjectRoot $normalizedRoot
if ($LASTEXITCODE -ne 0) {
    throw "agent_manager failed with exit code $LASTEXITCODE"
}

$unit = Get-JunitMetrics -XmlPath (Join-Path $resultsDir "unit_results.xml")
$integration = Get-JunitMetrics -XmlPath (Join-Path $resultsDir "integration_results.xml")
$e2e = Get-JunitMetrics -XmlPath (Join-Path $resultsDir "e2e_results.xml")
$runtime = Get-LatestRuntimeScore -LogsRoot (Join-Path $normalizedRoot "logs")
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$failures = @()
if ($unit.Tests -eq 0) { $failures += "Unit tests executed: 0" }
if ($integration.Tests -eq 0) { $failures += "Integration tests executed: 0" }
if ($e2e.Tests -eq 0) { $failures += "E2E tests executed: 0" }

if ($unit.PassRate -lt $threshold) { $failures += "Unit pass rate $($unit.PassRate)% < $threshold%" }
if ($integration.PassRate -lt $threshold) { $failures += "Integration pass rate $($integration.PassRate)% < $threshold%" }
if ($e2e.PassRate -lt $threshold) { $failures += "E2E pass rate $($e2e.PassRate)% < $threshold%" }

if ($runtime -eq $null) {
    $failures += "Runtime review score not found in latest agent_manager log."
} elseif ($runtime.Percent -lt $threshold) {
    $failures += "Runtime review $($runtime.Percent)% < $threshold%"
}

$routeGovernance = [pscustomobject]@{
    executed = (-not $SkipRouteGovernance)
    report_json = ""
    report_md = ""
    gate_passed = $false
    thresholds = [pscustomobject]@{
        max_added_routes = $MaxAddedRoutes
        max_removed_routes = $MaxRemovedRoutes
        max_high_churn_buckets = $MaxHighChurnBuckets
        max_duplicate_semantic_routes = $MaxDuplicateSemanticRoutes
    }
    summary = $null
}

if (-not $SkipRouteGovernance) {
    Write-Host "Generating route governance report..." -ForegroundColor Cyan
    & $pythonExe $routeGovScript
    if ($LASTEXITCODE -ne 0) {
        $failures += "Route governance report generation failed (exit $LASTEXITCODE)."
    }
    else {
        $latestGovJson = Get-ChildItem -Path (Join-Path $normalizedRoot "reports") -Filter "ROUTE_GOVERNANCE_REPORT_*.json" -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        $latestGovMd = Get-ChildItem -Path (Join-Path $normalizedRoot "reports") -Filter "ROUTE_GOVERNANCE_REPORT_*.md" -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if ($latestGovJson) { $routeGovernance.report_json = $latestGovJson.FullName }
        if ($latestGovMd) { $routeGovernance.report_md = $latestGovMd.FullName }

        if ($latestGovJson) {
            try {
                $gov = Get-Content -Path $latestGovJson.FullName -Raw | ConvertFrom-Json
                $routeGovernance.summary = [pscustomobject]@{
                    total_routes = [int]$gov.total_routes
                    added_count = [int]$gov.added_count
                    removed_count = [int]$gov.removed_count
                    high_churn_buckets = @($gov.prefix_churn | Where-Object { $_.high_churn -eq $true }).Count
                    duplicate_semantic_routes = @($gov.duplicate_semantic_routes).Count
                }
            }
            catch {
                $failures += "Unable to parse route governance report JSON: $($_.Exception.Message)"
            }
        }

        Write-Host "Validating route governance gates..." -ForegroundColor Cyan
        & $pythonExe $routeGovGateScript `
            --report "$($routeGovernance.report_json)" `
            --max-added-routes $MaxAddedRoutes `
            --max-removed-routes $MaxRemovedRoutes `
            --max-high-churn-buckets $MaxHighChurnBuckets `
            --max-duplicate-semantic-routes $MaxDuplicateSemanticRoutes

        if ($LASTEXITCODE -ne 0) {
            $failures += "Route governance gate failed."
        }
        else {
            $routeGovernance.gate_passed = $true
        }
    }
}

$summary = [pscustomobject]@{
    timestamp = $timestamp
    project_root = $normalizedRoot
    threshold_percent = $threshold
    runtime_review = [pscustomobject]@{
        percent = if ($runtime) { $runtime.Percent } else { 0.0 }
        score = if ($runtime) { $runtime.Score } else { 0 }
        max = if ($runtime) { $runtime.Max } else { 0 }
        log_path = if ($runtime) { $runtime.LogPath } else { "" }
    }
    unit = $unit
    integration = $integration
    e2e = $e2e
    route_governance = $routeGovernance
    passed = ($failures.Count -eq 0)
    failures = $failures
}

$jsonPath = Join-Path $resultsDir "full_harness_summary.json"
$mdPath = Join-Path $resultsDir "full_harness_summary.md"

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $jsonPath -Encoding UTF8

$runtimePercent = if ($runtime) { $runtime.Percent } else { 0.0 }
$runtimeScoreText = if ($runtime) { "$($runtime.Score)/$($runtime.Max)" } else { "n/a" }

$mdLines = @(
    "# Full Harness Summary"
    ""
    "- Timestamp: $timestamp"
    "- Project Root: $normalizedRoot"
    "- Threshold: $threshold%"
    ""
    "## Runtime Review"
    "- Score: $runtimeScoreText"
    "- Percent: $runtimePercent%"
    "- Log: $($summary.runtime_review.log_path)"
    ""
    "## Test Results"
    "- Unit: tests=$($unit.Tests), failures=$($unit.Failures), errors=$($unit.Errors), pass=$($unit.PassRate)%"
    "- Integration: tests=$($integration.Tests), failures=$($integration.Failures), errors=$($integration.Errors), pass=$($integration.PassRate)%"
    "- E2E: tests=$($e2e.Tests), failures=$($e2e.Failures), errors=$($e2e.Errors), pass=$($e2e.PassRate)%"
    ""
    "## Route Governance"
    "- Executed: $($routeGovernance.executed)"
    "- Gate passed: $($routeGovernance.gate_passed)"
    "- Max Added: $MaxAddedRoutes"
    "- Max Removed: $MaxRemovedRoutes"
    "- Max High-Churn Buckets: $MaxHighChurnBuckets"
    "- Max Duplicate Semantic Routes: $MaxDuplicateSemanticRoutes"
    "- Report JSON: $($routeGovernance.report_json)"
    "- Report MD: $($routeGovernance.report_md)"
    ""
    "## Status"
    "- Passed: $($summary.passed)"
)

if ($routeGovernance.summary -ne $null) {
    $mdLines += "- Total Routes: $($routeGovernance.summary.total_routes)"
    $mdLines += "- Added: $($routeGovernance.summary.added_count)"
    $mdLines += "- Removed: $($routeGovernance.summary.removed_count)"
    $mdLines += "- High-Churn Buckets: $($routeGovernance.summary.high_churn_buckets)"
    $mdLines += "- Duplicate Semantic Routes: $($routeGovernance.summary.duplicate_semantic_routes)"
}

if ($failures.Count -gt 0) {
    $mdLines += ""
    $mdLines += "## Failures"
    foreach ($failure in $failures) {
        $mdLines += "- $failure"
    }
}

$mdLines | Set-Content -Path $mdPath -Encoding UTF8

Write-Host ""
Write-Host "Harness summary JSON: $jsonPath" -ForegroundColor Cyan
Write-Host "Harness summary MD:   $mdPath" -ForegroundColor Cyan

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "Full harness failed:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "Full harness passed." -ForegroundColor Green
exit 0
