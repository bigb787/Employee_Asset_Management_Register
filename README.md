# Employee Asset Management Register

Dashboard UI backed by **SQLite** (`data/assets.db`) and optional **GitHub Actions** to refresh `static/dashboard-data.json`.

Repo: [github.com/bigb787/Employee_Asset_Management_Register](https://github.com/bigb787/Employee_Asset_Management_Register)

## Dashboard (SQLite + JSON export)

- **Schema:** `data/schema.sql` — table `assets` with `category` values aligned to dashboard chips (see `eamr/dashboard_json.py` `CATEGORIES_META`): **Employee_Assets**, **Internal Assets**, **External Assets**, **Cloud_Assets**, **Admin_Assets**, **GatePass**, **InfoDesk_Leavers**.
- **Build JSON:** from repo root run  
  `python scripts/build_dashboard_data.py`  
  (creates/updates `data/assets.db` with demo rows if empty, writes `static/dashboard-data.json`).
- **GitHub Actions:** `.github/workflows/build-dashboard.yml` runs the same script on pushes that touch `data/`, the script, or `eamr/dashboard_json.py`, then commits updated JSON (and DB if new).

## Run API + UI locally

```bash
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
python scripts/build_dashboard_data.py
```

**Windows:** the `uvicorn` command is often not on your PATH. Use one of these from the **project root** instead:

- **PowerShell:** `.\run.ps1`
- **Command Prompt:** `run.bat`
- **Either shell:** `python -m uvicorn eamr.main:app --host 0.0.0.0 --port 8000 --reload`  
  (if `ModuleNotFoundError: uvicorn`, run `pip install -r requirements.txt` first)

**Linux / macOS** (or Windows when `Scripts` is on PATH):

```bash
python -m uvicorn eamr.main:app --reload --host 127.0.0.1 --port 8000
```

If imports fail, set `PYTHONPATH` to the project root. **PowerShell:**  
`$env:PYTHONPATH = (Get-Location).Path` then run the `python -m uvicorn` line above.

Open **http://127.0.0.1:8000/** — data loads from **`/api/dashboard-data`** (live SQLite) with fallback to **`/static/dashboard-data.json`**.

- **Export all:** button calls **`/api/assets/export.csv`**.
- **+ Add asset:** placeholder until you add a form/API.

## Editing data

- Use any SQLite tool on **`data/assets.db`**, or add SQL migrations, then run **`python scripts/build_dashboard_data.py`** (or push to `main` to let Actions run).
