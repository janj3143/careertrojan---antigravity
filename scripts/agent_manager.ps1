<#
.SYNOPSIS
    CareerTrojan Agent Manager — Runtime Review & Background SA Testing
.DESCRIPTION
    Two-mode orchestrator you can run while getting code improvements from Copilot:

      Mode A — REVIEW:  Validates the full runtime build (Docker, paths, imports, deps)
      Mode B — TEST:    Runs the SA testing ladder in the background:
                          Phase 1 → Unit tests
                          Phase 2 → Integration tests (unlocked when unit pass-rate ≥ 80%)
                          Phase 3 → E2E tests       (unlocked when integration pass-rate ≥ 80%)

.PARAMETER Mode
    "review"  — run runtime build review only
    "test"    — run the SA testing ladder in background
    "all"     — run review, then kick off tests in background

.PARAMETER Watch
    If set, re-runs the test ladder every N seconds (continuous SA while you code).

.EXAMPLE
    # Quick runtime review
    .\scripts\agent_manager.ps1 -Mode review

    # Start background SA testing
    .\scripts\agent_manager.ps1 -Mode test

    # Full review + continuous background testing every 60s
    .\scripts\agent_manager.ps1 -Mode all -Watch 60
#>
[CmdletBinding()]
param(
    [ValidateSet("review", "test", "all")]
    [string]$Mode = "all",

    [int]$Watch = 0,   # 0 = single-shot; >0 = re-run interval in seconds

    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

# ── Globals ──────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Continue"
$LogDir   = Join-Path $ProjectRoot "logs"
$LogFile  = Join-Path $LogDir "agent_manager_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $(switch ($Level) {
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        "PASS"  { "Green" }
        "PHASE" { "Cyan" }
        default { "White" }
    })
    Add-Content -Path $LogFile -Value $line
}

