$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python CAD environment is missing. Create .venv and install the project first."
}

& $python -m agentic_cad.cli `
    (Join-Path $root "models\python\fit_calibration.py") `
    --profile (Join-Path $root "profiles\elegoo_cc2_pla.json") `
    --output (Join-Path $root "exports\python")
