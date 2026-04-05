"""Build dashboard JSON payload from SQLite (used by API and build script)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_PATH = DATA_DIR / "schema.sql"

# Chip headers (labels shown in the UI)
CATEGORIES_META = [
    {"id": "employee_devices", "label": "Employee_Devices", "color": "#185FA5"},
    {"id": "networking", "label": "Networking", "color": "#4B2E83"},
    {"id": "cloud_asset_register", "label": "Cloud Asset Register", "color": "#0F766E"},
    {"id": "infodesk_applications", "label": "Infodesk Applications", "color": "#0369A1"},
    {"id": "third_party_softwares", "label": "Third Party Softwares", "color": "#1E3A5F"},
    {"id": "admin_devices", "label": "Admin Devices", "color": "#8B3A3A"},
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
        WHEN 'employee_assets' THEN 'employee_devices'
        WHEN 'employee_devices' THEN 'employee_devices'
        WHEN 'internal_assets' THEN 'networking'
        WHEN 'network' THEN 'networking'
        WHEN 'external_assets' THEN 'third_party_softwares'
        WHEN 'cloud_assets' THEN 'cloud_asset_register'
        WHEN 'admin_assets' THEN 'admin_devices'
        WHEN 'third_party' THEN 'third_party_softwares'
        WHEN 'infodesk_apps' THEN 'infodesk_applications'
        ELSE category
      END"""


DEMO_ROWS = [
    ("employee_devices", "Laptop — Finance-01"),
    ("employee_devices", "Laptop — HR-02"),
    ("employee_devices", "Monitor — Desk A"),
    ("employee_devices", "Accessory — Dock kit"),
    ("networking", "Core switch — DC1"),
    ("networking", "Firewall — edge"),
    ("cloud_asset_register", "AWS account — prod"),
    ("cloud_asset_register", "Azure subscription — dev"),
    ("infodesk_applications", "Service desk portal"),
    ("third_party_softwares", "Vendor SaaS — billing"),
    ("admin_devices", "Jump host — admin"),
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
    for i in range(max(0, 12 - len(names_by_cat["employee_devices"]))):
        names_by_cat["employee_devices"].append(f"Laptop — auto {i + 1}")
    while len(names_by_cat["networking"]) < 4:
        names_by_cat["networking"].append(
            f"Network asset — {len(names_by_cat['networking']) + 1}"
        )
    while len(names_by_cat["cloud_asset_register"]) < 3:
        names_by_cat["cloud_asset_register"].append(
            f"Cloud row — {len(names_by_cat['cloud_asset_register']) + 1}"
        )
    while len(names_by_cat["infodesk_applications"]) < 2:
        names_by_cat["infodesk_applications"].append(
            f"Infodesk app — {len(names_by_cat['infodesk_applications']) + 1}"
        )
    while len(names_by_cat["third_party_softwares"]) < 3:
        names_by_cat["third_party_softwares"].append(
            f"Third party — {len(names_by_cat['third_party_softwares']) + 1}"
        )
    while len(names_by_cat["admin_devices"]) < 4:
        names_by_cat["admin_devices"].append(
            f"Admin device — {len(names_by_cat['admin_devices']) + 1}"
        )
    while len(names_by_cat["gatepass"]) < 2:
        names_by_cat["gatepass"].append(
            f"Gate pass — {len(names_by_cat['gatepass']) + 1}"
        )
    while len(names_by_cat["infodesk_leavers"]) < 2:
        names_by_cat["infodesk_leavers"].append(
            f"InfoDesk leavers — {len(names_by_cat['infodesk_leavers']) + 1}"
        )

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
