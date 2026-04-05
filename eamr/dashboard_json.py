"""Build dashboard JSON payload from SQLite (used by API and build script)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_PATH = DATA_DIR / "schema.sql"

# Chip headers — one chip = one register table (see eamr/register_schema.py)
CATEGORIES_META = [
    {"id": "laptop", "label": "Laptop", "color": "#185FA5"},
    {"id": "desktop", "label": "Desktop", "color": "#1D4ED8"},
    {"id": "monitor", "label": "Monitors", "color": "#2563EB"},
    {"id": "networking", "label": "Networking", "color": "#4B2E83"},
    {"id": "cloud_asset_register", "label": "Cloud Asset Register", "color": "#0F766E"},
    {"id": "infodesk_applications", "label": "Infodesk Applications", "color": "#0369A1"},
    {"id": "third_party_softwares", "label": "Third Party Softwares", "color": "#1E3A5F"},
    {"id": "ups", "label": "UPS", "color": "#9F1239"},
    {"id": "mobile_phones", "label": "Mobile Phones", "color": "#BE123C"},
    {"id": "scanner_and_others", "label": "Scanner and Others", "color": "#A21CAF"},
    {"id": "admin", "label": "Admin", "color": "#8B3A3A"},
    {"id": "gatepass", "label": "GatePass", "color": "#B45309"},
    {"id": "infodesk_leavers", "label": "InfoDesk_Leavers", "color": "#7C3AED"},
]

EXPECTED_CATEGORY_IDS = frozenset(c["id"] for c in CATEGORIES_META)
_LEGACY_CHIP_IDS = frozenset(
    {
        "network",
        "infodesk_apps",
        "third_party",
        "employee_assets",
        "internal_assets",
        "external_assets",
        "cloud_assets",
        "admin_assets",
        "employee_devices",
        "admin_devices",
        "cloud_register",
        "third_party_software",
        "emp_laptop",
        "emp_desktop",
        "emp_monitor",
        "emp_accessory",
        "admin_ups",
        "admin_mobile_phone",
        "admin_scanners_printers",
        "admin_camera",
        "admin_dvr",
    }
)


def verify_categories_meta_or_die() -> None:
    """Fail fast if CATEGORIES_META is wrong (e.g. legacy chip ids mixed in)."""
    got = frozenset(c["id"] for c in CATEGORIES_META)
    if got & _LEGACY_CHIP_IDS:
        bad = sorted(got & _LEGACY_CHIP_IDS)
        raise RuntimeError(
            f"Wrong eamr.dashboard_json: legacy ids {bad!r} must not appear in CATEGORIES_META. "
            f"Loaded from {Path(__file__).resolve()}."
        )
    if got != EXPECTED_CATEGORY_IDS:
        raise RuntimeError(
            f"Wrong CATEGORIES_META ids {sorted(got)!r}; expected {sorted(EXPECTED_CATEGORY_IDS)!r}. "
            f"File: {Path(__file__).resolve()}"
        )


def _sql_category_check_line() -> str:
    inner = ", ".join(f"'{c['id']}'" for c in CATEGORIES_META)
    return f"category TEXT NOT NULL CHECK (category IN ({inner}))"


def _category_map_case_sql() -> str:
    """Map old category values to current CATEGORIES_META ids."""
    return """CASE category
        WHEN 'employee_assets' THEN 'laptop'
        WHEN 'employee_devices' THEN 'laptop'
        WHEN 'emp_laptop' THEN 'laptop'
        WHEN 'laptop' THEN 'laptop'
        WHEN 'desktop' THEN 'desktop'
        WHEN 'emp_desktop' THEN 'desktop'
        WHEN 'monitor' THEN 'monitor'
        WHEN 'emp_monitor' THEN 'monitor'
        WHEN 'internal_assets' THEN 'networking'
        WHEN 'network' THEN 'networking'
        WHEN 'networking' THEN 'networking'
        WHEN 'external_assets' THEN 'third_party_softwares'
        WHEN 'cloud_assets' THEN 'cloud_asset_register'
        WHEN 'cloud_register' THEN 'cloud_asset_register'
        WHEN 'cloud_asset_register' THEN 'cloud_asset_register'
        WHEN 'admin_assets' THEN 'admin'
        WHEN 'admin_devices' THEN 'admin'
        WHEN 'admin_ups' THEN 'ups'
        WHEN 'admin_mobile_phone' THEN 'mobile_phones'
        WHEN 'admin_scanners_printers' THEN 'scanner_and_others'
        WHEN 'admin_camera' THEN 'admin'
        WHEN 'admin_dvr' THEN 'admin'
        WHEN 'ups' THEN 'ups'
        WHEN 'mobile_phones' THEN 'mobile_phones'
        WHEN 'scanner_and_others' THEN 'scanner_and_others'
        WHEN 'admin' THEN 'admin'
        WHEN 'third_party' THEN 'third_party_softwares'
        WHEN 'third_party_software' THEN 'third_party_softwares'
        WHEN 'third_party_softwares' THEN 'third_party_softwares'
        WHEN 'infodesk_apps' THEN 'infodesk_applications'
        WHEN 'infodesk_applications' THEN 'infodesk_applications'
        WHEN 'gatepass' THEN 'gatepass'
        WHEN 'infodesk_leavers' THEN 'infodesk_leavers'
        ELSE 'laptop'
      END"""


DEMO_ROWS = [
    ("laptop", "Laptop — Finance-01"),
    ("laptop", "Laptop — HR-02"),
    ("desktop", "Desktop — Ops-01"),
    ("monitor", "Monitor — Desk A"),
    ("networking", "Core switch — DC1"),
    ("networking", "Firewall — edge"),
    ("cloud_asset_register", "AWS account — prod"),
    ("cloud_asset_register", "Azure subscription — dev"),
    ("infodesk_applications", "Service desk portal"),
    ("third_party_softwares", "Vendor SaaS — billing"),
    ("ups", "UPS — server room"),
    ("mobile_phones", "Mobile — field rep"),
    ("scanner_and_others", "Scanner — HR"),
    ("admin", "DVR — lobby"),
    ("gatepass", "Visitor gate pass — lobby kiosk"),
    ("gatepass", "Contractor badge printer"),
    ("infodesk_leavers", "Leaver checklist — HR workflow"),
    ("infodesk_leavers", "Mailbox disable — automation"),
]


def migrate_legacy_assets_table(conn: sqlite3.Connection) -> None:
    """One-time: 5 legacy categories -> 7-chip schema with employee_assets, etc."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='assets'"
    ).fetchone()
    if not row or not row[0]:
        return
    ddl = row[0]
    if "employee_assets" in ddl and "employee_devices" not in ddl:
        return
    if "employee_devices" not in ddl:
        return
    # Intermediate CHECK (not current CATEGORIES_META); widen step maps to new ids.
    legacy_check = """category TEXT NOT NULL CHECK (category IN (
    'employee_assets', 'internal_assets', 'external_assets', 'cloud_assets', 'admin_assets',
    'gatepass', 'infodesk_leavers'
  ))"""
    conn.executescript(
        f"""
    CREATE TABLE assets__new (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      {legacy_check},
      serial_number TEXT,
      notes TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    INSERT INTO assets__new (id, name, category, serial_number, notes, created_at)
    SELECT id, name,
      CASE category
        WHEN 'employee_devices' THEN 'employee_assets'
        WHEN 'network' THEN 'internal_assets'
        WHEN 'cloud_assets' THEN 'cloud_assets'
        WHEN 'infodesk_apps' THEN 'infodesk_leavers'
        WHEN 'third_party' THEN 'admin_assets'
        ELSE 'admin_assets'
      END,
      serial_number, notes, created_at
    FROM assets;
    DROP TABLE assets;
    ALTER TABLE assets__new RENAME TO assets;
    CREATE INDEX IF NOT EXISTS idx_assets_category ON assets (category);
    """
    )
    conn.commit()


