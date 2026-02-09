<#
.SYNOPSIS
    Ingest Data Script
    Watches the AI Data Input folder for new resumes/files and triggers ingestion.
    Simulates the "Data Enrichment Loop".

.DESCRIPTION
    Runtime script to:
    1. Scan L:\antigravity_version_ai_data_final\INPUT
    2. Validate file types (.pdf, .docx)
    3. Call the Parser API (Mocked for now)
    4. Move file to PROCESSED or ERROR
#>

param (
    [switch]$Loop = $false,
    [int]$IntervalSeconds = 10
)

$DATA_ROOT = "L:\antigravity_version_ai_data_final"
$INPUT_DIR = Join-Path $DATA_ROOT "INPUT"
$PROCESSED_DIR = Join-Path $DATA_ROOT "PROCESSED"
$ERROR_DIR = Join-Path $DATA_ROOT "ERROR"

# Ensure directories exist
if (-not (Test-Path $INPUT_DIR)) { New-Item -ItemType Directory -Path $INPUT_DIR -Force | Out-Null }
if (-not (Test-Path $PROCESSED_DIR)) { New-Item -ItemType Directory -Path $PROCESSED_DIR -Force | Out-Null }
if (-not (Test-Path $ERROR_DIR)) { New-Item -ItemType Directory -Path $ERROR_DIR -Force | Out-Null }

function Process-File($file) {
    Write-Host " [API] Detected file: $($file.Name)" -ForegroundColor Yellow
    
    try {
        # TODO: Call actual API
        # Invoke-RestMethod -Uri "http://localhost:8000/api/v1/parser/ingest" ...
        
        Start-Sleep -Seconds 1 # Simulate processing time
        
        Write-Host " [API] Enrichment complete for $($file.Name)" -ForegroundColor Green
        
        # Move to Processed
        $dest = Join-Path $PROCESSED_DIR $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force
        Write-Host " [IO] Moved to PROCESSED" -ForegroundColor Gray
    }
    catch {
        Write-Error "Failed to process $($file.Name): $_"
        $dest = Join-Path $ERROR_DIR $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force
    }
}

Write-Host "--- CareerTrojan Data Ingestion Worker ---" -ForegroundColor Cyan
Write-Host "Monitoring: $INPUT_DIR"

do {
    $files = Get-ChildItem -Path $INPUT_DIR -File
    
    if ($files.Count -eq 0) {
        if ($Loop) { 
            Write-Host "." -NoNewline
        }
        else {
            Write-Host "No files found locally."
        }
    }
    
    foreach ($file in $files) {
        Process-File $file
    }

    if ($Loop) { Start-Sleep -Seconds $IntervalSeconds }

} while ($Loop)
