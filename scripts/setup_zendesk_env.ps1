param(
    [string]$TemplatePath = ".env.zendesk.template",
    [string]$TargetPath = ".env"
)

$ErrorActionPreference = "Stop"

function Parse-EnvFile {
    param([string]$Path)

    $map = @{}
    if (-not (Test-Path $Path)) {
        return $map
    }

    $lines = Get-Content $Path -Encoding UTF8
    foreach ($line in $lines) {
        $trim = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trim)) { continue }
        if ($trim.StartsWith("#")) { continue }
        if ($trim -notmatch "=") { continue }

        $parts = $trim.Split("=", 2)
        $key = $parts[0].Trim()
        $value = if ($parts.Count -gt 1) { $parts[1] } else { "" }
        if (-not [string]::IsNullOrWhiteSpace($key)) {
            $map[$key] = $value
        }
    }

    return $map
}

if (-not (Test-Path $TemplatePath)) {
    Write-Host "[FAIL] Template not found: $TemplatePath" -ForegroundColor Red
    exit 1
}

$templateLines = Get-Content $TemplatePath -Encoding UTF8
$templateMap = Parse-EnvFile -Path $TemplatePath
$targetExists = Test-Path $TargetPath

if (-not $targetExists) {
    Copy-Item -Path $TemplatePath -Destination $TargetPath -Force
    Write-Host "[OK] Created $TargetPath from template." -ForegroundColor Green
}
else {
    $targetMap = Parse-EnvFile -Path $TargetPath
    $appendLines = New-Object System.Collections.Generic.List[string]

    foreach ($key in $templateMap.Keys) {
        if (-not $targetMap.ContainsKey($key)) {
            $appendLines.Add("$key=$($templateMap[$key])")
        }
    }

    if ($appendLines.Count -gt 0) {
        Add-Content -Path $TargetPath -Value ""
        Add-Content -Path $TargetPath -Value "# --- Zendesk wiring keys added by setup_zendesk_env.ps1 ---"
        Add-Content -Path $TargetPath -Value $appendLines
        Write-Host "[OK] Added $($appendLines.Count) missing Zendesk key(s) to $TargetPath." -ForegroundColor Green
    }
    else {
        Write-Host "[OK] No missing Zendesk keys. $TargetPath already contains template keys." -ForegroundColor Green
    }
}

$merged = Parse-EnvFile -Path $TargetPath
$requiredKeys = @(
    "HELPDESK_PROVIDER",
    "HELPDESK_WIDGET_ENABLED",
    "HELPDESK_SSO_ENABLED",
    "ZENDESK_SUBDOMAIN",
    "ZENDESK_SHARED_SECRET"
)

$placeholderPatterns = @("your-subdomain", "__REPLACE_WITH_SECURE_SECRET__", "")
$pending = New-Object System.Collections.Generic.List[string]

foreach ($k in $requiredKeys) {
    if (-not $merged.ContainsKey($k)) {
        $pending.Add($k)
        continue
    }
    $v = [string]$merged[$k]
    if ($k -eq "HELPDESK_PROVIDER" -and $v -ne "zendesk") {
        $pending.Add("$k (set to zendesk)")
        continue
    }
    if ($k -eq "ZENDESK_SUBDOMAIN" -and ($v -like "*your-subdomain*" -or [string]::IsNullOrWhiteSpace($v))) {
        $pending.Add($k)
        continue
    }
    if ($k -eq "ZENDESK_SHARED_SECRET" -and ($v -like "*__REPLACE_WITH_SECURE_SECRET__*" -or [string]::IsNullOrWhiteSpace($v))) {
        $pending.Add($k)
        continue
    }
}

if ($pending.Count -gt 0) {
    Write-Host "[WARN] Zendesk env is not fully configured yet. Update these keys:" -ForegroundColor DarkYellow
    $pending | ForEach-Object { Write-Host " - $_" -ForegroundColor DarkYellow }
    exit 2
}

Write-Host "[OK] Zendesk env keys look configured. Next: run verify_zendesk_wiring.ps1 -Strict" -ForegroundColor Green
exit 0
