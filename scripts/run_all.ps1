<#
.SYNOPSIS
    One-command launcher for J-drive CareerTrojan runtime setup + validation.

.DESCRIPTION
    Runs a practical end-to-end sequence:
    1) Optional runtime setup
    2) Bootstrap
    3) Full harness (runtime review + unit + integration + E2E)
    4) Optional runtime start in a new PowerShell window

    Produces:
    - Full transcript log
    - JSON summary with per-step status

.EXAMPLE
    .\scripts\run_all.ps1

.EXAMPLE
    .\scripts\run_all.ps1 -WithSetup -WithDocker

.EXAMPLE
    .\scripts\run_all.ps1 -Require100 -StartRuntimeWindow
#>

[CmdletBinding()]
param(
    [switch]$WithSetup,
    [switch]$WithDocker,
    [switch]$StartRuntimeWindow,
    [switch]$Require100,
    [double]$MinPassRate = 80.0
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $ProjectRoot.StartsWith("J:\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "run_all.ps1 is restricted to J-drive runtime. Current root: $ProjectRoot"
}

$RunLogsDir = Join-Path $ProjectRoot "logs\run_all"
if (-not (Test-Path $RunLogsDir)) {
    New-Item -Path $RunLogsDir -ItemType Directory -Force | Out-Null
}

$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$TranscriptPath = Join-Path $RunLogsDir "run_all_$RunId.log"
$RunSummaryPath = Join-Path $RunLogsDir "run_all_summary_$RunId.json"

$script:StepResults = New-Object System.Collections.Generic.List[object]

function Add-StepResult {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Details = ""
    )
    $script:StepResults.Add([pscustomobject]@{
        name = $Name
        status = $Status
        details = $Details
        timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    })
}

function Set-LatestStepStatus {
    param(
        [string]$Status,
        [string]$Details = ""
    )
    if ($script:StepResults.Count -gt 0) {
        $idx = $script:StepResults.Count - 1
        $script:StepResults[$idx].status = $Status
        if ($Details) {
            $script:StepResults[$idx].details = $Details
        }
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==== $Name ====" -ForegroundColor Cyan
    Add-StepResult -Name $Name -Status "in_progress"

    try {
        & $Action
        Set-LatestStepStatus -Status "passed"
        Write-Host "[PASS] $Name" -ForegroundColor Green
    }
    catch {
        $msg = $_.Exception.Message
        Set-LatestStepStatus -Status "failed" -Details $msg
        Write-Host "[FAIL] $Name : $msg" -ForegroundColor Red
        throw
    }
}

$runPassed = $false
$failedStep = ""

Start-Transcript -Path $TranscriptPath -Force | Out-Null
try {
    Write-Host "CareerTrojan Run-All started" -ForegroundColor Green
    Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
    Write-Host "Run ID: $RunId" -ForegroundColor Yellow

    Invoke-Step -Name "Preflight" -Action {
        $requiredScripts = @(
            "scripts\bootstrap.ps1",
            "scripts\full_harness.ps1",
            "scripts\Start-And-Map.ps1"
        )
        foreach ($rel in $requiredScripts) {
            $full = Join-Path $ProjectRoot $rel
            if (-not (Test-Path $full)) {
                throw "Missing required script: $rel"
            }
        }
    }

    if ($WithSetup) {
        Invoke-Step -Name "Runtime setup" -Action {
            $setupScript = Join-Path $ProjectRoot "scripts\setup_j_runtime.ps1"
            & $setupScript -FullDeps -InstallPytest
            if ($LASTEXITCODE -ne 0) {
                throw "setup_j_runtime.ps1 failed with exit code $LASTEXITCODE"
            }
        }
    }
    else {
        Add-StepResult -Name "Runtime setup" -Status "skipped" -Details "Skipped (use -WithSetup to run)."
    }

    Invoke-Step -Name "Bootstrap" -Action {
        $bootstrapScript = Join-Path $ProjectRoot "scripts\bootstrap.ps1"
        if ($WithDocker) {
            & $bootstrapScript -StartDocker
        }
        else {
            & $bootstrapScript
        }
        if (-not $?) {
            throw "bootstrap.ps1 reported failure."
        }
    }

    Invoke-Step -Name "Full harness" -Action {
        $harnessScript = Join-Path $ProjectRoot "scripts\full_harness.ps1"
        if ($Require100) {
            & $harnessScript -Require100
        }
        else {
            & $harnessScript -MinPassRate $MinPassRate
        }
        if (-not $?) {
            throw "full_harness.ps1 reported failure."
        }
    }

    if ($StartRuntimeWindow) {
        Invoke-Step -Name "Start runtime window" -Action {
            $startScript = Join-Path $ProjectRoot "scripts\Start-And-Map.ps1"
            Start-Process powershell -ArgumentList @(
                "-NoExit",
                "-ExecutionPolicy", "Bypass",
                "-File", $startScript
            ) -WorkingDirectory $ProjectRoot | Out-Null
        }
    }
    else {
        Add-StepResult -Name "Start runtime window" -Status "skipped" -Details "Skipped (use -StartRuntimeWindow to launch runtime)."
    }

    $runPassed = $true
}
catch {
    $failed = $script:StepResults | Where-Object { $_.status -eq "failed" } | Select-Object -Last 1
    if ($failed) {
        $failedStep = $failed.name
    }
    $runPassed = $false
}
finally {
    Stop-Transcript | Out-Null
}

$harnessJson = Join-Path $ProjectRoot "logs\test_results\full_harness_summary.json"
$harnessMd = Join-Path $ProjectRoot "logs\test_results\full_harness_summary.md"

$summary = [pscustomobject]@{
    run_id = $RunId
    timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    project_root = $ProjectRoot
    passed = $runPassed
    failed_step = $failedStep
    transcript_log = $TranscriptPath
    harness_summary_json = if (Test-Path $harnessJson) { $harnessJson } else { "" }
    harness_summary_md = if (Test-Path $harnessMd) { $harnessMd } else { "" }
    steps = $script:StepResults
}

$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $RunSummaryPath -Encoding UTF8

Write-Host ""
Write-Host "Run summary: $RunSummaryPath" -ForegroundColor Cyan
Write-Host "Transcript:  $TranscriptPath" -ForegroundColor Cyan
if (Test-Path $harnessMd) {
    Write-Host "Harness MD:  $harnessMd" -ForegroundColor Cyan
}

if (-not $runPassed) {
    Write-Host ""
    Write-Host "Run-all failed. Share these files for full error context:" -ForegroundColor Red
    Write-Host " 1) $RunSummaryPath" -ForegroundColor Red
    Write-Host " 2) $TranscriptPath" -ForegroundColor Red
    if (Test-Path $harnessMd) {
        Write-Host " 3) $harnessMd" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "Run-all completed successfully." -ForegroundColor Green
exit 0
