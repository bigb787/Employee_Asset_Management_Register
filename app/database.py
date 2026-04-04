"""
SQLite database layer: schema, CRUD, audit logging, gatepass numbers, S3 helpers.
Uses parameterized queries only. AWS: profile my-aws-project (override via AWS_PROFILE).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "assets.db"

VALID_TABLES = frozenset(
    {
        "laptops",
        "desktops",
        "monitors",
        "accessories",
        "networking",
        "cloud_assets",
        "infodesk_applications",
        "third_party_software",
        "ups",
        "mobile_phones",
        "scanners_printers",
        "cameras_dvr",
        "gatepass",
        "leavers_checklist",
        "audit_log",
    }
)

# Writable columns per table (excludes id; timestamps managed in SQL where noted).
TABLE_WRITABLE_COLUMNS: dict[str, frozenset[str]] = {
    "laptops": frozenset(
        {
            "asset_type",
            "asset_manufacturer",
            "service_tag",
            "model",
            "pn",
            "asset_owner",
            "assigned_to",
            "asset_status",
            "last_owner",
            "dept",
            "location",
            "asset_health",
            "warranty",
            "install_date",
            "date_added_updated",
            "processor",
            "ram",
            "hard_disk",
            "os",
            "supt_vendor",
            "keyboard",
            "mouse",
            "headphone",
            "usb_extender",
            "contains_pii",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "desktops": frozenset(
        {
            "asset_type",
            "asset_manufacturer",
            "service_tag",
            "model",
            "pn",
            "asset_owner",
            "assigned_to",
            "asset_status",
            "last_owner",
            "dept",
            "location",
            "asset_health",
            "warranty",
            "install_date",
            "date_added_updated",
            "processor",
            "os",
            "supt_vendor",
            "configuration",
            "contains_pii",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "monitors": frozenset(
        {
            "asset_type",
            "asset_manufacturer",
            "service_tag",
            "model",
            "pn",
            "asset_owner",
            "assigned_to",
            "asset_status",
            "dept",
            "location",
            "asset_health",
            "warranty",
            "install_date",
            "date_added_updated",
            "supt_vendor",
            "contains_pii",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "accessories": frozenset(
        {
            "asset_type",
            "asset_manufacturer",
            "model",
            "pn",
            "asset_owner",
            "assigned_to",
            "asset_status",
            "dept",
            "location",
            "warranty",
            "install_date",
            "date_added_updated",
            "supt_vendor",
            "linked_device_tag",
            "contains_pii",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "networking": frozenset(
        {
            "asset_type",
            "asset_id",
            "mac_id",
            "asset_owner",
            "location",
            "model",
            "sn",
            "pn",
            "warranty",
            "install_date",
            "os",
            "supt_vendor",
            "dept",
            "configuration",
            "contains_pii",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "cloud_assets": frozenset(
        {
            "asset",
            "asset_type",
            "asset_value",
            "asset_owner",
            "asset_location",
            "contains_pii",
            "asset_region",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "infodesk_applications": frozenset(
        {
            "asset",
            "asset_type",
            "asset_value",
            "asset_owner",
            "asset_location",
            "contains_pii",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "third_party_software": frozenset(
        {
            "asset",
            "asset_type",
            "asset_value",
            "asset_owner",
            "asset_location",
            "contains_pii",
            "date_added_updated",
            "cve_alert",
            "setup",
            "billing_api",
            "patch_status",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "ups": frozenset(
        {
            "asset_type",
            "device_id",
            "location",
            "model",
            "warranty",
            "install_date",
            "supt_vendor",
            "dept",
            "asset_owner",
            "contains_pii",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "mobile_phones": frozenset(
        {
            "asset_type",
            "device_id",
            "location",
            "model",
            "pn",
            "warranty",
            "supt_vendor",
            "dept",
            "asset_owner",
            "contains_pii",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "scanners_printers": frozenset(
        {
            "asset_type",
            "device_id",
            "location",
            "model",
            "service_tag",
            "pn",
            "warranty",
            "supt_vendor",
            "dept",
            "description",
            "asset_owner",
            "contains_pii",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "cameras_dvr": frozenset(
        {
            "asset_type",
            "location",
            "invoice_no",
            "warranty",
            "install_date",
            "supt_vendor",
            "dept",
            "asset_owner",
            "contains_pii",
            "date_added_updated",
            "iso_classification",
            "created_by",
            "updated_by",
        }
    ),
    "gatepass": frozenset(
        {
            "gatepass_no",
            "gatepass_date",
            "pass_type",
            "issued_to",
            "person",
            "dept_head",
            "security_guard",
            "receiver_name",
            "asset_items",
            "expected_return_date",
            "actual_return_date",
            "status",
            "remarks",
            "iso_ref",
            "created_by",
            "updated_by",
        }
    ),
    "leavers_checklist": frozenset(
        {
            "employee_name",
            "date_of_leaving",
            "department",
            "line_manager",
            "email_address",
            "email_groups",
            "infodesk_qa_dev",
            "infodesk_prod",
            "jira_and_wiki",
            "ms_office",
            "mongo_access",
            "azure_infodesk",
            "azure_wn_infodesk",
            "vpn",
            "wn_vpn",
            "azure_devops",
            "info_admin",
            "zabbix",
            "github",
            "infodesk_portal",
            "salesforce",
            "hw_inventory_location",
            "hw_handed_over",
            "evidence_file_name",
            "evidence_file_s3_key",
            "evidence_file_url",
            "evidence_uploaded_at",
            "evidence_uploaded_by",
            "it_peer_review",
            "it_peer_reviewer",
            "it_peer_review_date",
            "reporting_manager",
            "reporting_manager_name",
            "reporting_manager_date",
            "confirmation_audit",
            "confirmation_audit_by",
            "confirmation_audit_date",
            "communication_github_ticket",
            "overall_status",
            "notes",
            "iso_ref",
            "created_by",
            "updated_by",
        }
    ),
    "audit_log": frozenset(
        {
            "table_name",
            "record_id",
            "action",
            "changed_fields",
            "old_values",
            "new_values",
            "performed_by",
            "ip_address",
            "iso_ref",
        }
    ),
}

DDL_STATEMENTS = [
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Confidential',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Confidential',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
CREATE TABLE IF NOT EXISTS infodesk_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT,
  asset_type TEXT,
  asset_value TEXT,
  asset_owner TEXT,
  asset_location TEXT,
  contains_pii TEXT DEFAULT 'No',
  date_added_updated TEXT,
  iso_classification TEXT DEFAULT 'Confidential',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Confidential',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Internal',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_classification TEXT DEFAULT 'Confidential',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_ref TEXT DEFAULT 'A.5.11',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  iso_ref TEXT DEFAULT 'A.6.5, A.5.11, A.8.1',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  updated_by TEXT
);
""",
    """
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
  ip_address TEXT,
  iso_ref TEXT
);
""",
]


