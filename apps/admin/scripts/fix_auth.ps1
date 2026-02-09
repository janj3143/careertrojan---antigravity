# Fix Fallback Authentication in All Pages
# This script replaces all "return True  # Fallback authentication" with proper auth checks

$pages = @(
    "04_Compliance_Audit.py",
    "07_Batch_Processing.py", 
    "09_AI_Content_Generator.py",
    "10_Market_Intelligence_Center.py",
    "11_Competitive_Intelligence.py",
    "12_Web_Company_Intelligence.py",
    "14_Contact_Communication.py",
    "15_Advanced_Settings.py",
    "16_Advanced_Logging.py",
    "17_System_Snapshot.py",
    "19_Legacy_Utilities.py",
    "20_Enhanced_Glossary.py"
)

$oldPattern = "    return True  # Fallback authentication"
$newCode = @"
    if not st.session_state.get('admin_authenticated', False):
        st.error("🔒 **ADMIN AUTHENTICATION REQUIRED**")
        st.warning("You must login through the main admin portal to access this module.")
        
        if st.button("🏠 Return to Main Portal", type="primary"):
            st.switch_page("main.py")
        st.stop()
    return True
"@

foreach ($page in $pages) {
    if (Test-Path $page) {
        $content = Get-Content $page -Raw -Encoding UTF8
        if ($content -match [regex]::Escape($oldPattern)) {
            $newContent = $content -replace [regex]::Escape($oldPattern), $newCode
            Set-Content $page -Value $newContent -Encoding UTF8
            Write-Host "✅ Fixed authentication in $page" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Pattern not found in $page" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ File not found: $page" -ForegroundColor Red
    }
}

Write-Host "`n🔒 Authentication fix completed for all pages!" -ForegroundColor Cyan