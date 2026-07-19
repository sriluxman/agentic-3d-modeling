$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$openscad = "C:\Program Files\OpenSCAD\openscad.com"
$model = Join-Path $root "models\jointscad_dovetail_coupon.scad"
$exportDir = Join-Path $root "exports\jointscad-dovetail"
$profile = Join-Path $root "profiles\elegoo_cc2_pla.json"
$python = Join-Path $root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

function Invoke-OpenScadExport($name, $partId, $extraArgs = @()) {
    $output = Join-Path $exportDir $name
    if (Test-Path -LiteralPath $output) {
        Remove-Item -LiteralPath $output
    }
    $renderLog = & $openscad -o $output @extraArgs -D "part_id=$partId" $model 2>&1
    $renderLog | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output)) {
        throw "OpenSCAD failed to create $output"
    }
    return $output
}

$plate = Invoke-OpenScadExport "dovetail_clearance_plate.stl" 0
Invoke-OpenScadExport "receiver_rack.stl" 1 | Out-Null
Invoke-OpenScadExport "dovetail_key.stl" 2 | Out-Null
Invoke-OpenScadExport "print_layout.png" 0 @("--imgsize=1200,700", "--viewall") | Out-Null
Invoke-OpenScadExport "assembly_preview.png" 3 @("--imgsize=1200,700", "--viewall") | Out-Null

& $python -m agentic_cad.stl_cli $plate `
    --profile $profile `
    --output (Join-Path $exportDir "evaluation") `
    --expected-bodies 2
if ($LASTEXITCODE -ne 0) {
    throw "Automated STL or slicer evaluation failed"
}

Write-Host "Exported and validated JointSCAD dovetail coupon at $exportDir"
