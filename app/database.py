import os
import json
import aiosqlite
import boto3
from datetime import datetime, date
from typing import Any, Optional

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/assets.db")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
AWS_REGION     = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
AWS_PROFILE    = os.getenv("AWS_PROFILE", "my-asset-project")

# Locations allowed throughout the application
LOCATIONS = ["India", "US", "UK", "Sweden"]

# Whitelisted table names (prevents SQL-injection via table parameter)
ALLOWED_TABLES = {
    "laptops", "desktops", "monitors", "accessories",
    "networking", "cloud_assets", "infodesk_applications",
    "third_party_software", "ups", "mobile_phones",
    "scanners_printers", "cameras_dvr", "gatepass",
    "leavers_checklist", "audit_log",
}

# ---------------------------------------------------------------------------
# DDL — all tables
# ---------------------------------------------------------------------------
_DDL = """
CREATE TABLE IF NOT EXISTS laptops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT DEFAULT 'Laptop',
  asset_manufacturer TEXT,
  service_tag TEXT UNIQUE,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT DEFAULT 'Active',
  last_owner TEXT,
  dept TEXT,
  location TEXT,
  asset_health TEXT DEFAULT 'Good',
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  processor TEXT,
  ram TEXT,
  hard_disk TEXT,
  os TEXT,
  supt_vendor TEXT,
  keyboard TEXT,
  mouse TEXT,
  headphone TEXT,
  usb_extender TEXT,
  contains_pii TEXT DEFAULT 'No',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS desktops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT DEFAULT 'Desktop',
  asset_manufacturer TEXT,
  service_tag TEXT UNIQUE,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT DEFAULT 'Active',
  last_owner TEXT,
  dept TEXT,
  location TEXT,
  asset_health TEXT DEFAULT 'Good',
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  processor TEXT,
  os TEXT,
  supt_vendor TEXT,
  configuration TEXT,
  contains_pii TEXT DEFAULT 'No',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS monitors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT DEFAULT 'Monitor',
  asset_manufacturer TEXT,
  service_tag TEXT,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT DEFAULT 'Active',
  dept TEXT,
  location TEXT,
  asset_health TEXT DEFAULT 'Good',
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  supt_vendor TEXT,
  contains_pii TEXT DEFAULT 'No',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS accessories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  asset_manufacturer TEXT,
  model TEXT,
  pn TEXT,
  asset_owner TEXT,
  assigned_to TEXT,
  asset_status TEXT DEFAULT 'Active',
  dept TEXT,
  location TEXT,
  warranty TEXT,
  install_date TEXT,
  date_added_updated TEXT,
  supt_vendor TEXT,
  linked_device_tag TEXT,
  contains_pii TEXT DEFAULT 'No',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS networking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  asset_id TEXT,
  mac_id TEXT,
  asset_owner TEXT,
  location TEXT,
  model TEXT,
  sn TEXT,
  pn TEXT,
  warranty TEXT,
  install_date TEXT,
  os TEXT,
  supt_vendor TEXT,
  dept TEXT,
  configuration TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS cloud_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii TEXT DEFAULT 'No',
  asset_region TEXT,
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS infodesk_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS third_party_software (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  cve_alert TEXT DEFAULT 'None',
  setup TEXT,
  billing_api TEXT,
  patch_status TEXT DEFAULT 'Up to date',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS ups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT DEFAULT 'UPS',
  device_id TEXT,
  location TEXT,
  model TEXT,
  warranty TEXT,
  install_date TEXT,
  supt_vendor TEXT,
  dept TEXT,
  asset_owner TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS mobile_phones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT DEFAULT 'Mobile Phone',
  device_id TEXT,
  location TEXT,
  model TEXT,
  pn TEXT,
  warranty TEXT,
  supt_vendor TEXT,
  dept TEXT,
  asset_owner TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS scanners_printers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  device_id TEXT,
  location TEXT,
  model TEXT,
  service_tag TEXT,
  pn TEXT,
  warranty TEXT,
  supt_vendor TEXT,
  dept TEXT,
  description TEXT,
  asset_owner TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS cameras_dvr (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT,
  location TEXT,
  invoice_no TEXT,
  warranty TEXT,
  install_date TEXT,
  supt_vendor TEXT,
  dept TEXT,
  asset_owner TEXT,
  contains_pii TEXT DEFAULT 'Yes',
  date_added_updated TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS gatepass (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gatepass_no TEXT UNIQUE NOT NULL,
  gatepass_date TEXT,
  pass_type TEXT DEFAULT 'Returnable',
  issued_to TEXT,
  person TEXT,
  dept_head TEXT,
  security_guard TEXT,
  receiver_name TEXT,
  asset_items TEXT,
  expected_return_date TEXT,
  actual_return_date TEXT,
  status TEXT DEFAULT 'Open',
  remarks TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS leavers_checklist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_name TEXT NOT NULL,
  date_of_leaving TEXT,
  department TEXT,
  line_manager TEXT,
  email_address TEXT,
  email_groups TEXT DEFAULT 'Active',
  infodesk_qa_dev TEXT DEFAULT 'Active',
  infodesk_prod TEXT DEFAULT 'Active',
  jira_and_wiki TEXT DEFAULT 'Active',
  ms_office TEXT DEFAULT 'Active',
  mongo_access TEXT DEFAULT 'Active',
  azure_infodesk TEXT DEFAULT 'Active',
  azure_wn_infodesk TEXT DEFAULT 'Active',
  vpn TEXT DEFAULT 'Active',
  wn_vpn TEXT DEFAULT 'Active',
  azure_devops TEXT DEFAULT 'Active',
  info_admin TEXT DEFAULT 'Active',
  zabbix TEXT DEFAULT 'Active',
  github TEXT DEFAULT 'Active',
  infodesk_portal TEXT DEFAULT 'Active',
  salesforce TEXT DEFAULT 'Active',
  hw_inventory_location TEXT,
  hw_handed_over TEXT DEFAULT 'Pending',
  evidence_file_name TEXT,
  evidence_file_s3_key TEXT,
  evidence_file_url TEXT,
  evidence_uploaded_at DATETIME,
  evidence_uploaded_by TEXT,
  it_peer_review TEXT DEFAULT 'Pending',
  it_peer_reviewer TEXT,
  it_peer_review_date TEXT,
  reporting_manager TEXT DEFAULT 'Pending',
  reporting_manager_name TEXT,
  reporting_manager_date TEXT,
  confirmation_audit TEXT DEFAULT 'Pending',
  confirmation_audit_by TEXT,
  confirmation_audit_date TEXT,
  communication_github_ticket TEXT,
  overall_status TEXT DEFAULT 'In Progress',
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  table_name TEXT,
  record_id INTEGER,
  action TEXT,
  changed_fields TEXT,
  old_values TEXT,
  new_values TEXT,
  performed_by TEXT,
  performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  ip_address TEXT
);
"""


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------
async def init_db() -> None:
    os.makedirs(os.path.dirname(DATABASE_PATH) or "data", exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for statement in _DDL.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                await db.execute(stmt)
        await db.commit()


# ---------------------------------------------------------------------------
# Generic CRUD helpers
# ---------------------------------------------------------------------------
def _check_table(table: str) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Table '{table}' is not allowed.")


async def get_all(table: str, filters: Optional[dict] = None) -> list[dict]:
    _check_table(table)
    query = f"SELECT * FROM {table}"
    params: list[Any] = []
    if filters:
        clauses = [f"{k} = ?" for k in filters]
        query += " WHERE " + " AND ".join(clauses)
        params = list(filters.values())
    query += " ORDER BY id DESC"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_by_id(table: str, record_id: int) -> Optional[dict]:
    _check_table(table)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT * FROM {table} WHERE id = ?", (record_id,)
        ) as cur:
            row = await cur.fetchone()
    return dict(row) if row else None


