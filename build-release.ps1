# Build release zip for cursor-concept.
# Usage: pwsh -File .\build-release.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ReleaseDir  = Join-Path $ProjectRoot "release"
$Version     = "v1.0.0"
$ZipName     = "cursor-concept-$Version.zip"
$ZipPath     = Join-Path $ReleaseDir $ZipName

# Ensure clean release directory
if (Test-Path $ReleaseDir) {
    Remove-Item -Recurse -Force $ReleaseDir
}
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null

# Staging directory
$Stage = Join-Path $ReleaseDir "staging"
New-Item -ItemType Directory -Path $Stage | Out-Null

# Copy distribution files
$items = @(
    "README.md",
    "Agreement.txt",
    "install.ps1",
    "install.cmd",
    "themes"
)

foreach ($item in $items) {
    $src = Join-Path $ProjectRoot $item
    $dst = Join-Path $Stage $item
    if (Test-Path $src -PathType Container) {
        Copy-Item -Recurse -Force $src $dst
    } else {
        Copy-Item -Force $src $dst
    }
}

# Create zip
Compress-Archive -Path "$Stage\*" -DestinationPath $ZipPath -Force

# Report
$zipSize = (Get-Item $ZipPath).Length
Write-Host "Release built: $ZipPath" -ForegroundColor Green
Write-Host "Size: $([math]::Round($zipSize / 1MB, 2)) MB" -ForegroundColor Green

# Cleanup staging
Remove-Item -Recurse -Force $Stage
