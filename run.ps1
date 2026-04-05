# Start dashboard API from project root (Windows)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = (Get-Location).Path
Write-Host "Open http://127.0.0.1:8000/  (Ctrl+C to stop)"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
