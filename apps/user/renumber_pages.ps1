# IntelliCV Pages Renumbering Script
# This script will renumber all pages in sequential order

$pagesPath = "c:\IntelliCV-AI\IntelliCV\SANDBOX\user_portal_final\pages"
Set-Location $pagesPath

Write-Host "🔄 Starting IntelliCV Pages Renumbering..." -ForegroundColor Cyan

# Define the new page order with their current names
$pageMapping = @(
    @{Current="01_Home.py"; New="01_Home.py"; Keep=$true},
    @{Current="02_Welcome_Page.py"; New="02_Welcome_Page.py"; Keep=$true},
    @{Current="03_Registration.py"; New="03_Registration.py"; Keep=$true},
    @{Current="04_Dashboard.py"; New="04_Dashboard.py"; Keep=$true},
    @{Current="05_Payment.py"; New="05_Payment.py"; Keep=$true},
    @{Current="06_Pricing.py"; New="06_Pricing.py"; Keep=$true},
    @{Current="07_Account_Verification.py"; New="07_Account_Verification.py"; Keep=$true},
    @{Current="08_Profile_Complete.py"; New="08_Profile_Complete.py"; Keep=$true},
    @{Current="09_Resume_Upload_Career_Intelligence_Express.py"; New="09_Resume_Upload_Career_Intelligence_Express.py"; Keep=$true},
    @{Current="10_Your_Current_Resume.py"; New="10_Your_Current_Resume.py"; Keep=$true},
    @{Current="11_Career_Intelligence_Suite.py"; New="11_Career_Intelligence_Suite.py"; Keep=$true},
    @{Current="temp_Application_Tracker.py"; New="12_Application_Tracker.py"; Keep=$true},
    @{Current="12_Job_Title_Word_Cloud.py"; New="13_Job_Title_Word_Cloud.py"; Keep=$true},
    @{Current="15_Current_Resume_Management.py"; New="14_Current_Resume_Management.py"; Keep=$true},
    @{Current="15_Resume_Upload_Enhanced.py"; New="15_Resume_Upload_Enhanced.py"; Keep=$true},
    @{Current="16_Job_Match.py"; New="16_Job_Match.py"; Keep=$true},
    @{Current="17_Resume_Tuner.py"; New="17_Resume_Tuner.py"; Keep=$true},
    @{Current="18_Resume_Diff.py"; New="18_Resume_Diff.py"; Keep=$true},
    @{Current="19_Resume_Feedback.py"; New="19_Resume_Feedback.py"; Keep=$true},
    @{Current="20_Job_Opportunities.py"; New="20_Job_Opportunities.py"; Keep=$true},
    @{Current="21_Job_Description_Upload.py"; New="21_Job_Description_Upload.py"; Keep=$true},
    @{Current="22_JD_Upload.py"; New="22_JD_Upload.py"; Keep=$true},
    @{Current="23_Profile_Chat_Agent.py"; New="23_Profile_Chat_Agent.py"; Keep=$true},
    @{Current="24_Resume_Job_Description_Fit.py"; New="24_Resume_Job_Description_Fit.py"; Keep=$true},
    @{Current="25_Tailored_CV_Generator.py"; New="25_Tailored_CV_Generator.py"; Keep=$true},
    @{Current="28_Job_Match_Enhanced_AI.py"; New="26_Job_Match_Enhanced_AI.py"; Keep=$true},
    @{Current="29_Job_Match_INTEGRATED.py"; New="27_Job_Match_INTEGRATED.py"; Keep=$true},
    @{Current="30_AI_Interview_Coach.py"; New="28_AI_Interview_Coach.py"; Keep=$true},
    @{Current="31_AI_Interview_Coach_INTEGRATED.py"; New="29_AI_Interview_Coach_INTEGRATED.py"; Keep=$true},
    @{Current="32_Career_Intelligence.py"; New="30_Career_Intelligence.py"; Keep=$true},
    @{Current="33_Career_Intelligence_INTEGRATED.py"; New="31_Career_Intelligence_INTEGRATED.py"; Keep=$true},
    @{Current="34_AI_Insights.py"; New="32_AI_Insights.py"; Keep=$true},
    @{Current="35_Interview_Coach.py"; New="33_Interview_Coach.py"; Keep=$true},
    @{Current="36_Career_Intelligence_Advanced.py"; New="34_Career_Intelligence_Advanced.py"; Keep=$true},
    @{Current="37_AI_Enrichment.py"; New="35_AI_Enrichment.py"; Keep=$true},
    @{Current="38_Geo_Career_Finder.py"; New="36_Geo_Career_Finder.py"; Keep=$true},
    @{Current="39_Job_Title_Intelligence.py"; New="37_Job_Title_Intelligence.py"; Keep=$true},
    @{Current="40_Geographic_Career_Intelligence.py"; New="38_Geographic_Career_Intelligence.py"; Keep=$true},
    @{Current="41_Advanced_Career_Tools.py"; New="39_Advanced_Career_Tools.py"; Keep=$true},
    @{Current="42_AI_Career_Intelligence.py"; New="40_AI_Career_Intelligence.py"; Keep=$true},
    @{Current="43_AI_Career_Intelligence_Enhanced.py"; New="41_AI_Career_Intelligence_Enhanced.py"; Keep=$true},
    @{Current="44_Mentorship_Hub.py"; New="42_Mentorship_Hub.py"; Keep=$true},
    @{Current="45_Mentorship_Marketplace.py"; New="43_Mentorship_Marketplace.py"; Keep=$true}
)

# First, rename all files to temporary names to avoid conflicts
Write-Host "📝 Phase 1: Creating temporary names..." -ForegroundColor Yellow
foreach ($mapping in $pageMapping) {
    if (Test-Path $mapping.Current) {
        $tempName = "TEMP_" + $mapping.New
        try {
            Rename-Item $mapping.Current $tempName -ErrorAction Stop
            Write-Host "✅ Renamed $($mapping.Current) to $tempName" -ForegroundColor Green
        } catch {
            Write-Host "Failed to rename $($mapping.Current): $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️  File not found: $($mapping.Current)" -ForegroundColor Orange
    }
}

# Second, rename from temporary names to final names
Write-Host "📝 Phase 2: Applying final numbering..." -ForegroundColor Yellow
foreach ($mapping in $pageMapping) {
    $tempName = "TEMP_" + $mapping.New
    if (Test-Path $tempName) {
        try {
            Rename-Item $tempName $mapping.New -ErrorAction Stop
            Write-Host "✅ Final rename: $tempName to $($mapping.New)" -ForegroundColor Green
        } catch {
            Write-Host "Failed final rename $tempName" -ForegroundColor Red
        }
    }
}

Write-Host "🎉 Renumbering complete!" -ForegroundColor Cyan
Write-Host "📊 Listing final structure..." -ForegroundColor Cyan
Get-ChildItem "*.py" | Sort-Object Name