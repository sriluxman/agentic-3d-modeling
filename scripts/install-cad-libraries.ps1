$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$installRoot = Join-Path $root ".cad-libs"
$bosl2 = Join-Path $installRoot "BOSL2"
$commit = "881947c32a28fa68049b518dcc1e73202bfc2c7c"

New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $bosl2 ".git"))) {
    git clone --filter=blob:none --no-checkout https://github.com/BelfrySCAD/BOSL2.git $bosl2
    if ($LASTEXITCODE -ne 0) { throw "Failed to clone BOSL2" }
}

$actual = git -C $bosl2 rev-parse HEAD 2>$null
if ($actual.Trim() -ne $commit) {
    git -C $bosl2 fetch --depth 1 origin $commit
    if ($LASTEXITCODE -ne 0) { throw "Failed to fetch pinned BOSL2 commit" }
    git -C $bosl2 checkout --detach $commit
    if ($LASTEXITCODE -ne 0) { throw "Failed to check out pinned BOSL2 commit" }
}

$actual = git -C $bosl2 rev-parse HEAD
if ($actual.Trim() -ne $commit) { throw "BOSL2 checkout does not match lock file" }
Write-Host "BOSL2 ready at $bosl2 ($commit)"
