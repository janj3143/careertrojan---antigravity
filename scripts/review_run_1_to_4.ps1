$ErrorActionPreference = 'Stop'

Write-Host "=== CareerTrojan Code Review Pack (1-4) ==="
Write-Host "[1/4] API Matrix"
python scripts/review_api_matrix.py --base-url http://localhost:8600 --out reports/review_api_matrix.json

Write-Host "[2/4] New Elements Validation"
python scripts/review_new_elements.py --base-url http://localhost:8600 --out reports/review_new_elements.json

Write-Host "[3/4] Golden Path E2E"
python scripts/e2e_golden_path.py --port 8600

Write-Host "[4/4] Braintree E2E"
python scripts/e2e_braintree_test.py

Write-Host "=== Review Pack Completed ==="
