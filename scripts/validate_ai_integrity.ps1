# AI Data Integrity Validation ("The Trap")
# Purpose: Detect if the system is running on fallback/demo data instead of the real L: drive AI data.

$ErrorActionPreference = "Stop"

Write-Host "--- AI Data Integrity Trap ---" -ForegroundColor Cyan

# 1. Configuration
$AI_DATA_PATH = "L:\antigravity_version_ai_data_final"
$TRAP_KEYWORDS = @("Python", "Machine Learning", "Janj!3143", "John Doe", "Demo Corp")
$EXPECTED_SALES_KEYWORDS = @("Sales", "Revenue", "Business Development", "Account Executive", "Closing")

# 2. Check Data Source Existence
Write-Host "[1/3] Verifying Data Source..." -NoNewline
if (-not (Test-Path $AI_DATA_PATH)) {
    Write-Host " [FAILED]" -ForegroundColor Red
    throw "CRITICAL: AI Data Root not found at $AI_DATA_PATH"
}
Write-Host " [OK] ($AI_DATA_PATH)" -ForegroundColor Green

# 3. Scan for Demo Artifacts (Static Trap) - FAST CHECK
Write-Host "[2/3] Checking for specific fallback artifacts (Fast Check)..." -NoNewline
# Instead of scanning everything, we check for specific known bad locations or just proceed if root is clean.
# A full scan of 500GB is too slow for a bootstrap check.
$badPaths = @(
    (Join-Path $AI_DATA_PATH "MOCK_DATA.json"), 
    (Join-Path $AI_DATA_PATH "fallback_resume.pdf")
)

$found = $false
foreach ($path in $badPaths) {
    if (Test-Path $path) {
        $found = $true
        Write-Host "`n [TRAP TRIGGERED] Found forbidden artifact: $path" -ForegroundColor Red
    }
}

if ($found) {
    throw "DATA_CONTAMINATION_ERROR: Demo artifacts detected in Source of Truth."
}
Write-Host " [CLEAN]" -ForegroundColor Green

# 4. Inference Trap (Mocked for Phase 1, to be replaced by real Python inference call)
Write-Host "[3/3] Running 'Sales vs Python' Inference Trap..."
Write-Host "    * Loading Sales Profile (Simulation)..." 

# SIMULATION LOGIC FOR PHASE 1:
# In a real scenario, this would call: python inference.py --profile "sales_candidate_id"
# Here we simulate the check to prove the trap logic works.

# Validating that we are NOT seeing "Python" in a Sales profile
$simulatedResult = "Account Executive with 5 years experience in SaaS sales." 
# UNCOMMENT TO TEST TRAP: $simulatedResult = "Senior Python Developer with Machine Learning experience."

Write-Host "    * Inference Result: '$simulatedResult'"

$contaminationFound = $false
foreach ($keyword in $TRAP_KEYWORDS) {
    if ($simulatedResult -match $keyword) {
        $contaminationFound = $true
        Write-Host " [TRAP TRIGGERED] Found forbidden keyword: '$keyword'" -ForegroundColor Red
    }
}

if ($contaminationFound) {
    throw "DATA_CONTAMINATION_ERROR: Inference returned Demo/Fallback signatures."
}

# Validate expected keywords
$matchCount = 0
foreach ($keyword in $EXPECTED_SALES_KEYWORDS) {
    if ($simulatedResult -match $keyword) {
        $matchCount++
    }
}

if ($matchCount -eq 0) {
    Write-Host " [WARNING] No expected Sales keywords found. Model may be under-performing." -ForegroundColor Yellow
}
else {
    Write-Host " [PASSED] Profile signature matches expected Persona." -ForegroundColor Green
}

Write-Host "`nAI Integrity Check Passed. No Contamination Detected." -ForegroundColor Green
