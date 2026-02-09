# Clean Streamlit Portal Launcher
# Fixes the directory flipping issue

param(
    [Parameter(Mandatory=$false)]
    [string]$Portal = "all"
)

# Define the Python path
$PythonPath = "C:\IntelliCV-AI\IntelliCV\env310\python.exe"
$BaseDir = "C:\IntelliCV-AI\IntelliCV\SANDBOX\BACKEND-ADMIN-REORIENTATION\user_portal_final"

# Verify Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "❌ Python not found at: $PythonPath" -ForegroundColor Red
    Write-Host "Please check the Python environment path." -ForegroundColor Yellow
    exit 1
}

# Verify base directory exists
if (-not (Test-Path $BaseDir)) {
    Write-Host "❌ Portal directory not found: $BaseDir" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 IntelliCV-AI Portal Launcher" -ForegroundColor Cyan
Write-Host "Using Python: $PythonPath" -ForegroundColor Green
Write-Host "Base Directory: $BaseDir" -ForegroundColor Green
Write-Host ""

function Start-IntelliCVPortal {
    param(
        [string]$PortalName,
        [string]$PortalDir,
        [int]$Port,
        [string]$Color
    )
    
    $FullPath = Join-Path $BaseDir $PortalDir
    $WelcomeFile = Join-Path $FullPath "00_Welcome.py"
    
    Write-Host "🔍 Checking $PortalName..." -ForegroundColor $Color
    Write-Host "   Directory: $FullPath" -ForegroundColor Gray
    Write-Host "   Welcome file: $WelcomeFile" -ForegroundColor Gray
    
    if (-not (Test-Path $FullPath)) {
        Write-Host "❌ Portal directory not found: $FullPath" -ForegroundColor Red
        return $false
    }
    
    if (-not (Test-Path $WelcomeFile)) {
        Write-Host "❌ Welcome file not found: $WelcomeFile" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ $PortalName verified - Starting on port $Port" -ForegroundColor $Color
    
    # Create a script block that maintains the correct directory
    $ScriptBlock = {
        param($PythonPath, $PortalDir, $Port, $PortalName)
        
        Set-Location $PortalDir
        Write-Host "🚀 Starting $PortalName in: $(Get-Location)" -ForegroundColor Green
        Write-Host "📍 URL: http://localhost:$Port" -ForegroundColor Cyan
        Write-Host ""
        
        & $PythonPath -m streamlit run "00_Welcome.py" --server.port $Port
    }
    
    # Start in new PowerShell window with correct working directory
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command", 
        "& { $($ScriptBlock.ToString()) } '$PythonPath' '$FullPath' $Port '$PortalName'"
    ) -WindowStyle Normal
    
    Start-Sleep 2
    return $true
}

# Portal configurations
$Portals = @(
    @{
        Name = "Professional Pro"
        Dir = "pages_pro"
        Port = 8503
        Color = "Magenta"
    },
    @{
        Name = "Simple Start"
        Dir = "pages_simple"
        Port = 8504
        Color = "Blue"
    },
    @{
        Name = "Backup Recovered"
        Dir = "pages_backup_recovered"
        Port = 8508
        Color = "Green"
    }
)

if ($Portal -eq "all") {
    Write-Host "🎯 Starting all portals..." -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($p in $Portals) {
        $success = Start-IntelliCVPortal -PortalName $p.Name -PortalDir $p.Dir -Port $p.Port -Color $p.Color
        if (-not $success) {
            Write-Host "❌ Failed to start $($p.Name)" -ForegroundColor Red
        }
    }
} else {
    $selectedPortal = $Portals | Where-Object { $_.Name -like "*$Portal*" -or $_.Dir -like "*$Portal*" }
    if ($selectedPortal) {
        Start-IntelliCVPortal -PortalName $selectedPortal.Name -PortalDir $selectedPortal.Dir -Port $selectedPortal.Port -Color $selectedPortal.Color
    } else {
        Write-Host "❌ Portal '$Portal' not found" -ForegroundColor Red
        Write-Host "Available portals: $($Portals.Name -join ', ')" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🌐 Portal URLs:" -ForegroundColor White
Write-Host "🏆 Professional Pro:    http://localhost:8503" -ForegroundColor Magenta
Write-Host "⚡ Simple Start:        http://localhost:8504" -ForegroundColor Blue
Write-Host "🚀 Backup Recovered:    http://localhost:8508" -ForegroundColor Green
Write-Host ""
Write-Host "💰 New Pricing Features:" -ForegroundColor White
Write-Host "   • Free Starter ($0) - Partner-supported" -ForegroundColor Gray
Write-Host "   • Monthly Pro ($15.99) - NEW PRICE!" -ForegroundColor Gray
Write-Host "   • Annual Pro ($149.99) - Save $42!" -ForegroundColor Gray
Write-Host "   • Enterprise Premium ($299.99) - Full features" -ForegroundColor Gray
Write-Host ""
Write-Host "🛡️ 2FA Security Features:" -ForegroundColor White
Write-Host "   • Demo accounts: demo@intellicv.ai/demo123" -ForegroundColor Gray
Write-Host "   • Pro accounts: pro@intellicv.ai/pro123" -ForegroundColor Gray
Write-Host "   • 2FA codes: 123456 or 000000" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 To stop: Close PowerShell windows or press Ctrl+C" -ForegroundColor Red
Write-Host ""

Read-Host "Press Enter to exit launcher (portals will continue running)"