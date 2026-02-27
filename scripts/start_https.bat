@echo off
chcp 65001 >nul
echo ================================================
echo   Borofone Chat - HTTPS Server Launcher
echo ================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Not running as Administrator!
    echo Port 443 requires admin privileges.
    echo.
    echo Please run this script as Administrator.
    echo.
    pause
    exit /b 1
)

REM Check if SSL certificates exist (PFX or PEM)
if exist "ssl\voice.pfx" (
    echo [OK] Found PFX certificate: ssl\voice.pfx
    echo      Will auto-convert to PEM format...
    goto :start_server
)

if exist "ssl\cert.pem" if exist "ssl\key.pem" (
    echo [OK] Found PEM certificates
    goto :start_server
)

echo [ERROR] SSL certificates not found!
echo.
echo Please run first:
echo   PowerShell ^(as Admin^): .\scripts\generate_ssl.ps1
echo.
pause
exit /b 1

:start_server
echo.
echo Starting HTTPS server...
echo Address: https://26.150.183.241/
echo.
echo Press Ctrl+C to stop
echo ================================================
echo.

python run_https.py

pause
