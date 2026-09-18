param(
  [int]$Port = 8770,
  [switch]$Restart
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalPackages = Join-Path $Root ".python-packages"
$Requirements = Join-Path $Root "requirements-wewrite.txt"
$Server = Join-Path $Root "app\server.py"

function Write-Step($Message) {
  Write-Host ""
  Write-Host "== $Message" -ForegroundColor Cyan
}

function Get-PythonCandidate {
  $candidates = @()
  if ($env:WEWRITE_PYTHON) {
    $candidates += $env:WEWRITE_PYTHON
  }
  $candidates += (Join-Path $Root "runtime\python\python.exe")
  $candidates += (Join-Path $Root ".venv\Scripts\python.exe")

  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) {
    $candidates += $pythonCmd.Source
  }

  $codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  $candidates += $codexPython

  foreach ($candidate in $candidates) {
    if (-not $candidate) { continue }
    if (-not (Test-Path $candidate)) { continue }
    try {
      & $candidate --version *> $null
      if ($LASTEXITCODE -eq 0) {
        return (Resolve-Path $candidate).Path
      }
    } catch {
      continue
    }
  }

  $pyCmd = Get-Command py -ErrorAction SilentlyContinue
  if ($pyCmd) {
    try {
      & $pyCmd.Source -3 --version *> $null
      if ($LASTEXITCODE -eq 0) {
        return $pyCmd.Source
      }
    } catch {
      # py.exe may exist without an installed Python.
    }
  }

  return $null
}

function Invoke-Python {
  param(
    [string]$Python,
    [string[]]$Arguments
  )

  if ((Split-Path -Leaf $Python).ToLowerInvariant() -eq "py.exe") {
    & $Python -3 @Arguments
  } else {
    & $Python @Arguments
  }
}

function Test-PythonImports {
  param([string]$Python)
  $oldPath = $env:PYTHONPATH
  try {
    $env:PYTHONPATH = $LocalPackages
    Invoke-Python $Python @("-c", "import yaml, requests, bs4, docx")
    return ($LASTEXITCODE -eq 0)
  } catch {
    return $false
  } finally {
    $env:PYTHONPATH = $oldPath
  }
}

function Ensure-Dependencies {
  param([string]$Python)

  if (Test-PythonImports $Python) {
    Write-Host "Python dependencies are ready." -ForegroundColor Green
    return
  }

  Write-Step "Installing local Python dependencies"
  New-Item -ItemType Directory -Path $LocalPackages -Force | Out-Null
  Invoke-Python $Python @("-m", "pip", "install", "--target", $LocalPackages, "-r", $Requirements)
  if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed. Please check the network and pip output above."
  }

  if (-not (Test-PythonImports $Python)) {
    throw "Dependencies were installed, but Python still cannot import them."
  }
}

function Get-ListeningProcessIds {
  param([int]$Port)
  $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if (-not $connections) { return @() }
  return @($connections | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique)
}

Set-Location $Root

Write-Step "Checking Python"
$Python = Get-PythonCandidate
if (-not $Python) {
  throw "No usable Python was found. Install Python 3.11+ or set WEWRITE_PYTHON to python.exe."
}
Write-Host "Using Python: $Python"

Ensure-Dependencies $Python

$pids = Get-ListeningProcessIds $Port
if ($pids.Count -gt 0) {
  if ($Restart) {
    Write-Step "Restarting existing server on port $Port"
    foreach ($processId in $pids) {
      Stop-Process -Id $processId -Force
    }
    Start-Sleep -Seconds 1
  } else {
    Write-Host ""
    Write-Host "WeWrite already appears to be running:" -ForegroundColor Green
    Write-Host "http://127.0.0.1:$Port/"
    Write-Host ""
    Write-Host "Use .\start_wewrite.ps1 -Restart to restart it."
    exit 0
  }
}

Write-Step "Starting WeWrite"
$env:PYTHONPATH = $LocalPackages
Write-Host "Open: http://127.0.0.1:$Port/" -ForegroundColor Green
Write-Host "Press Ctrl+C in this window to stop the server."
Invoke-Python $Python @($Server, "$Port")
