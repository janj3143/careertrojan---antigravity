<#
.SYNOPSIS
    Fix the user-data junction mount to point to the correct source of truth.
    L:\antigravity_version_ai_data_final is the ONLY source of truth.
#>

$ErrorActionPreference = "Stop"
$mountDir = "C:\careertrojan\data-mounts"

$junctions = @(
    @{ Name = "ai-data";    Target = "L:\antigravity_version_ai_data_final" },
    @{ Name = "parser";     Target = "L:\antigravity_version_ai_data_final\automated_parser" },
    @{ Name = "user-data";  Target = "L:\antigravity_version_ai_data_final\USER DATA" }
)

Write-Host "=== Fixing Data Mount Junctions ===" -ForegroundColor Cyan
Write-Host "Source of truth: L:\antigravity_version_ai_data_final" -ForegroundColor Yellow

foreach ($j in $junctions) {
    $link = Join-Path $mountDir $j.Name
    $target = $j.Target

    # Check if target exists
    if (-not (Test-Path $target)) {
        Write-Host "  SKIP  $($j.Name) - target not found: $target" -ForegroundColor Red
        continue
    }

    # Remove existing junction if it points to wrong target
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        $currentTarget = $item.Target
        if ($currentTarget -eq $target) {
            Write-Host "  OK    $($j.Name) -> $target" -ForegroundColor Green
            continue
        }
        Write-Host "  FIX   $($j.Name) was -> $currentTarget" -ForegroundColor Yellow
        cmd /c "rmdir `"$link`"" 2>$null
        Remove-Item $link -Force -ErrorAction SilentlyContinue
    }

    # Create junction
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host "  SET   $($j.Name) -> $target" -ForegroundColor Green
}

# Verify
Write-Host "`n=== Verification ===" -ForegroundColor Cyan
foreach ($j in $junctions) {
    $link = Join-Path $mountDir $j.Name
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        Write-Host "  $($j.Name) -> $($item.Target)" -ForegroundColor Green
    }
    else {
        Write-Host "  $($j.Name) MISSING" -ForegroundColor Red
    }
}

Write-Host "`nDone." -ForegroundColor Cyan
