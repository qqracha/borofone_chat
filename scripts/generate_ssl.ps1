# SSL Certificate Generation Script for Windows
# Run this script in PowerShell as Administrator

param(
    [string]$IpAddress = "26.150.183.241",
    [string]$OutputDir = ".\ssl",
    [string]$Password = "1234"
)

Write-Host "=== SSL Certificate Generation for Radmin VPN ===" -ForegroundColor Cyan
Write-Host "IP Address: $IpAddress" -ForegroundColor Yellow
Write-Host "Output Directory: $OutputDir" -ForegroundColor Yellow
Write-Host ""

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created directory: $OutputDir" -ForegroundColor Green
}

# Step 1: Create self-signed certificate
Write-Host "Step 1: Creating self-signed certificate..." -ForegroundColor Cyan

$cert = New-SelfSignedCertificate `
    -DnsName $IpAddress `
    -CertStoreLocation "cert:\LocalMachine\My" `
    -FriendlyName "Borofone Chat SSL" `
    -NotAfter (Get-Date).AddYears(5)

Write-Host "Certificate created with Thumbprint: $($cert.Thumbprint)" -ForegroundColor Green

# Step 2: Export to PFX
Write-Host "Step 2: Exporting to PFX format..." -ForegroundColor Cyan

$pfxPath = Join-Path $OutputDir "voice.pfx"
$securePassword = ConvertTo-SecureString -String $Password -Force -AsPlainText

Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $securePassword | Out-Null
Write-Host "PFX exported to: $pfxPath" -ForegroundColor Green

# Step 3: Export public certificate (for friends to import)
Write-Host "Step 3: Exporting public certificate..." -ForegroundColor Cyan

$crtPath = Join-Path $OutputDir "cert.crt"
Export-Certificate -Cert $cert -FilePath $crtPath -Type CERT | Out-Null
Write-Host "Public certificate exported to: $crtPath" -ForegroundColor Green

# Step 4: Convert to PEM format (for Python/uvicorn)
Write-Host "Step 4: Converting to PEM format..." -ForegroundColor Cyan

$keyPemPath = Join-Path $OutputDir "key.pem"
$certPemPath = Join-Path $OutputDir "cert.pem"

# Check if OpenSSL is available
$opensslAvailable = Get-Command openssl -ErrorAction SilentlyContinue

if ($opensslAvailable) {
    # Export private key
    openssl pkcs12 -in $pfxPath -nocerts -out $keyPemPath -nodes -passin pass:$Password 2>$null
    # Export certificate
    openssl pkcs12 -in $pfxPath -clcerts -nokeys -out $certPemPath -passin pass:$Password 2>$null
    
    Write-Host "PEM files created:" -ForegroundColor Green
    Write-Host "  - $keyPemPath (private key)" -ForegroundColor Yellow
    Write-Host "  - $certPemPath (certificate)" -ForegroundColor Yellow
} else {
    Write-Host "OpenSSL not found. Extracting private key using .NET..." -ForegroundColor Yellow
    
    # Export certificate as PEM using PowerShell
    $certBase64 = [Convert]::ToBase64String($cert.RawData, [Base64FormattingOptions]::InsertLineBreaks)
    $certPemContent = "-----BEGIN CERTIFICATE-----`n$certBase64`n-----END CERTIFICATE-----"
    Set-Content -Path $certPemPath -Value $certPemContent
    
    # Extract private key using .NET
    try {
        # Get the private key from the certificate
        $rsa = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
        if ($rsa) {
            $keyParams = $rsa.ExportParameters($true)
            $rsa.Dispose()
            
            # Convert to PKCS#1 RSA private key format
            $privateKeyBytes = [System.Security.Cryptography.Pkcs.Pkcs8PrivateKeyInfo]::Create($rsa).Encode()
            
            # Alternative: Use PFX directly with Python
            Write-Host "Certificate PEM created: $certPemPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "Private key extraction requires OpenSSL or pyOpenSSL." -ForegroundColor Yellow
            Write-Host "The PFX file can be used directly with Python!" -ForegroundColor Green
            Write-Host ""
            Write-Host "To extract key manually, install OpenSSL and run:" -ForegroundColor Cyan
            Write-Host "  openssl pkcs12 -in $pfxPath -nocerts -out $keyPemPath -nodes -passin pass:$Password" -ForegroundColor White
        }
    } catch {
        Write-Host "Could not extract private key: $_" -ForegroundColor Red
        Write-Host "The PFX file can be used directly with Python!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Certificate Generation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files created in $OutputDir`:" -ForegroundColor White
Get-ChildItem $OutputDir | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Yellow }
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Share cert.crt with your friends" -ForegroundColor White
Write-Host "2. Friends need to import cert.crt to 'Trusted Root Certification Authorities'" -ForegroundColor White
Write-Host "3. Run the server with: python run_https.py" -ForegroundColor White
Write-Host ""
Write-Host "To remove the certificate from Windows store later:" -ForegroundColor DarkGray
Write-Host "  Remove-Item -Path 'cert:\LocalMachine\My\$($cert.Thumbprint)'" -ForegroundColor DarkGray