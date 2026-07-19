$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\parametric_sd_travel_wallet.scad"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$processPreset = "profiles/slicer/ecc2_028_functional_draft.json"
$exportDir = Join-Path $root "exports\sd-travel-wallet"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

function Export-Part($name, $partId, $expectedBodies = 1) {
    $output = Join-Path $exportDir "$name.stl"
    & $openscad -o $output -D "part_id=$partId" $model
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD export failed: $name" }
    & $python -m agentic_cad.stl_cli $output `
        --profile $profile `
        --output (Join-Path $exportDir "$name-evaluation") `
        --expected-bodies $expectedBodies `
        --process-preset $processPreset
    if ($LASTEXITCODE -ne 0) { throw "Validation failed: $name" }
}

Export-Part "sd-wallet-tray" 1
Export-Part "sd-wallet-sleeve" 2
Export-Part "latch-preflight-coupon" 6 2

$collision = Join-Path $exportDir "assembly-collision.stl"
Remove-Item $collision -ErrorAction SilentlyContinue
& $openscad -o $collision -D "part_id=5" $model 2>&1 | Out-Host
& $python (Join-Path $root "scripts\check-collision-mesh.py") $collision
if ($LASTEXITCODE -ne 0) { throw "SD wallet assembly collision detected" }

foreach ($render in @(
    @{ Name = "print-layout.png"; Part = 0 },
    @{ Name = "assembly.png"; Part = 3 },
    @{ Name = "exploded.png"; Part = 4 },
    @{ Name = "latch-preflight-coupon.png"; Part = 6 }
)) {
    & $openscad -o (Join-Path $exportDir $render.Name) `
        --imgsize=1200,800 --viewall -D "part_id=$($render.Part)" $model
    if ($LASTEXITCODE -ne 0) { throw "Preview failed: $($render.Name)" }
}

& $python (Join-Path $root "scripts\summarize-sd-wallet-run.py")
if ($LASTEXITCODE -ne 0) { throw "SD wallet agent report failed" }

Write-Host "Exported parametric SD travel wallet to $exportDir"
