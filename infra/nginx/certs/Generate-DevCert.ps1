# =============================================================================
# Generate self-signed TLS certificate for local development (Windows)
# =============================================================================
# Usage:  powershell -ExecutionPolicy Bypass -File infra\nginx\certs\Generate-DevCert.ps1
# Output: infra\nginx\certs\dev.crt  +  infra\nginx\certs\dev.key
# =============================================================================

$CertDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Domain  = "localhost"

Write-Host "Generating self-signed certificate for $Domain ..." -ForegroundColor Cyan

# Try OpenSSL first (Git Bash, MSYS2, or standalone)
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if ($openssl) {
    & openssl req -x509 -nodes -newkey rsa:2048 `
        -keyout "$CertDir\dev.key" `
        -out    "$CertDir\dev.crt" `
        -days   365 `
        -subj   "/C=GB/ST=London/L=London/O=CareerTrojan-Dev/CN=$Domain" `
        -addext "subjectAltName=DNS:$Domain,DNS:*.localhost,IP:127.0.0.1"

    Write-Host "Certificate generated via OpenSSL:" -ForegroundColor Green
    Write-Host "  $CertDir\dev.crt"
    Write-Host "  $CertDir\dev.key"
}
else {
    # Fallback: use .NET / New-SelfSignedCertificate (Windows only)
    $cert = New-SelfSignedCertificate `
        -DnsName $Domain, "*.localhost" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddDays(365) `
        -FriendlyName "CareerTrojan Local Dev"

    # Export .crt (public)
    Export-Certificate -Cert $cert -FilePath "$CertDir\dev.crt" -Type CERT | Out-Null

    # Export .pfx then extract key with certutil
    $pfxPath = "$CertDir\dev.pfx"
    $password = ConvertTo-SecureString -String "devonly" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null

    Write-Host "Certificate generated via PowerShell (PFX at $pfxPath):" -ForegroundColor Green
    Write-Host "  $CertDir\dev.crt  (DER — convert to PEM with openssl if needed for nginx)"
    Write-Host "  $CertDir\dev.pfx  (password: devonly)"
    Write-Host ""
    Write-Host "To convert to PEM for nginx:" -ForegroundColor Yellow
    Write-Host "  openssl pkcs12 -in dev.pfx -nocerts -nodes -out dev.key"
    Write-Host "  openssl pkcs12 -in dev.pfx -clcerts -nokeys -out dev.crt"
}