def get_db_path() -> Path:
    raw = os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH))
    p = Path(raw)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def _validate_table(table: str) -> None:
    if table not in VALID_TABLES:
        raise ValueError(f"Invalid table: {table}")


def _filter_payload(table: str, data: dict[str, Any]) -> dict[str, Any]:
    allowed = TABLE_WRITABLE_COLUMNS[table]
    return {k: data[k] for k in data if k in allowed}


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _serialize_row(d: Optional[dict[str, Any]]) -> str:
    if not d:
        return "{}"
    return json.dumps({k: _json_safe(v) for k, v in d.items()}, default=str)


def init_db() -> None:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    try:
        for stmt in DDL_STATEMENTS:
            conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


def log_audit(
    table: str,
    record_id: int,
    action: str,
    old_values: Optional[dict[str, Any]],
    new_values: Optional[dict[str, Any]],
    performed_by: Optional[str],
    ip_address: Optional[str],
    iso_ref: Optional[str],
    changed_fields: Optional[list[str]] = None,
) -> None:
    """Insert a row into audit_log (direct SQL; does not recurse through create())."""
    cf = json.dumps(changed_fields) if changed_fields is not None else None
    sql = """
    INSERT INTO audit_log (
      table_name, record_id, action, changed_fields, old_values, new_values,
      performed_by, ip_address, iso_ref
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        conn = _connect()
        try:
            conn.execute(
                sql,
                (
                    table,
                    record_id,
                    action,
                    cf,
                    _serialize_row(old_values) if old_values is not None else None,
                    _serialize_row(new_values) if new_values is not None else None,
                    performed_by,
                    ip_address,
                    iso_ref,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error:
        raise


def get_all(table: str) -> list[dict[str, Any]]:
    _validate_table(table)
    try:
        conn = _connect()
        try:
            cur = conn.execute(f"SELECT * FROM {table}")
            return [_row_to_dict(r) or {} for r in cur.fetchall()]
        finally:
            conn.close()
    except sqlite3.Error:
        raise


def get_by_id(table: str, row_id: int) -> Optional[dict[str, Any]]:
    _validate_table(table)
    try:
        conn = _connect()
        try:
            cur = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
            return _row_to_dict(cur.fetchone())
        finally:
            conn.close()
    except sqlite3.Error:
        raise


def create(table: str, data: dict[str, Any], *, client_ip: Optional[str] = None) -> int:
    _validate_table(table)
    payload = _filter_payload(table, data)
    cols = list(payload.keys())
    if not cols:
        raise ValueError("No valid fields to insert")
    placeholders = ", ".join("?" * len(cols))
    col_sql = ", ".join(cols)
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
    try:
        conn = _connect()
        try:
            cur = conn.execute(sql, [payload[c] for c in cols])
            conn.commit()
            new_id = int(cur.lastrowid)
        finally:
            conn.close()
    except sqlite3.Error:
        raise

    if table != "audit_log":
        new_row = get_by_id(table, new_id)
        log_audit(
            table,
            new_id,
            "CREATE",
            None,
            new_row,
            performed_by=payload.get("created_by") or payload.get("updated_by"),
            ip_address=client_ip,
            iso_ref=payload.get("iso_ref"),
            changed_fields=list(payload.keys()),
        )
    return new_id


def update(
    table: str, row_id: int, data: dict[str, Any], *, client_ip: Optional[str] = None
) -> bool:
    _validate_table(table)
    old = get_by_id(table, row_id)
    if old is None:
        return False
    payload = _filter_payload(table, data)
    if not payload:
        return True
    if table != "audit_log":
        payload = {k: v for k, v in payload.items() if k not in ("created_at",)}
    set_parts = [f"{c} = ?" for c in payload]
    values = [payload[c] for c in payload]
    values.append(row_id)
    sql = f"UPDATE {table} SET {', '.join(set_parts)}, updated_at = datetime('now') WHERE id = ?"
    if table == "audit_log":
        sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE id = ?"
    try:
        conn = _connect()
        try:
            cur = conn.execute(sql, values)
            conn.commit()
            updated = cur.rowcount > 0
        finally:
            conn.close()
    except sqlite3.Error:
        raise

    if updated and table != "audit_log":
        new_row = get_by_id(table, row_id)
        old_sub = {k: old[k] for k in payload if k in old.keys()}
        new_sub = {k: new_row[k] for k in payload if new_row and k in new_row.keys()}
        changed = [
            k
            for k in payload
            if new_row is not None and old.get(k) != new_row.get(k)
        ]
        log_audit(
            table,
            row_id,
            "UPDATE",
            old_sub,
            new_sub,
            performed_by=payload.get("updated_by") or payload.get("created_by") or old.get("updated_by"),
            ip_address=client_ip,
            iso_ref=payload.get("iso_ref") or (old.get("iso_ref") if isinstance(old.get("iso_ref"), str) else None),
            changed_fields=changed,
        )
    return updated


def delete(table: str, row_id: int, *, client_ip: Optional[str] = None) -> bool:
    _validate_table(table)
    old = get_by_id(table, row_id)
    if old is None:
        return False
    try:
        conn = _connect()
        try:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    except sqlite3.Error:
        raise

    if deleted and table != "audit_log":
        log_audit(
            table,
            row_id,
            "DELETE",
            old,
            None,
            performed_by=old.get("updated_by") or old.get("created_by"),
            ip_address=client_ip,
            iso_ref=old.get("iso_ref") if isinstance(old.get("iso_ref"), str) else None,
            changed_fields=list(old.keys()),
        )
    return deleted


def fetch_audit_log_page(
    *,
    table_name: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Paginated audit_log rows; filters use ISO date strings YYYY-MM-DD. All SQL parameterized."""
    page = max(1, page)
    limit = min(max(1, limit), 500)
    offset = (page - 1) * limit
    where_clauses: list[str] = ["1=1"]
    params: list[Any] = []
    if table_name:
        where_clauses.append("table_name = ?")
        params.append(table_name)
    if from_date:
        where_clauses.append("date(performed_at) >= date(?)")
        params.append(from_date)
    if to_date:
        where_clauses.append("date(performed_at) <= date(?)")
        params.append(to_date)
    where_sql = " AND ".join(where_clauses)
    count_sql = f"SELECT COUNT(*) AS c FROM audit_log WHERE {where_sql}"
    data_sql = f"""
    SELECT * FROM audit_log WHERE {where_sql}
    ORDER BY performed_at DESC, id DESC
    LIMIT ? OFFSET ?
    """
    try:
        conn = _connect()
        try:
            cur = conn.execute(count_sql, params)
            total = int(cur.fetchone()["c"])
            cur = conn.execute(data_sql, params + [limit, offset])
            rows = [_row_to_dict(r) or {} for r in cur.fetchall()]
            return rows, total
        finally:
            conn.close()
    except sqlite3.Error:
        raise