def migrate_assets_category_widen(conn: sqlite3.Connection) -> None:
    """Rebuild assets if CHECK is missing any current category; map old labels to new."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='assets'"
    ).fetchone()
    if not row or not row[0]:
        return
    ddl = row[0]
    for c in CATEGORIES_META:
        if f"'{c['id']}'" not in ddl:
            break
    else:
        return
    check_line = _sql_category_check_line()
    cat_map = _category_map_case_sql()
    conn.executescript(
        f"""
    CREATE TABLE assets__new (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      {check_line},
      serial_number TEXT,
      notes TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    INSERT INTO assets__new (id, name, category, serial_number, notes, created_at)
    SELECT id, name, {cat_map}, serial_number, notes, created_at
    FROM assets;
    DROP TABLE assets;
    ALTER TABLE assets__new RENAME TO assets;
    CREATE INDEX IF NOT EXISTS idx_assets_category ON assets (category);
    """
    )
    conn.commit()


def ensure_schema(conn: sqlite3.Connection) -> None:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Missing {SCHEMA_PATH}")
    migrate_legacy_assets_table(conn)
    migrate_assets_category_widen(conn)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def seed_if_empty(conn: sqlite3.Connection) -> None:
    n = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    if n > 0:
        return
    names_by_cat: dict[str, list[str]] = {c["id"]: [] for c in CATEGORIES_META}
    for cat, name in DEMO_ROWS:
        names_by_cat[cat].append(name)
    _min = {
        "laptop": 10,
        "desktop": 2,
        "monitor": 2,
        "networking": 4,
        "cloud_asset_register": 3,
        "infodesk_applications": 2,
        "third_party_softwares": 3,
        "ups": 2,
        "mobile_phones": 2,
        "scanner_and_others": 2,
        "admin": 2,
        "gatepass": 2,
        "infodesk_leavers": 2,
    }
    for cid, min_n in _min.items():
        while len(names_by_cat[cid]) < min_n:
            names_by_cat[cid].append(f"{cid} — auto {len(names_by_cat[cid]) + 1}")

    for cat, names in names_by_cat.items():
        for name in names:
            conn.execute(
                "INSERT INTO assets (name, category) VALUES (?, ?)",
                (name, cat),
            )
    conn.commit()


def build_payload(conn: sqlite3.Connection) -> dict:
    counts = dict(
        conn.execute(
            "SELECT category, COUNT(*) FROM assets GROUP BY category"
        ).fetchall()
    )
    categories_out = []
    for c in CATEGORIES_META:
        cid = c["id"]
        categories_out.append(
            {
                "id": cid,
                "label": c["label"],
                "color": c["color"],
                "count": int(counts.get(cid, 0)),
            }
        )

    rows = conn.execute(
        """
        SELECT id, name, category, serial_number, created_at
        FROM assets
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 50
        """
    ).fetchall()

    items = [
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "serial_number": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]

    return {
        "title": "Asset register",
        "subtitle": "All company assets in one place",
        "generated_by": "eamr.dashboard_json",
        "categories": categories_out,
        "items": items,
    }
