$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\parametric_sd_travel_wallet.scad"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$processPreset = "profiles/slicer/ecc2_028_functional_draft.json"
$exportDir = Join-Path $root "exports\sd-travel-wallet"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

function Export-Part($name, $partId, $cardCount, $expectedBodies = 1) {
    $output = Join-Path $exportDir "$name.stl"
    & $openscad -o $output -D "part_id=$partId" -D "card_count=$cardCount" $model
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD export failed: $name" }
    & $python -m agentic_cad.stl_cli $output `
        --profile $profile `
        --output (Join-Path $exportDir "$name-evaluation") `
        --expected-bodies $expectedBodies `
        --process-preset $processPreset
    if ($LASTEXITCODE -ne 0) { throw "Validation failed: $name" }
}

foreach ($cardCount in @(5, 8)) {
    Export-Part "sd-wallet-$cardCount-card-tray" 1 $cardCount
    Export-Part "sd-wallet-$cardCount-card-sleeve" 2 $cardCount

    $collision = Join-Path $exportDir "sd-wallet-$cardCount-card-assembly-collision.stl"
    Remove-Item $collision -ErrorAction SilentlyContinue
    & $openscad -o $collision -D "part_id=5" -D "card_count=$cardCount" $model 2>&1 | Out-Host
    & $python (Join-Path $root "scripts\check-collision-mesh.py") $collision
    if ($LASTEXITCODE -ne 0) { throw "$cardCount-card SD wallet assembly collision detected" }
}

Export-Part "latch-preflight-coupon" 6 5 2

foreach ($render in @(
    @{ Name = "5-card-print-layout.png"; Part = 0; Count = 5 },
    @{ Name = "5-card-assembly.png"; Part = 3; Count = 5 },
    @{ Name = "5-card-exploded.png"; Part = 4; Count = 5 },
    @{ Name = "8-card-print-layout.png"; Part = 0; Count = 8 },
    @{ Name = "8-card-assembly.png"; Part = 3; Count = 8 },
    @{ Name = "8-card-exploded.png"; Part = 4; Count = 8 },
    @{ Name = "latch-preflight-coupon.png"; Part = 6; Count = 5 }
)) {
    & $openscad -o (Join-Path $exportDir $render.Name) `
        --imgsize=1200,800 --viewall -D "part_id=$($render.Part)" `
        -D "card_count=$($render.Count)" $model
    if ($LASTEXITCODE -ne 0) { throw "Preview failed: $($render.Name)" }
}

& $python (Join-Path $root "scripts\summarize-sd-wallet-run.py")
if ($LASTEXITCODE -ne 0) { throw "SD wallet agent report failed" }

Write-Host "Exported parametric SD travel wallet to $exportDir"
