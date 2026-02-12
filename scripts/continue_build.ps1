<#
.SYNOPSIS
    CareerTrojan Phase 4 - Continue Build
    Runs endpoint introspection, React callsite migration, and full validation.
#>
param(
    [switch]$DryRun,
    [string]$PythonExe = "C:\careertrojan\infra\venv-py311\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$root = "C:\careertrojan"
$reports = Join-Path $root "reports"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " CareerTrojan - Phase 4 Continue Build"  -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python not found at $PythonExe. Aborting."
    exit 1
}

if (-not (Test-Path "L:\antigravity_version_ai_data_final")) {
    Write-Error "Data drive L:\antigravity_version_ai_data_final not found. Aborting."
    exit 1
}

New-Item -ItemType Directory -Force -Path $reports | Out-Null

# --- 4a: Endpoint Introspection Pipeline ---
Write-Host ""
Write-Host "[4a] Running Endpoint Introspection Pipeline..." -ForegroundColor Yellow

$introArgs = @(
    (Join-Path $root "scripts\run_introspection.py"),
    "--output",
    (Join-Path $reports "endpoint_map.json")
)
if ($DryRun) {
    $introArgs += "--dry-run"
}

& $PythonExe @introArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Introspection pipeline failed."
    exit 1
}
Write-Host "[4a] Done - Endpoint map generated." -ForegroundColor Green

# --- 4b: React Callsite Migration ---
Write-Host ""
Write-Host "[4b] Running React API Prefix Migration..." -ForegroundColor Yellow

$migrateArgs = @(
    (Join-Path $root "scripts\migrate_react_api_prefixes.py")
)
if ($DryRun) {
    $migrateArgs += "--check"
}

& $PythonExe @migrateArgs
$migrateExit = $LASTEXITCODE

if ($DryRun) {
    Write-Host "[4b] Dry-run complete. Re-run without -DryRun to apply." -ForegroundColor Cyan
}
elseif ($migrateExit -ne 0) {
    Write-Error "Callsite migration failed."
    exit 1
}
else {
    Write-Host "[4b] React callsites migrated." -ForegroundColor Green
}

# --- 4c: Full Validation Deep-Dive ---
Write-Host ""
Write-Host "[4c] Running Validation Deep-Dive..." -ForegroundColor Yellow

# 4c-i: Zero Intellicv-AI check (FAST - only scan apps/, services/, shared/, scripts/)
Write-Host "  Checking for legacy branding..." -NoNewline
$scanDirs = @("apps", "services", "shared", "scripts", "config")
$legacyHits = @()
foreach ($sd in $scanDirs) {
    $scanPath = Join-Path $root $sd
    if (Test-Path $scanPath) {
        $hits = Get-ChildItem -Path $scanPath -Recurse -Include *.py,*.ts,*.tsx,*.json,*.md -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "node_modules|__pycache__|\.git|dist|build" } |
            Select-String -Pattern "Intellicv-AI" -SimpleMatch
        if ($null -ne $hits) {
            $legacyHits += $hits
        }
    }
}

if ($legacyHits.Count -gt 0) {
    Write-Host " FAIL ($($legacyHits.Count) hits)" -ForegroundColor Red
    foreach ($hit in $legacyHits) {
        Write-Host "    $hit" -ForegroundColor DarkRed
    }
}
else {
    Write-Host " Zero instances." -ForegroundColor Green
}

# 4c-ii: Data mount junction health
Write-Host "  Checking data-mount junctions..." -NoNewline
$junctionOk = $true
$jNames = @("ai-data", "parser", "user-data")
foreach ($jn in $jNames) {
    $link = Join-Path $root "data-mounts\$jn"
    if (-not (Test-Path $link)) {
        Write-Host ""
        Write-Host "    MISSING: $link" -ForegroundColor Red
        $junctionOk = $false
    }
}
if ($junctionOk) {
    Write-Host " All junctions present." -ForegroundColor Green
}

# 4c-iii: L: to E: sync trap
Write-Host "  Running sync trap (L: to E:)..." -NoNewline
if (-not $DryRun) {
    $ts = Get-Date -Format "yyyyMMddHHmmss"
    $trapDir = "L:\antigravity_version_ai_data_final\USER DATA\test"
    $trapFile = Join-Path $trapDir "_sync_trap_$ts.txt"
    $mirrorDir = "E:\CareerTrojan\USER_DATA_COPY\test"
    $trapContent = "sync-trap-$(Get-Random)"

    New-Item -ItemType Directory -Force -Path $trapDir | Out-Null
    Set-Content -Path $trapFile -Value $trapContent
    Start-Sleep -Seconds 5

    $mirrorFile = Join-Path $mirrorDir "_sync_trap_$ts.txt"
    if ((Test-Path $mirrorFile) -and ((Get-Content $mirrorFile) -eq $trapContent)) {
        Write-Host " Sync verified." -ForegroundColor Green
    }
    else {
        Write-Host " Mirror not found or mismatch." -ForegroundColor Yellow
    }
    Remove-Item $trapFile -ErrorAction SilentlyContinue
    Remove-Item $mirrorFile -ErrorAction SilentlyContinue
}
else {
    Write-Host " SKIPPED (dry-run)." -ForegroundColor Cyan
}

# 4c-iv: Contamination trap
Write-Host "  Running contamination trap..." -NoNewline
if (-not $DryRun) {
    $trapArgs = @(
        (Join-Path $root "scripts\run_introspection.py"),
        "--contamination-check"
    )
    & $PythonExe @trapArgs 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " Clean - no contamination." -ForegroundColor Green
    }
    else {
        Write-Host " DATA_CONTAMINATION_ERROR - HALT" -ForegroundColor Red
        exit 99
    }
}
else {
    Write-Host " SKIPPED (dry-run)." -ForegroundColor Cyan
}

# --- Summary ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Phase 4 Continue Build - Complete"      -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next: pytest tests/ -v"