async def create(
    table: str,
    data: dict,
    performed_by: str = "system",
    ip_address: str = "",
) -> int:
    _check_table(table)
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    data.setdefault("created_by", performed_by)
    data.setdefault("updated_by", performed_by)

    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            list(data.values()),
        )
        await db.commit()
        new_id = cur.lastrowid

    await log_audit(
        table=table,
        record_id=new_id,
        action="CREATE",
        old_values=None,
        new_values=data,
        performed_by=performed_by,
        ip_address=ip_address,
    )
    return new_id


async def update(
    table: str,
    record_id: int,
    data: dict,
    performed_by: str = "system",
    ip_address: str = "",
) -> bool:
    _check_table(table)
    old = await get_by_id(table, record_id)
    if old is None:
        return False

    data["updated_at"] = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    data["updated_by"] = performed_by

    set_clause = ", ".join(f"{k} = ?" for k in data)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE {table} SET {set_clause} WHERE id = ?",
            [*data.values(), record_id],
        )
        await db.commit()

    changed = {k: v for k, v in data.items() if old.get(k) != v}
    await log_audit(
        table=table,
        record_id=record_id,
        action="UPDATE",
        old_values={k: old.get(k) for k in changed},
        new_values=changed,
        performed_by=performed_by,
        ip_address=ip_address,
    )
    return True


