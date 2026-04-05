@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
echo Open http://127.0.0.1:8000/  (Ctrl+C to stop)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
