param([switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location -LiteralPath $Root
$Python = Join-Path $Root '.build-venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv .build-venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create build environment' }
}
if (-not $SkipInstall) {
    & $Python -m pip install -r requirements-distribution.txt
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install dependencies' }
}
& $Python packaging\generate_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Failed to generate application icon' }
& $Python -m PyInstaller --noconfirm --clean --distpath dist\portable --workpath build\portable packaging\wewrite.spec
if ($LASTEXITCODE -ne 0) { throw 'Portable build failed' }
Write-Host "Portable executable: $Root\dist\portable\WeWrite.exe"
