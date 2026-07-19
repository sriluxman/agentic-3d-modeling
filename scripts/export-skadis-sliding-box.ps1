$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\python\skadis_sliding_box.py"
$preview = Join-Path $root "models\skadis_sliding_box_preview.scad"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$exportRoot = Join-Path $root "exports\skadis"
$exportDir = Join-Path $exportRoot "skadis_sliding_box"

& $python -m agentic_cad.cli $model --profile $profile --output $exportRoot
if ($LASTEXITCODE -ne 0) {
    throw "SKADIS sliding box CAD pipeline failed"
}

Copy-Item -LiteralPath (Join-Path $root "models\ikea\T-Clip for Painted Skadis.stl") `
    -Destination (Join-Path $exportDir "t_clip_painted_skadis.stl") -Force

& $python -m agentic_cad.stl_cli (Join-Path $exportDir "t_clip_painted_skadis.stl") `
    --profile $profile `
    --output (Join-Path $exportDir "t_clip_evaluation") `
    --expected-bodies 1
if ($LASTEXITCODE -ne 0) {
    throw "Painted SKADIS T-clip validation failed"
}

foreach ($render in @(
    @{ Name = "print_layout.png"; Mode = 0 },
    @{ Name = "assembly_closed.png"; Mode = 1 },
    @{ Name = "assembly_open.png"; Mode = 2 }
)) {
    & $openscad -o (Join-Path $exportDir $render.Name) `
        --imgsize=1200,800 --viewall -D "mode=$($render.Mode)" $preview
    if ($LASTEXITCODE -ne 0) {
        throw "OpenSCAD preview failed: $($render.Name)"
    }
}

Write-Host "Exported and validated SKADIS sliding box at $exportDir"
