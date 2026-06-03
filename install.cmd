@echo off
:: Cursor Concept — Quick installer launcher
:: Requires PowerShell 7+ (pwsh)

echo Cursor Concept Installer
echo ========================
echo.

where pwsh >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell 7 ^(pwsh^) is not found in PATH.
    echo Please install it from https://github.com/PowerShell/PowerShell
    pause
    exit /b 1
)

if "%~1"=="light" (
    echo Installing LIGHT theme...
    pwsh -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Light
) else if "%~1"=="restore" (
    echo Restoring default cursors...
    pwsh -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Restore
) else (
    echo Installing DARK theme ^(default^)...
    echo To install light theme, run: install.cmd light
    echo To restore defaults, run: install.cmd restore
    echo.
    pwsh -ExecutionPolicy Bypass -File "%~dp0install.ps1"
)

pause
