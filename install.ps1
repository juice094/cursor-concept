# Install or restore cursor-concept themes (dark / light).
#
# Usage:
#   pwsh -File .\install.ps1              # Install dark (default)
#   pwsh -File .\install.ps1 -Light       # Install light
#   pwsh -File .\install.ps1 -Restore     # Restore backed-up scheme

[CmdletBinding()]
param(
    [switch]$Light,
    [switch]$Restore
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$ProjectRoot   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Theme         = if ($Light) { 'light' } else { 'dark' }
$BaseDir       = Join-Path $ProjectRoot "themes" $Theme "base"
$VariantDir    = Join-Path $ProjectRoot "themes" $Theme "01_default"
$InstalledDir  = Join-Path $ProjectRoot "installed" $Theme
$BackupFile    = Join-Path $ProjectRoot "backup" "cursor_backup.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Ensure-Dir($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

function Export-CursorBackup {
    Ensure-Dir (Split-Path -Parent $BackupFile)
    $regPath = "HKCU:\Control Panel\Cursors"
    $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
    $backup = @{}
    if ($props) {
        $props.PSObject.Properties | Where-Object {
            $_.Name -notin @('PSPath','PSParentPath','PSChildName','PSDrive','PSProvider')
        } | ForEach-Object {
            $backup[$_.Name] = $_.Value
        }
    }
    $backup | ConvertTo-Json -Depth 4 | Set-Content -Path $BackupFile -Encoding UTF8
    Write-Host "Backup saved to: $BackupFile" -ForegroundColor Green
}

function Import-CursorBackup {
    if (-not (Test-Path $BackupFile)) {
        throw "No backup file found at $BackupFile"
    }
    $backup = Get-Content -Path $BackupFile -Raw | ConvertFrom-Json
    $regPath = "HKCU:\Control Panel\Cursors"
    foreach ($prop in $backup.PSObject.Properties.Name) {
        Set-ItemProperty -Path $regPath -Name $prop -Value $backup.$prop -ErrorAction SilentlyContinue
    }
    Write-Host "Cursor scheme restored from backup." -ForegroundColor Green
}

function Refresh-Cursors {
    Add-Type @"
using System; using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, string pvParam, uint fWinIni);
    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
}
"@ -ErrorAction SilentlyContinue

    [void][Win32]::SystemParametersInfo(0x0057, 0, $null, 0x02 -bor 0x01)

    $HWND_BROADCAST = [IntPtr]0xffff
    $WM_SETTINGCHANGE = 0x1a
    $result = [UIntPtr]::Zero
    [void][Win32]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE, [UIntPtr]::Zero, "WindowsThemeElement", 0x0002, 5000, [ref]$result)
}

# ---------------------------------------------------------------------------
# Restore mode
# ---------------------------------------------------------------------------
if ($Restore) {
    Import-CursorBackup
    Refresh-Cursors
    if (Test-Path (Join-Path $ProjectRoot "installed")) {
        if (Test-Path $InstalledDir) {
            Remove-Item -Recurse -Force $InstalledDir -ErrorAction SilentlyContinue
            Write-Host "Removed installed cursor files from $InstalledDir" -ForegroundColor Yellow
        }
    }
    Write-Host "`nRestore complete. Log off and back on if cursors look wrong." -ForegroundColor Cyan
    return
}

# ---------------------------------------------------------------------------
# Validate inputs
# ---------------------------------------------------------------------------
if (-not (Test-Path $VariantDir)) {
    throw "Variant directory not found: $VariantDir"
}
if (-not (Test-Path $BaseDir)) {
    throw "Base cursor directory not found: $BaseDir"
}

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
Write-Host "Installing cursor-concept $Theme ..." -ForegroundColor Cyan

# 1. Backup current scheme (only if no backup exists yet)
if (-not (Test-Path $BackupFile)) {
    Export-CursorBackup
} else {
    Write-Host "Backup already exists at $BackupFile (skipped)" -ForegroundColor DarkGray
}

# 2. Copy cursor files to local installed directory
Ensure-Dir $InstalledDir
Get-ChildItem -Path $BaseDir -Filter "*.cur" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $InstalledDir -Force
}
Get-ChildItem -Path $VariantDir -Filter "*.ani" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $InstalledDir -Force
}
Write-Host "Copied cursor files to $InstalledDir" -ForegroundColor Green

# 3. Registry cursor map
$cursorMap = @{
    "AppStarting" = "working.ani"
    "Arrow"       = "pointer.cur"
    "Crosshair"   = "precision.cur"
    "Hand"        = "link.cur"
    "Help"        = "help.cur"
    "IBeam"       = "beam.cur"
    "No"          = "unavailable.cur"
    "NWPen"       = "handwriting.cur"
    "SizeAll"     = "move.cur"
    "SizeNESW"    = "dgn2.cur"
    "SizeNS"      = "vert.cur"
    "SizeNWSE"    = "dgn1.cur"
    "SizeWE"      = "horz.cur"
    "UpArrow"     = "alternate.cur"
    "Wait"        = "busy.ani"
    "Person"      = "person.cur"
    "Pin"         = "pin.cur"
}

# 4. Write HKCU registry
$regPath = "HKCU:\Control Panel\Cursors"
foreach ($name in $cursorMap.Keys) {
    $file = $cursorMap[$name]
    $fullPath = Join-Path $InstalledDir $file
    if (Test-Path $fullPath) {
        Set-ItemProperty -Path $regPath -Name $name -Value $fullPath
    } else {
        Write-Warning "Cursor file missing, skipping: $fullPath"
    }
}

# Set scheme display name
Set-ItemProperty -Path $regPath -Name "(Default)" -Value "cursor-concept $Theme"

# 5. Refresh
Refresh-Cursors

Write-Host "`nInstallation complete." -ForegroundColor Green
Write-Host "To switch theme, run: pwsh -File .\install.ps1 -Light" -ForegroundColor Cyan
Write-Host "To restore defaults, run: pwsh -File .\install.ps1 -Restore" -ForegroundColor Cyan
