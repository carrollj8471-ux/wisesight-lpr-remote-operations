$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Missing local virtual environment. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

if (-not $env:PORT) {
    $env:PORT = "5055"
}

if (-not $env:WISESIGHT_DB_PATH) {
    $env:WISESIGHT_DB_PATH = "runtime.sqlite"
}

Set-Location $repoRoot
& $python -u app.py
