# Employee Asset Management Register

Dashboard UI backed by **SQLite** (`data/assets.db`) and optional **GitHub Actions** to refresh `static/dashboard-data.json`.

Repo: [github.com/bigb787/Employee_Asset_Management_Register](https://github.com/bigb787/Employee_Asset_Management_Register)

## Dashboard (SQLite + JSON export)

- **Schema:** `data/schema.sql` — table `assets` with `category`: `employee_assets`, `internal_assets`, `external_assets`, `cloud_assets`, `admin_assets` (chips: **Employee_Assets**, **Internal Assets**, **External Assets**, **Cloud_Assets**, **Admin_Assets**).
- **Build JSON:** from repo root run  
  `python scripts/build_dashboard_data.py`  
  (creates/updates `data/assets.db` with demo rows if empty, writes `static/dashboard-data.json`).
- **GitHub Actions:** `.github/workflows/build-dashboard.yml` runs the same script on pushes that touch `data/`, the script, or `app/dashboard_json.py`, then commits updated JSON (and DB if new).

## Run API + UI locally

```bash
pip install -r requirements.txt
python -c "from app.database import init_db; init_db()"
python scripts/build_dashboard_data.py
```

Start the server (use **`python -m uvicorn`** on Windows if the `uvicorn` command is not found):

```bash
# Linux / macOS, or Windows when Scripts is on PATH:
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

From the **project root**, set `PYTHONPATH` to the current folder if imports fail:

**PowerShell:** `$env:PYTHONPATH = (Get-Location).Path`  
Then: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

Or run: **`.\run.ps1`**

Open **http://127.0.0.1:8000/** — data loads from **`/api/dashboard-data`** (live SQLite) with fallback to **`/static/dashboard-data.json`**.

- **Export all:** button calls **`/api/assets/export.csv`**.
- **+ Add asset:** placeholder until you add a form/API.

## Editing data

- Use any SQLite tool on **`data/assets.db`**, or add SQL migrations, then run **`python scripts/build_dashboard_data.py`** (or push to `main` to let Actions run).
