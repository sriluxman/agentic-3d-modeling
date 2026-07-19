$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\skadis_micro_cassette.scad"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$processPreset = "profiles/slicer/ecc2_028_functional_draft.json"
$exportDir = Join-Path $root "exports\skadis-micro-cassette"
$env:OPENSCADPATH = "$(Join-Path $root '.cad-libs');$(Join-Path $root 'components\vendor')"

& (Join-Path $root "scripts\install-cad-libraries.ps1")
& $python (Join-Path $root "scripts\export-skadis-seat-stl.py")
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

Export-Part "cassette-body" 1
Export-Part "cassette-lid" 2
Export-Part "cassette-divider" 3
Export-Part "cassette-latch" 4
Export-Part "latch-preflight-coupon" 7 3

foreach ($probe in @(
    @{ Name = "closed"; Part = 8 },
    @{ Name = "open"; Part = 9 }
)) {
    $collision = Join-Path $exportDir "collision-$($probe.Name).stl"
    Remove-Item $collision -ErrorAction SilentlyContinue
    & $openscad -o $collision -D "part_id=$($probe.Part)" $model 2>&1 | Out-Host
    & $python (Join-Path $root "scripts\check-collision-mesh.py") $collision
    if ($LASTEXITCODE -ne 0) { throw "Assembly collision detected: $($probe.Name)" }
}

foreach ($render in @(
    @{ Name = "print-layout.png"; Part = 0 },
    @{ Name = "assembly-closed.png"; Part = 5 },
    @{ Name = "assembly-open.png"; Part = 6 },
    @{ Name = "latch-preflight-coupon.png"; Part = 7 }
)) {
    & $openscad -o (Join-Path $exportDir $render.Name) `
        --imgsize=1200,800 --viewall -D "part_id=$($render.Part)" $model
    if ($LASTEXITCODE -ne 0) { throw "Preview failed: $($render.Name)" }
}

& $python (Join-Path $root "scripts\summarize-cassette-run.py")
if ($LASTEXITCODE -ne 0) { throw "Cassette production target failed" }

Write-Host "Exported SKADIS micro-cassette to $exportDir"