async def delete(
    table: str,
    record_id: int,
    performed_by: str = "system",
    ip_address: str = "",
) -> bool:
    _check_table(table)
    old = await get_by_id(table, record_id)
    if old is None:
        return False

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        await db.commit()

    await log_audit(
        table=table,
        record_id=record_id,
        action="DELETE",
        old_values=old,
        new_values=None,
        performed_by=performed_by,
        ip_address=ip_address,
    )
    return True


async def get_count(table: str) -> int:
    _check_table(table)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(f"SELECT COUNT(*) FROM {table}") as cur:
            row = await cur.fetchone()
    return row[0] if row else 0


async def get_all_stats() -> dict:
    tables = list(ALLOWED_TABLES - {"audit_log"})
    stats: dict[str, int] = {}
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for t in tables:
            async with db.execute(f"SELECT COUNT(*) FROM {t}") as cur:
                row = await cur.fetchone()
            stats[t] = row[0] if row else 0
    return stats


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------
async def log_audit(
    table: str,
    record_id: Optional[int],
    action: str,
    old_values: Optional[dict],
    new_values: Optional[dict],
    performed_by: str,
    ip_address: str,
) -> None:
    changed_fields = None
    if old_values and new_values:
        changed_fields = json.dumps(list(new_values.keys()))

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO audit_log
               (table_name, record_id, action, changed_fields,
                old_values, new_values, performed_by, ip_address)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                table,
                record_id,
                action,
                changed_fields,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values, default=str) if new_values else None,
                performed_by,
                ip_address,
            ),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Gatepass number generator  GP-YYYYMMDD-001
# ---------------------------------------------------------------------------
async def generate_gatepass_no() -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"GP-{today}-"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT gatepass_no FROM gatepass WHERE gatepass_no LIKE ? ORDER BY id DESC LIMIT 1",
            (f"{prefix}%",),
        ) as cur:
            row = await cur.fetchone()
    if row:
        last_seq = int(row[0].split("-")[-1])
        seq = last_seq + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


# ---------------------------------------------------------------------------
# S3 helpers  (profile: my-asset-project, no hardcoded credentials)
# ---------------------------------------------------------------------------
def get_s3_client():
    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client("s3", region_name=AWS_REGION)


async def upload_evidence_to_s3(
    file_bytes: bytes,
    s3_key: str,
    content_type: str,
) -> str:
    client = get_s3_client()
    client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
        ServerSideEncryption="AES256",
    )
    return s3_key


async def get_presigned_url(s3_key: str, expiry: int = 3600) -> str:
    client = get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry,
    )
    return url
