$root = "C:\careertrojan"

Write-Host "=== CareerTrojan Layout Discovery ===" -ForegroundColor Cyan

# Apps
Write-Host "`n[apps/]" -ForegroundColor Yellow
Get-ChildItem -Path "$root\apps" -Directory -ErrorAction SilentlyContinue |
    ForEach-Object {
        $hasSrc = Test-Path (Join-Path $_.FullName "src")
        $icon = if ($hasSrc) { "OK" } else { "NO src/" }
        Write-Host "  $($_.Name)  [$icon]"
    }
if (-not (Test-Path "$root\apps")) { Write-Host "  (apps/ directory NOT FOUND)" -ForegroundColor Red }

# Services
Write-Host "`n[services/]" -ForegroundColor Yellow
Get-ChildItem -Path "$root\services" -Directory -ErrorAction SilentlyContinue |
    ForEach-Object {
        $hasMain = Test-Path (Join-Path $_.FullName "main.py")
        $hasInit = Test-Path (Join-Path $_.FullName "__init__.py")
        $icon = if ($hasMain) { "main.py" } elseif ($hasInit) { "__init__.py" } else { "no entry" }
        Write-Host "  $($_.Name)  [$icon]"
    }
if (-not (Test-Path "$root\services")) { Write-Host "  (services/ directory NOT FOUND)" -ForegroundColor Red }

# FastAPI entry points
Write-Host "`n[FastAPI app candidates]" -ForegroundColor Yellow
Get-ChildItem -Path $root -Recurse -Filter "main.py" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules|venv-py311|__pycache__|\.git" } |
    ForEach-Object {
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($content -match "FastAPI") {
            Write-Host "  $($_.FullName)" -ForegroundColor Green
        }
    }

# Data mounts
Write-Host "`n[data-mounts/]" -ForegroundColor Yellow
if (Test-Path "$root\data-mounts") {
    Get-ChildItem -Path "$root\data-mounts" -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host "  $($_.Name)  -> $($_.Target)" }
}
else {
    Write-Host "  (data-mounts/ directory NOT FOUND)" -ForegroundColor Red
}

# React src dirs (deep search)
Write-Host "`n[React src/ directories]" -ForegroundColor Yellow
Get-ChildItem -Path "$root\apps" -Recurse -Directory -Filter "src" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" } |
    ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor Green }

Write-Host "`n=== Done ===" -ForegroundColor Cyan
