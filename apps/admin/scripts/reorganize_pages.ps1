# IntelliCV-AI Admin Portal Page Reorganization Script
# Reorganizes pages into logical administrative workflow order

Write-Host "🔄 Starting IntelliCV-AI Admin Portal Page Reorganization..." -ForegroundColor Cyan

# Define the reorganization mapping
$reorganizationMap = @{
    # DASHBOARD & OVERVIEW (01-02) - Keep Home as 00
    "03_System_Monitor.py" = "01_System_Monitor.py"
    "05_Analytics.py" = "02_Analytics.py"
    
    # USER & ACCESS MANAGEMENT (03-04)
    "01_User_Management.py" = "03_User_Management.py"
    "06_Compliance_Audit.py" = "04_Compliance_Audit.py"
    
    # DATA PROCESSING CORE (05-09)
    "21_Email_Integration.py" = "05_Email_Integration.py"
    "02_Data_Parsers.py" = "06_Data_Parsers.py"
    "20_Complete_Data_Parser.py" = "07_Complete_Data_Parser.py"
    "09_Batch_Processing.py" = "08_Batch_Processing.py"
    "04_AI_Enrichment.py" = "09_AI_Enrichment.py"
    
    # INTELLIGENCE & CONTENT (10-13)
    "17_AI_Content_Generator.py" = "10_AI_Content_Generator.py"
    "16_Market_Intelligence_Center.py" = "11_Market_Intelligence_Center.py"
    "12_Competitive_Intelligence.py" = "12_Competitive_Intelligence.py"
    "18_Web_Company_Intelligence.py" = "13_Web_Company_Intelligence.py"
    
    # SYSTEM MANAGEMENT (14-17)
    "07_API_Integration.py" = "14_API_Integration.py"
    "08_Contact_Communication.py" = "15_Contact_Communication.py"
    "11_Advanced_Settings.py" = "16_Advanced_Settings.py"
    "10_Advanced_Logging.py" = "17_Advanced_Logging.py"
    
    # BACKUP & MAINTENANCE (18-21)
    "14_System_Snapshot.py" = "18_System_Snapshot.py"
    "19_Backup_Management.py" = "19_Backup_Management.py"  # No change
    "15_Legacy_Utilities.py" = "20_Legacy_Utilities.py"
    "13_Enhanced_Glossary.py" = "21_Enhanced_Glossary.py"
}

Write-Host "📋 Reorganization Plan:" -ForegroundColor Yellow
foreach ($mapping in $reorganizationMap.GetEnumerator()) {
    Write-Host "  $($mapping.Key) → $($mapping.Value)" -ForegroundColor White
}

Write-Host "`n🚀 Executing reorganization..." -ForegroundColor Green

# Create temporary directory for staging
$tempDir = "temp_reorg_staging"
New-Item -ItemType Directory -Name $tempDir -Force | Out-Null

# First, move files to temporary staging
foreach ($mapping in $reorganizationMap.GetEnumerator()) {
    $oldName = $mapping.Key
    $newName = $mapping.Value
    
    if (Test-Path $oldName) {
        Write-Host "📄 Staging: $oldName → temp/$newName" -ForegroundColor Cyan
        Move-Item $oldName "$tempDir\$newName" -Force
    } else {
        Write-Host "⚠️  File not found: $oldName" -ForegroundColor Yellow
    }
}

# Then move from staging back to pages directory
Write-Host "`n📥 Moving files from staging..." -ForegroundColor Green
Get-ChildItem "$tempDir\*.py" | ForEach-Object {
    Write-Host "✅ Finalizing: $($_.Name)" -ForegroundColor Green
    Move-Item $_.FullName "." -Force
}

# Clean up staging directory
Remove-Item $tempDir -Recurse -Force

Write-Host "`n🎉 Page reorganization completed successfully!" -ForegroundColor Green
Write-Host "📊 New logical order implemented:" -ForegroundColor Cyan

# Show the new organization
Write-Host "`n📋 NEW LOGICAL STRUCTURE:" -ForegroundColor Yellow
Write-Host "🏠 DASHBOARD & OVERVIEW:" -ForegroundColor Magenta
Write-Host "  00_Home, 01_System_Monitor, 02_Analytics"
Write-Host "👥 USER & ACCESS MANAGEMENT:" -ForegroundColor Magenta  
Write-Host "  03_User_Management, 04_Compliance_Audit"
Write-Host "📊 DATA PROCESSING CORE:" -ForegroundColor Magenta
Write-Host "  05_Email_Integration, 06_Data_Parsers, 07_Complete_Data_Parser, 08_Batch_Processing, 09_AI_Enrichment"
Write-Host "🧠 INTELLIGENCE & CONTENT:" -ForegroundColor Magenta
Write-Host "  10_AI_Content_Generator, 11_Market_Intelligence_Center, 12_Competitive_Intelligence, 13_Web_Company_Intelligence"
Write-Host "🔧 SYSTEM MANAGEMENT:" -ForegroundColor Magenta
Write-Host "  14_API_Integration, 15_Contact_Communication, 16_Advanced_Settings, 17_Advanced_Logging"
Write-Host "💾 BACKUP & MAINTENANCE:" -ForegroundColor Magenta
Write-Host "  18_System_Snapshot, 19_Backup_Management, 20_Legacy_Utilities, 21_Enhanced_Glossary"

Write-Host "`n✅ Reorganization complete! Pages now follow logical administrative workflow." -ForegroundColor Green