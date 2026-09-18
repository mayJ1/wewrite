param(
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot 'build_portable.ps1') -SkipInstall:$SkipInstall
return
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Root ".build-venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$DistRoot = Join-Path $Root "dist"
$AppDist = Join-Path $DistRoot "WeWrite"
$BuildRoot = Join-Path $Root "build\pyinstaller"
$ZipPath = Join-Path $DistRoot "WeWrite-Windows-x64.zip"

Set-Location $Root

if (-not (Test-Path $Python)) {
  Write-Host "Creating isolated build environment..."
  python -m venv $Venv
}

if (-not $SkipInstall) {
  Write-Host "Installing packaging dependencies..."
  & $Python -m pip install --upgrade pip
  & $Python -m pip install -r (Join-Path $Root "requirements-distribution.txt")
}

foreach ($path in @($AppDist, $BuildRoot)) {
  if (Test-Path -LiteralPath $path) {
    $resolved = (Resolve-Path -LiteralPath $path).Path
    if (-not $resolved.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing to remove path outside project: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
  }
}

if (Test-Path -LiteralPath $ZipPath) {
  Remove-Item -LiteralPath $ZipPath -Force
}

Write-Host "Building WeWrite..."
& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --distpath $DistRoot `
  --workpath $BuildRoot `
  (Join-Path $Root "packaging\wewrite.spec")

Copy-Item -LiteralPath (Join-Path $Root "packaging\Start-WeWrite.bat") -Destination $AppDist
Copy-Item -LiteralPath (Join-Path $Root "packaging\README.txt") -Destination $AppDist
Copy-Item -LiteralPath (Join-Path $Root "packaging\WeWrite-Config-Guide.pdf") -Destination $AppDist

Write-Host "Creating ZIP package..."
Compress-Archive -Path $AppDist -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "Build complete:"
Write-Host "  Folder: $AppDist"
Write-Host "  ZIP:    $ZipPath"
