# Setup Data Mounts for CareerTrojan
$ErrorActionPreference = "Stop"

$AppRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TargetBase = Join-Path $AppRoot "data-mounts"
$SourceRoot = if ($env:CAREERTROJAN_DATA_ROOT) { $env:CAREERTROJAN_DATA_ROOT } else { "L:\Codec-Antigravity Data set" }
$SourceData = $SourceRoot
$SourceParser = Join-Path $SourceRoot "automated_parser"
$SourceUserData = Join-Path $SourceRoot "USER DATA"

function Ensure-Link {
    param(
        [string]$LinkPath,
        [string]$TargetPath
    )

    if (-not (Test-Path $TargetPath)) {
        throw "Source target not found: $TargetPath"
    }

    if (Test-Path $LinkPath) {
        $item = Get-Item $LinkPath
        if ($item.LinkType -eq "Junction" -or $item.LinkType -eq "SymbolicLink") {
            Write-Host "Link already exists: $LinkPath -> $($item.Target)"
            return
        }
        Write-Host "Removing existing non-link directory: $LinkPath"
        Remove-Item $LinkPath -Recurse -Force
    }

    Write-Host "Creating Junction: $LinkPath -> $TargetPath"
    cmd /c mklink /J "$LinkPath" "$TargetPath" | Out-Null
}

if (-not (Test-Path $TargetBase)) {
    New-Item -ItemType Directory -Path $TargetBase -Force | Out-Null
}

Ensure-Link -LinkPath (Join-Path $TargetBase "ai-data") -TargetPath $SourceData
Ensure-Link -LinkPath (Join-Path $TargetBase "parser") -TargetPath $SourceParser
Ensure-Link -LinkPath (Join-Path $TargetBase "user-data") -TargetPath $SourceUserData

Write-Host "Mount setup complete."
