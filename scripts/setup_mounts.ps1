# Setup Data Mounts for CareerTrojan
$ErrorActionPreference = "Stop"

$TargetBase = "C:\careertrojan\data-mounts"
$SourceData = "L:\antigravity_version_ai_data_final"
$SourceParser = "L:\antigravity_version_ai_data_final\automated_parser"

# Ensure target directories don't exist as folders (need to be junctions)
if (Test-Path "$TargetBase\ai-data") {
    $item = Get-Item "$TargetBase\ai-data"
    if ($item.LinkType -ne "Junction") {
        Write-Host "Removing existing directory (not junction): $TargetBase\ai-data"
        Remove-Item "$TargetBase\ai-data" -Recurse -Force
    }
}
else {
    New-Item -ItemType Directory -Path $TargetBase -Force | Out-Null
}

if (Test-Path "$TargetBase\parser") {
    $item = Get-Item "$TargetBase\parser"
    if ($item.LinkType -ne "Junction") {
        Write-Host "Removing existing directory (not junction): $TargetBase\parser"
        Remove-Item "$TargetBase\parser" -Recurse -Force
    }
}

# Create Junctions
Write-Host "Creating Junction: ai-data -> $SourceData"
cmd /c mklink /J "$TargetBase\ai-data" "$SourceData"

Write-Host "Creating Junction: parser -> $SourceParser"
cmd /c mklink /J "$TargetBase\parser" "$SourceParser"

Write-Host "Mount setup complete."
