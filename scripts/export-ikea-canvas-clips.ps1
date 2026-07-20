$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\ikea_canvas_frame_clip.scad"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$processPreset = "profiles/slicer/ecc2_028_functional_draft.json"
$exportDir = Join-Path $root "exports\ikea-canvas-frame-clips"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

function Export-Part($name, $partId, $expectedBodies) {
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

Export-Part "single-canvas-clip" 1 1
Export-Part "four-canvas-clips-print-plate" 0 4
Export-Part "board-gap-fit-coupon" 2 3

foreach ($render in @(
    @{ Name = "single-clip.png"; Part = 1 },
    @{ Name = "four-clip-print-plate.png"; Part = 0 },
    @{ Name = "board-gap-fit-coupon.png"; Part = 2 },
    @{ Name = "assembly.png"; Part = 3 }
)) {
    & $openscad -o (Join-Path $exportDir $render.Name) `
        --imgsize=1200,800 --viewall -D "part_id=$($render.Part)" $model
    if ($LASTEXITCODE -ne 0) { throw "Preview failed: $($render.Name)" }
}

& $python (Join-Path $root "scripts\summarize-ikea-canvas-clips.py")
if ($LASTEXITCODE -ne 0) { throw "Canvas clip agent report failed" }

Write-Host "Exported IKEA canvas frame clips to $exportDir"
