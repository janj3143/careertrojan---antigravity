# SANDBOX Admin Portal Launcher
# This script ALWAYS runs from the correct SANDBOX\admin_portal directory
# Created to fix directory confusion issues

Write-Host "Starting IntelliCV Admin Portal from SANDBOX directory..." -ForegroundColor Green

# Force change to the correct directory
$TargetDirectory = "C:\IntelliCV-AI\IntelliCV\SANDBOX\admin_portal"
Set-Location -Path $TargetDirectory

# Verify we're in the right place
$CurrentLocation = Get-Location
Write-Host "Current Directory: $CurrentLocation" -ForegroundColor Yellow

# Check if main.py exists (Best-of-Breed unified version)
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found in current directory!" -ForegroundColor Red
    Write-Host "Expected location: $TargetDirectory\main.py" -ForegroundColor Red
    exit 1
}

Write-Host "Found main.py - launching Best-of-Breed Admin Portal..." -ForegroundColor Green

# Kill any existing Python processes
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
taskkill /F /IM python.exe 2>$null
taskkill /F /IM streamlit.exe 2>$null

# Start Streamlit from the correct SANDBOX directory with the correct Python
Write-Host "Starting Best-of-Breed Admin Portal on port 8507..." -ForegroundColor Cyan
& "C:\IntelliCV-AI\IntelliCV\env310\python.exe" -m streamlit run main.py --server.port 8507 --server.address localhost --server.headless false

Write-Host "Admin Portal launch completed." -ForegroundColor Green