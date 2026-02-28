# CareerTrojan Frontend Build Script
# Builds all unified portals (Admin, User, Mentor)

$ErrorActionPreference = "Stop"
$APP_ROOT = Resolve-Path (Join-Path $PSScriptRoot "..")
$APPS_ROOT = Join-Path $APP_ROOT "apps"
$APPS = @("admin", "user", "mentor")

function Resolve-Npm {
    $candidates = @(
        "J:\nodej\npm.cmd",
        "J:\nodej\npm"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $cmd = Get-Command npm -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$NPM = Resolve-Npm
if (-not $NPM) {
    throw "npm not found. Install Node on J: (J:\nodej) or add npm to PATH."
}

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
        if (-not (Test-Path "package.json")) {
            Write-Host " [SKIP] (No package.json)" -ForegroundColor Yellow
            continue
        }

        if (-not (Test-Path "node_modules")) {
            Write-Host " (Installing dependencies...)" -NoNewline
            & $NPM install --quiet --no-audit --no-fund | Out-Null
        }
        
        $build = & $NPM run build 2>&1
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
