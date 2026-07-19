$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\india_austria_dovetail_cube.scad"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$processPreset = "profiles/slicer/ecc2_028_functional_draft.json"
$exportDir = Join-Path $root "exports\india-austria-dovetail-cube"
$env:OPENSCADPATH = "$(Join-Path $root '.cad-libs');$(Join-Path $root 'components\vendor')"

& (Join-Path $root "scripts\install-cad-libraries.ps1")
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

Export-Part "india-half" 1
Export-Part "austria-half" 2
$collision = Join-Path $exportDir "assembly-collision.stl"
Remove-Item $collision -ErrorAction SilentlyContinue
& $openscad -o $collision -D "part_id=5" $model 2>&1 | Out-Host
& $python (Join-Path $root "scripts\check-collision-mesh.py") $collision
if ($LASTEXITCODE -ne 0) { throw "Dovetail cube assembly collision detected" }

$colorDir = Join-Path $exportDir "color-volumes"
New-Item -ItemType Directory -Force -Path $colorDir | Out-Null
$colorVolumes = @(
    @{ Name = "india-green"; Part = 10 },
    @{ Name = "india-white"; Part = 11 },
    @{ Name = "india-saffron"; Part = 12 },
    @{ Name = "austria-red-bottom"; Part = 13 },
    @{ Name = "austria-white"; Part = 14 },
    @{ Name = "austria-red-top"; Part = 15 }
)
foreach ($volume in $colorVolumes) {
    & $openscad -o (Join-Path $colorDir "$($volume.Name).stl") `
        -D "part_id=$($volume.Part)" $model
    if ($LASTEXITCODE -ne 0) { throw "Color volume export failed: $($volume.Name)" }
}
Remove-Item (Join-Path $exportDir "multicolor-print-plate.3mf") -ErrorAction SilentlyContinue
& $python (Join-Path $root "scripts\export-color-3mf.py")
if ($LASTEXITCODE -ne 0) { throw "Color-aware 3MF export failed" }

foreach ($render in @(
    @{ Name = "print-layout.png"; Part = 0 },
    @{ Name = "assembly.png"; Part = 3 },
    @{ Name = "exploded.png"; Part = 4 }
)) {
    & $openscad -o (Join-Path $exportDir $render.Name) `
        --imgsize=1200,800 --viewall -D "part_id=$($render.Part)" $model
    if ($LASTEXITCODE -ne 0) { throw "Preview failed: $($render.Name)" }
}

& $python (Join-Path $root "scripts\summarize-cube-run.py")
if ($LASTEXITCODE -ne 0) { throw "Dovetail cube agent report failed" }

Write-Host "Exported India-Austria dovetail cube to $exportDir"
