$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$openscad = "C:\Program Files\OpenSCAD\openscad.exe"
$model = Join-Path $root "models\snapfit_binder_page.scad"
$exportDir = Join-Path $root "exports"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

function Invoke-OpenScadExport($output, $partId, $extraArgs = @()) {
    & $openscad -o $output @extraArgs -D "part_id=$partId" $model
    for ($i = 0; $i -lt 50; $i++) {
        if ((Test-Path $output) -and ((Get-Item $output).Length -gt 0)) {
            return
        }
        Start-Sleep -Milliseconds 100
    }
    throw "OpenSCAD did not create expected output: $output"
}

Invoke-OpenScadExport (Join-Path $exportDir "binder_rail.stl") 1
Invoke-OpenScadExport (Join-Path $exportDir "binder_page.stl") 2
Invoke-OpenScadExport (Join-Path $exportDir "binder_page_preview.png") 0 @("--imgsize=1400,700", "--viewall")
Invoke-OpenScadExport (Join-Path $exportDir "binder_v2_rail.stl") 1
Invoke-OpenScadExport (Join-Path $exportDir "binder_v2_page.stl") 2
Invoke-OpenScadExport (Join-Path $exportDir "binder_v2_preview.png") 0 @("--imgsize=1400,700", "--viewall")

Write-Host "Exported binder/page files to $exportDir"
