# CareerTrojan Frontend Build Script
# Builds all unified portals (Admin, User, Mentor)

$ErrorActionPreference = "Stop"
$APPS_ROOT = "C:\careertrojan\apps"
$APPS = @("admin-portal", "user-portal", "mentor-portal")

Write-Host "--- CareerTrojan Frontend Build ---" -ForegroundColor Cyan

foreach ($app in $APPS) {
    $appPath = Join-Path $APPS_ROOT $app
    Write-Host "Building $app..." -NoNewline
    
    if (-not (Test-Path $appPath)) {
        Write-Host " [FAILED] (Directory not found)" -ForegroundColor Red
        continue
    }

    Push-Location $appPath
    try {
        if (-not (Test-Path "node_modules")) {
            Write-Host " (Installing dependencies...)" -NoNewline
            npm install --quiet --no-audit --no-fund | Out-Null
        }
        
        # npm run build | Out-Null
        # Capturing output for debugging if needed, but keeping console clean
        $build = npm run build 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
        } else {
            Write-Host " [FAILED]" -ForegroundColor Red
            Write-Error $build
        }
    }
    catch {
        Write-Host " [ERROR]" -ForegroundColor Red
        Write-Error $_
    }
    finally {
        Pop-Location
    }
}

Write-Host "`nBuild Complete."
