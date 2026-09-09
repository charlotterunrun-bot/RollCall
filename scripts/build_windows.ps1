$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$pythonPath = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = (Get-Command python).Source }
& $pythonPath -m PyInstaller --noconfirm --clean RollCall.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$source = Join-Path $root 'dist\RollCall.exe'
$asset = Join-Path $root 'dist\RollCall-2.0.0-Windows-x64.exe'
Copy-Item -LiteralPath $source -Destination $asset -Force
Get-FileHash -Algorithm SHA256 -LiteralPath $asset