# ═══════════════════════════════════════════════════════════════════════════════
#  MODE A — RUNTIME BUILD REVIEW
# ═══════════════════════════════════════════════════════════════════════════════
function Invoke-RuntimeReview {
    Write-Log "═══════════════════════════════════════════════════" "PHASE"
    Write-Log "  MODE A — RUNTIME BUILD REVIEW" "PHASE"
    Write-Log "═══════════════════════════════════════════════════" "PHASE"

    $score = 0
    $maxScore = 0

    # ── 1. Python version ────────────────────────────────────────────────────
    $maxScore++
    Write-Log "Checking Python version..."
    try {
        $pyVer = & python --version 2>&1
        if ($pyVer -match "3\.1[1-3]") {
            Write-Log "Python: $pyVer" "PASS"
            $score++
        } else {
            Write-Log "Python version mismatch: $pyVer (need 3.11+)" "WARN"
        }
    } catch { Write-Log "Python not found on PATH" "ERROR" }

    # ── 2. Docker availability ───────────────────────────────────────────────
    $maxScore++
    Write-Log "Checking Docker..."
    try {
        $dv = & docker --version 2>&1
        Write-Log "Docker: $dv" "PASS"
        $score++
    } catch { Write-Log "Docker not available" "ERROR" }

    # ── 3. Docker Compose file ───────────────────────────────────────────────
    $maxScore++
    $composeFile = Join-Path $ProjectRoot "compose.yaml"
    if (Test-Path $composeFile) {
        Write-Log "compose.yaml present" "PASS"
        $score++
    } else { Write-Log "compose.yaml MISSING" "ERROR" }

    # ── 4. Service directories ───────────────────────────────────────────────
    $requiredDirs = @(
        "services/backend_api",
        "services/ai_engine",
        "services/workers",
        "services/shared",
        "shared_backend",
        "apps/admin",
        "apps/user",
        "apps/mentor"
    )
    foreach ($dir in $requiredDirs) {
        $maxScore++
        $full = Join-Path $ProjectRoot $dir.Replace("/", [IO.Path]::DirectorySeparatorChar)
        if (Test-Path $full) {
            Write-Log "Directory OK: $dir" "PASS"
            $score++
        } else { Write-Log "Directory MISSING: $dir" "ERROR" }
    }

    # ── 5. Critical Python imports ───────────────────────────────────────────
    $maxScore++
    Write-Log "Testing critical Python imports..."
    $importTest = @"
import sys, os
sys.path.insert(0, r'$ProjectRoot')
os.environ.setdefault('CAREERTROJAN_DB_URL', 'sqlite:///./test_agent.db')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test_agent.db')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('SECRET_KEY', 'agent-test-key')
failures = []
for mod in [
    'services.backend_api.main',
    'services.backend_api.db.models',
    'services.backend_api.utils.security',
    'services.backend_api.models.schemas',
]:
    try:
        __import__(mod)
    except Exception as e:
        failures.append(f'{mod}: {e}')
if failures:
    print('IMPORT_FAILURES:' + '|'.join(failures))
else:
    print('IMPORTS_OK')
"@
    $result = $importTest | python 2>&1
    if ($result -match "IMPORTS_OK") {
        Write-Log "All critical imports succeeded" "PASS"
        $score++
    } else {
        Write-Log "Import failures: $result" "ERROR"
    }

    # ── 6. Requirements files ────────────────────────────────────────────────
    $reqFiles = @("requirements.txt", "requirements.runtime.txt", "requirements.ai.txt", "requirements.parsers.txt")
    foreach ($rf in $reqFiles) {
        $maxScore++
        if (Test-Path (Join-Path $ProjectRoot $rf)) {
            Write-Log "Requirements file: $rf" "PASS"
            $score++
        } else { Write-Log "Requirements file MISSING: $rf" "WARN" }
    }

    # ── 7. Data mounts ──────────────────────────────────────────────────────
    $dataDirs = @("data-mounts/ai-data", "data-mounts/parser", "data-mounts/logs", "data-mounts/models")
    foreach ($dd in $dataDirs) {
        $maxScore++
        $full = Join-Path $ProjectRoot $dd.Replace("/", [IO.Path]::DirectorySeparatorChar)
        if (Test-Path $full) {
            Write-Log "Data mount: $dd" "PASS"
            $score++
        } else { Write-Log "Data mount MISSING: $dd" "WARN" }
    }

    # ── 8. Trained models ───────────────────────────────────────────────────
    $maxScore++
    $modelsDir = Join-Path $ProjectRoot "trained_models"
    $modelFiles = Get-ChildItem $modelsDir -Filter "*.json" -ErrorAction SilentlyContinue
    if ($modelFiles.Count -ge 3) {
        Write-Log "Trained models: $($modelFiles.Count) JSON files present" "PASS"
        $score++
    } else { Write-Log "Trained models: only $($modelFiles.Count) found" "WARN" }

    # ── 9. Docker Compose services parse ─────────────────────────────────────
    $maxScore++
    try {
        $services = & docker compose -f $composeFile config --services 2>&1
        if ($LASTEXITCODE -eq 0) {
            $svcList = ($services -split "`n").Count
            Write-Log "Docker Compose: $svcList services defined" "PASS"
            $score++
        } else {
            Write-Log "Docker Compose config parse failed" "WARN"
        }
    } catch { Write-Log "Docker Compose not available for validation" "WARN" }

    # ── 10. Test infrastructure ──────────────────────────────────────────────
    $maxScore++
    $pytestIni = Join-Path $ProjectRoot "pytest.ini"
    $conftest  = Join-Path $ProjectRoot "tests" "conftest.py"
    if ((Test-Path $pytestIni) -and (Test-Path $conftest)) {
        Write-Log "Test infrastructure (pytest.ini + conftest.py) present" "PASS"
        $score++
    } else { Write-Log "Test infrastructure incomplete" "WARN" }

    # ── Summary ──────────────────────────────────────────────────────────────
    $pct = [math]::Round(($score / $maxScore) * 100, 1)
    Write-Log "" "INFO"
    Write-Log "═══════════════════════════════════════════════════" "PHASE"
    Write-Log "  RUNTIME REVIEW SCORE: $score / $maxScore ($pct%)" $(if ($pct -ge 80) { "PASS" } else { "WARN" })
    Write-Log "═══════════════════════════════════════════════════" "PHASE"

    return @{ Score = $score; Max = $maxScore; Percent = $pct }
}


# ═══════════════════════════════════════════════════════════════════════════════
#  MODE B — SA TESTING LADDER  (Unit → Integration → E2E)
# ═══════════════════════════════════════════════════════════════════════════════
function Get-TestPassRate {
    param([string]$JunitXml)
    if (-not (Test-Path $JunitXml)) { return 0 }
    [xml]$doc = Get-Content $JunitXml
    $tests  = [int]$doc.testsuites.testsuite.tests
    $fails  = [int]$doc.testsuites.testsuite.failures
    $errors = [int]$doc.testsuites.testsuite.errors
    if ($tests -eq 0) { return 0 }
    return [math]::Round((($tests - $fails - $errors) / $tests) * 100, 1)
}

