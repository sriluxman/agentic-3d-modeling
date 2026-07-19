$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$openscad = "C:\Program Files\OpenSCAD\openscad.exe"
$model = Join-Path $root "models\library_cantilever_clip.scad"
$exportDir = Join-Path $root "exports"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

function Invoke-OpenScadExport($output, $partId, $extraArgs = @()) {
    if (Test-Path -LiteralPath $output) {
        Remove-Item -LiteralPath $output
    }
    & $openscad -o $output @extraArgs -D "part_id=$partId" $model
    for ($i = 0; $i -lt 50; $i++) {
        if ((Test-Path $output) -and ((Get-Item $output).Length -gt 0)) {
            return
        }
        Start-Sleep -Milliseconds 100
    }
    throw "OpenSCAD did not create expected output: $output"
}

Invoke-OpenScadExport (Join-Path $exportDir "library_clip.stl") 1
Invoke-OpenScadExport (Join-Path $exportDir "library_insert.stl") 2
Invoke-OpenScadExport (Join-Path $exportDir "library_clip_preview.png") 0 @("--imgsize=1400,700", "--viewall")
Invoke-OpenScadExport (Join-Path $exportDir "library_clip_assembly.png") 3 @("--imgsize=1400,700", "--viewall")

Write-Host "Exported library clip files to $exportDir"
