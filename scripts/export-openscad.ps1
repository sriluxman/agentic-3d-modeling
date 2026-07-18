$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$openscad = "C:\Program Files\OpenSCAD\openscad.exe"
$model = Join-Path $root "models\snapfit_pair.scad"
$exportDir = Join-Path $root "exports"

New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

& $openscad -o (Join-Path $exportDir "snapfit_plug.stl") -D "part_id=1" $model
& $openscad -o (Join-Path $exportDir "snapfit_socket.stl") -D "part_id=2" $model
& $openscad -o (Join-Path $exportDir "snapfit_both_preview.png") --imgsize=1400,700 --viewall -D "part_id=0" $model

Write-Host "Exported snap-fit files to $exportDir"
