# Start dashboard API from project root (Windows)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = (Get-Location).Path

$Port = 8000
if ($env:ASSET_REGISTER_PORT) { $Port = [int]$env:ASSET_REGISTER_PORT }

Write-Host "Project: $(Get-Location)"
Write-Host "Checking which Python loads (must show Employee_Assets, GatePass, not Employee devices)..."
python -c "import pathlib; import app.dashboard_json as d; print('  dashboard_json:', pathlib.Path(d.__file__).resolve()); print('  labels:', [x['label'] for x in d.CATEGORIES_META])"

$listen = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listen) {
  Write-Host ""
  Write-Host "WARNING: port $Port is already in use. http://127.0.0.1:$Port/ may be a DIFFERENT old app." -ForegroundColor Yellow
  Write-Host "  Fix: close that terminal, or run:  `$env:ASSET_REGISTER_PORT=8010; .\run.ps1" -ForegroundColor Yellow
  Write-Host ""
}

Write-Host "Open http://127.0.0.1:$Port/  (Ctrl+C to stop)"
Write-Host "On the page you should see a gray line: NEW dashboard ... GatePass ... and chip Employee_Assets (not Employee devices)."
python -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
