# Employee Asset Management Register

Internal **ISO 27001–aligned** asset register for laptops through cameras/DVR, **gate pass** (A.5.11), and **IT exit / leavers** checklists (A.6.5, A.5.11). Single-page UI, SQLite, optional S3 for evidence and backups, deployable on **AWS EC2** behind nginx.

**Repository:** [github.com/bigb787/Employee_Asset_Management_Register](https://github.com/bigb787/Employee_Asset_Management_Register)

---

## Features

- **12 asset tabs** with CRUD, filters (including country group **India / US / UK / Sweden** from `Country — City` location values), and exports.
- **Gate pass:** JSON line items, PDF (A5), Excel export with status colouring (Open / Closed / Cancelled).
- **Leavers:** Full checklist, S3 evidence upload, PDF clearance, Excel summary + per-system sheet with conditional formatting.
- **Audit log** API (who/when/IP on mutations) and **ISO summary** export row in the master Excel.
- **No** ISO “tips” or badge tooltips in the UI (compliance is in exports, PDFs, and server-side reporting).

---

## Local development

**Requirements:** Python 3.10+ (3.11 matches CI).

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # edit AWS/SECRET_KEY as needed
mkdir -p data
python -c "from app.database import init_db; init_db()"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000` (UI) or `http://127.0.0.1:8000/docs` (OpenAPI).

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `AWS_PROFILE` | Named profile for local AWS CLI / boto3 (omit on EC2 if using instance role). |
| `AWS_REGION` | Region for S3 and clients. |
| `S3_BUCKET_NAME` | Bucket for leaver evidence and DB backups (must match Terraform). |
| `DATABASE_PATH` | SQLite file path (default `data/assets.db`). |
| `APP_HOST` / `APP_PORT` | Bind address/port for uvicorn (systemd uses 8000). |
| `ENVIRONMENT` | e.g. `production`. |
| `SECRET_KEY` | Set a long random string in production. |

---

## Project layout

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app, routes, CORS, static, audit middleware. |
| `app/database.py` | Schema, CRUD, audit log, S3 helpers, gate pass number generation. |
| `app/utils/pdf_generator.py` | **Step 5:** Gate pass PDF (A5), IT exit PDF (A4). |
| `app/utils/excel_exporter.py` | **Step 6:** Master ISO workbook, gate pass & leavers exports. |
| `app/utils/iso_audit.py` | **Step 7:** `ISO_CONTROLS` map and `generate_iso_report()`. |
| `app/routers/` | Optional split (not required; all routes are wired from `main.py`). |
| `templates/` / `static/` | UI. |
| `terraform/` | EC2, EIP, SG, IAM, S3 (versioning, encryption, lifecycle, **public access block**). |
| `scripts/` | `backup.sh`, `restore.sh`, `healthcheck.sh`. |
| `asset-register.service` | systemd unit. |
| `nginx.conf` | Reverse proxy to uvicorn, static cache. |
| `.github/workflows/deploy.yml` | CI tests on push; **deploy** on `workflow_dispatch` when EC2 secrets exist. |
| `deploy.sh` | Manual `local` / `remote` deploy helper. |

### Dependencies (**Step 8**)

Pinned in `requirements.txt`: FastAPI, uvicorn, python-multipart, python-dotenv, boto3, openpyxl, reportlab, jinja2, aiofiles.

---

## PDF exports (**Step 5**)

- **`generate_gatepass_pdf(data)`** — A5, InfoDesk header, centred “GATE PASS”, pass type, issued-to block, **6-row** items table (Sr.No, Description, Unit, Qty, Remarks), signature lines, footer with ISO **A.5.11** and timestamp.
- **`generate_it_exit_pdf(leaver, checklist)`** — A4, three sections (system access table, hardware/evidence, sign-offs), completion %, confidential footer (**A.6.5**).

---

## Excel exports (**Step 6**)

- **`export_all_assets`** — Sheet **ISO Summary** first (table name, control ref, totals, PII, confidential, last updated + country breakdown), then asset sheets in fixed order (**Laptops** … **Cameras and DVR**). Header fill `#185FA5`, white bold text, zebra rows `#F5F5F5`. Filename: `ISO27001_Asset_Register_YYYY-MM-DD.xlsx`.
- **`export_gatepass`** — Status column colours (Open / Closed / Cancelled). Filename: `Gatepass_Export_YYYY-MM-DD.xlsx`.
- **`export_leavers`** — **Leavers Summary**, **System Access Status** with per-cell styling for Revoked / Active / N/A, completion %, summary row. Filename: `IT_Exit_Checklist_Export_YYYY-MM-DD.xlsx`.

---

## ISO audit helper (**Step 7**)

`generate_iso_report()` returns counts per table (totals, PII, confidential, missing owner/location), `country_breakdown`, `compliance_gaps` (human-readable strings), and `iso_controls` (full map including gatepass and leavers).

---

## AWS Terraform (**Step 10**)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Default region in code is ap-south-1 (Mumbai). Override aws_region in tfvars if needed.
# Edit: aws_profile, public_key_path, s3_bucket_name, etc.

terraform init
terraform plan
terraform apply
```

Outputs include **Elastic IP**, **S3 bucket**, **SSH command**, and app URL. The S3 bucket uses SSE-S3 encryption and **block all public access** (no Terraform-managed versioning or lifecycle; optional pruning remains in `scripts/backup.sh`).

**Security note:** The default security group allows **0.0.0.0/0** on 22/80/443. Restrict SSH to your IP in production.

---

## GitHub Actions (**Step 11**)

- **On push to `main`:** checkout, Python 3.11, `pip install -r requirements.txt`, import/smoke checks for app, DB, Excel, PDF, and ISO report.
- **Deploy job:** runs only on **`workflow_dispatch`** so pushes do not fail when `EC2_*` secrets are missing.

Configure secrets (repo → Settings → Secrets):

- `EC2_HOST` — public IP (EIP).
- `EC2_USER` — e.g. `ubuntu`.
- `EC2_SSH_KEY` — private key PEM contents.

Then run **Actions → CI and deploy → Run workflow**.

---

## EC2 operations (**Steps 12–15**)

First boot runs `terraform/user_data.sh`: clone/pull repo, venv, `init_db`, systemd, nginx, cron for **daily backup** (02:00) and **health check** (every 5 minutes).

| Script | Role |
|--------|------|
| `scripts/backup.sh` | Uploads `data/assets.db` to `s3://$S3_BUCKET_NAME/backups/`; prunes old objects (reads `.env` for bucket). |
| `scripts/restore.sh` | Interactive restore from S3; backs up current DB locally; restarts app. |
| `scripts/healthcheck.sh` | Hits `/api/stats`; restarts service if not HTTP 200. |

**systemd** (`asset-register.service`): `User=ubuntu`, `WorkingDirectory` and `EnvironmentFile` pointing at the repo, **4 uvicorn workers**.

**nginx:** proxies `/` to `127.0.0.1:8000`, serves `/static/` from the repo with cache headers, **10M** upload limit.

---

## Manual deploy (`deploy.sh`)

On the server (from repo root):

```bash
chmod +x deploy.sh
./deploy.sh local
```

From your machine:

```bash
./deploy.sh remote ubuntu@YOUR_EIP ~/.ssh/your-key.pem
# or: export EC2_SSH_KEY=~/.ssh/your-key.pem && ./deploy.sh remote ubuntu@YOUR_EIP
```

---

## `.gitignore` (**Step 15**)

Ignores `.env`, SQLite files, `venv`, keys (`.pem`, `.key`, `.pub`), Terraform state and `.terraform/`, `*.tfvars`, local `backups/`, generated `*.xlsx` / `*.pdf`, logs, and OS junk.

---

## API overview

JSON under `/api/…` for CRUD per table, `/api/stats`, exports (`/api/export/...`), gate pass and leavers PDFs, audit log pagination, presigned upload URL for leaver evidence, and `GET /api/gatepass/next-number`. See OpenAPI at `/docs`.

---

## Licence / use

Internal tooling for InfoDesk-style asset and exit processes; adapt governance text and bucket names to your organisation before production use.
