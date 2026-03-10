$ErrorActionPreference = 'Stop'

Write-Host "Stopping any older conflicting runtime containers..."
$legacy = @('careertrojan-backend','careertrojan-postgres','careertrojan-redis')
foreach ($name in $legacy) {
  docker ps --format "{{.Names}}" | Select-String "^$name$" | ForEach-Object { docker stop $name | Out-Null }
}

Write-Host "Starting careertrojan-codec stack..."
docker compose -f compose.codec.yml -p careertrojan-codec up -d --build

Write-Host "Waiting for backend health on port 8600..."
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
  try {
    $resp = Invoke-WebRequest "http://localhost:8600/health/live" -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -eq 200) { $ok = $true; break }
  } catch { }
  Start-Sleep -Seconds 2
}

if (-not $ok) {
  Write-Error "Backend did not become healthy on http://localhost:8600/health/live"
}

Write-Host "Running review pack..."
powershell -ExecutionPolicy Bypass -File scripts/review_run_1_to_4.ps1

Write-Host "Done."
