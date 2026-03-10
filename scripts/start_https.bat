@echo off
chcp 65001 >nul
set "PUBLIC_HOST=%BOROFONE_PUBLIC_HOST%"
if "%PUBLIC_HOST%"=="" set "PUBLIC_HOST=localhost"
set "HTTPS_PORT=%BOROFONE_HTTPS_PORT%"
if "%HTTPS_PORT%"=="" set "HTTPS_PORT=443"

echo ================================================
echo   Borofone Chat - HTTPS Server Launcher
echo ================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Not running as Administrator!
    echo Port %HTTPS_PORT% may require admin privileges.
    echo.
    pause
    exit /b 1
)

if exist "ssl\voice.pfx" (
    echo [OK] Found PFX certificate: ssl\voice.pfx
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
echo Address: https://%PUBLIC_HOST%:%HTTPS_PORT%/
echo.
echo Press Ctrl+C to stop
echo ================================================
echo.

python run_https.py --host 0.0.0.0 --port %HTTPS_PORT%

pause