def get_count(table: str) -> int:
    _validate_table(table)
    try:
        conn = _connect()
        try:
            cur = conn.execute(f"SELECT COUNT(*) AS c FROM {table}")
            row = cur.fetchone()
            return int(row["c"]) if row else 0
        finally:
            conn.close()
    except sqlite3.Error:
        raise


def get_all_stats() -> dict[str, int]:
    return {t: get_count(t) for t in sorted(VALID_TABLES)}


def generate_gatepass_no() -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"GP-{today}-"
    try:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                SELECT gatepass_no FROM gatepass
                WHERE gatepass_no LIKE ?
                ORDER BY gatepass_no DESC
                LIMIT 1
                """,
                (prefix + "%",),
            )
            row = cur.fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        raise

    if row is None:
        seq = 1
    else:
        last = row["gatepass_no"]
        suffix = last.split("-")[-1]
        try:
            seq = int(suffix, 10) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:03d}"


def get_s3_client():
    import boto3

    profile = os.getenv("AWS_PROFILE", "my-aws-project")
    region = os.getenv("AWS_REGION", "us-east-1")
    session = boto3.Session(profile_name=profile)
    return session.client("s3", region_name=region)


def upload_evidence_to_s3(
    file_bytes: bytes, s3_key: str, content_type: str
) -> None:
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("S3_BUCKET_NAME is not set")
    try:
        client = get_s3_client()
        client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type or "application/octet-stream",
            ServerSideEncryption="AES256",
        )
    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}") from e


def get_presigned_url(s3_key: str, expiry: int = 3600) -> str:
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("S3_BUCKET_NAME is not set")
    try:
        client = get_s3_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=expiry,
        )
    except Exception as e:
        raise RuntimeError(f"S3 presign failed: {e}") from e