function Invoke-TestLadder {
    Write-Log "" "INFO"
    Write-Log "═══════════════════════════════════════════════════" "PHASE"
    Write-Log "  MODE B — SA TESTING LADDER" "PHASE"
    Write-Log "═══════════════════════════════════════════════════" "PHASE"

    $resultsDir = Join-Path $ProjectRoot "logs" "test_results"
    if (-not (Test-Path $resultsDir)) { New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null }

    $PassThreshold = 80.0

    # ── Phase 1: Unit Tests ──────────────────────────────────────────────────
    Write-Log "─── PHASE 1: UNIT TESTS ───" "PHASE"
    $unitXml = Join-Path $resultsDir "unit_results.xml"
    $unitLog = Join-Path $resultsDir "unit_output.txt"

    Push-Location $ProjectRoot
    & python -m pytest tests/unit/ -m unit `
        --tb=short -q `
        --junitxml="$unitXml" `
        2>&1 | Tee-Object -FilePath $unitLog
    Pop-Location

    $unitRate = Get-TestPassRate $unitXml
    Write-Log "Unit test pass rate: $unitRate%" $(if ($unitRate -ge $PassThreshold) { "PASS" } else { "WARN" })

    if ($unitRate -lt $PassThreshold) {
        Write-Log "Unit pass rate below ${PassThreshold}% — Integration tests LOCKED" "WARN"
        Write-Log "Fix failing unit tests, then re-run agent_manager." "INFO"
        return @{ Unit = $unitRate; Integration = 0; E2E = 0; Phase = "Unit" }
    }

    # ── Phase 2: Integration Tests ───────────────────────────────────────────
    Write-Log "─── PHASE 2: INTEGRATION TESTS (unlocked) ───" "PHASE"
    $intXml = Join-Path $resultsDir "integration_results.xml"
    $intLog = Join-Path $resultsDir "integration_output.txt"

    Push-Location $ProjectRoot
    & python -m pytest tests/integration/ -m integration `
        --tb=short -q `
        --junitxml="$intXml" `
        2>&1 | Tee-Object -FilePath $intLog
    Pop-Location

    $intRate = Get-TestPassRate $intXml
    Write-Log "Integration test pass rate: $intRate%" $(if ($intRate -ge $PassThreshold) { "PASS" } else { "WARN" })

    if ($intRate -lt $PassThreshold) {
        Write-Log "Integration pass rate below ${PassThreshold}% — E2E tests LOCKED" "WARN"
        return @{ Unit = $unitRate; Integration = $intRate; E2E = 0; Phase = "Integration" }
    }

    # ── Phase 3: E2E Tests ───────────────────────────────────────────────────
    Write-Log "─── PHASE 3: E2E TESTS (unlocked) ───" "PHASE"
    $e2eXml = Join-Path $resultsDir "e2e_results.xml"
    $e2eLog = Join-Path $resultsDir "e2e_output.txt"

    Push-Location $ProjectRoot
    & python -m pytest tests/e2e/ -m e2e `
        --tb=short -q `
        --junitxml="$e2eXml" `
        2>&1 | Tee-Object -FilePath $e2eLog
    Pop-Location

    $e2eRate = Get-TestPassRate $e2eXml
    Write-Log "E2E test pass rate: $e2eRate%" $(if ($e2eRate -ge $PassThreshold) { "PASS" } else { "WARN" })

    return @{ Unit = $unitRate; Integration = $intRate; E2E = $e2eRate; Phase = "E2E" }
}


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════
Write-Log "╔═══════════════════════════════════════════════════════════╗" "PHASE"
Write-Log "║   CareerTrojan Agent Manager — $(Get-Date -Format 'yyyy-MM-dd HH:mm')          ║" "PHASE"
Write-Log "║   Mode: $Mode   Watch: $(if($Watch -gt 0){"${Watch}s"}else{'off'})                                     ║" "PHASE"
Write-Log "╚═══════════════════════════════════════════════════════════╝" "PHASE"

do {
    # ── Mode A: Review ───────────────────────────────────────────────────────
    if ($Mode -in @("review", "all")) {
        $reviewResult = Invoke-RuntimeReview
    }

    # ── Mode B: Test ─────────────────────────────────────────────────────────
    if ($Mode -in @("test", "all")) {
        $testResult = Invoke-TestLadder
    }

    # ── Summary ──────────────────────────────────────────────────────────────
    Write-Log "" "INFO"
    Write-Log "╔═══════════════════════════════════════════════════════════╗" "PHASE"
    Write-Log "║   AGENT MANAGER SUMMARY                                  ║" "PHASE"
    if ($reviewResult) {
        Write-Log "║   Runtime Score : $($reviewResult.Score)/$($reviewResult.Max) ($($reviewResult.Percent)%)" "INFO"
    }
    if ($testResult) {
        Write-Log "║   Unit Tests    : $($testResult.Unit)% pass rate" "INFO"
        Write-Log "║   Integration   : $($testResult.Integration)% pass rate" "INFO"
        Write-Log "║   E2E Tests     : $($testResult.E2E)% pass rate" "INFO"
        Write-Log "║   Current Phase : $($testResult.Phase)" "INFO"
    }
    Write-Log "║   Log File      : $LogFile" "INFO"
    Write-Log "╚═══════════════════════════════════════════════════════════╝" "PHASE"

    if ($Watch -gt 0) {
        Write-Log "Sleeping ${Watch}s before next cycle... (Ctrl+C to stop)" "INFO"
        Start-Sleep -Seconds $Watch
    }
} while ($Watch -gt 0)

Write-Log "Agent Manager complete." "INFO"
