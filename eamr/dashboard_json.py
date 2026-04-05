"""Build dashboard JSON payload from SQLite (used by API and build script)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_PATH = DATA_DIR / "schema.sql"

# Chip headers (labels shown in the UI)
CATEGORIES_META = [
    {"id": "employee_assets", "label": "Employee_Assets", "color": "#185FA5"},
    {"id": "internal_assets", "label": "Internal Assets", "color": "#4B2E83"},
    {"id": "external_assets", "label": "External Assets", "color": "#1E3A5F"},
    {"id": "cloud_assets", "label": "Cloud_Assets", "color": "#0F766E"},
    {"id": "gatepass", "label": "GatePass", "color": "#B45309"},
    {"id": "infodesk_leavers", "label": "InfoDesk_Leavers", "color": "#7C3AED"},
    {"id": "admin_assets", "label": "Admin_Assets", "color": "#8B3A3A"},
]

EXPECTED_CATEGORY_IDS = frozenset(c["id"] for c in CATEGORIES_META)
_LEGACY_CHIP_IDS = frozenset(
    {"employee_devices", "network", "infodesk_apps", "third_party"}
)


def verify_categories_meta_or_die() -> None:
    """Fail fast if CATEGORIES_META is wrong (e.g. old 5 legacy chips)."""
    got = frozenset(c["id"] for c in CATEGORIES_META)
    if got & _LEGACY_CHIP_IDS:
        raise RuntimeError(
            f"Wrong eamr.dashboard_json: legacy ids {sorted(got & _LEGACY_CHIP_IDS)!r} in CATEGORIES_META. "
            f"Loaded from {Path(__file__).resolve()}. Run from project root with PYTHONPATH set to that folder."
        )
    if got != EXPECTED_CATEGORY_IDS:
        raise RuntimeError(
            f"Wrong CATEGORIES_META ids {sorted(got)!r}; expected {sorted(EXPECTED_CATEGORY_IDS)!r}. "
            f"File: {Path(__file__).resolve()}"
        )


def _sql_category_check_line() -> str:
    inner = ", ".join(f"'{c['id']}'" for c in CATEGORIES_META)
    return f"category TEXT NOT NULL CHECK (category IN ({inner}))"


DEMO_ROWS = [
    ("employee_assets", "Laptop — Finance-01"),
    ("employee_assets", "Laptop — HR-02"),
    ("employee_assets", "Monitor — Desk A"),
    ("employee_assets", "Phone — Sales lead"),
    ("internal_assets", "Core switch — DC1"),
    ("internal_assets", "Firewall — edge"),
    ("cloud_assets", "AWS account — prod"),
    ("cloud_assets", "Azure subscription — dev"),
    ("internal_assets", "Service desk portal"),
    ("admin_assets", "Jump host — admin"),
    ("gatepass", "Visitor gate pass — lobby kiosk"),
    ("gatepass", "Contractor badge printer"),
    ("infodesk_leavers", "Leaver checklist — HR workflow"),
    ("infodesk_leavers", "Mailbox disable — automation"),
]


def migrate_legacy_assets_table(conn: sqlite3.Connection) -> None:
    """One-time: 5 legacy categories -> current CHECK set (SQLite CHECK cannot update in place)."""
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
    check_line = _sql_category_check_line()
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
    """SQLite CHECK cannot alter in place — rebuild if ddl is missing any current category."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='assets'"
    ).fetchone()
    if not row or not row[0]:
        return
    ddl = row[0]
    if "employee_devices" in ddl:
        return
    for c in CATEGORIES_META:
        if f"'{c['id']}'" not in ddl:
            break
    else:
        return
    check_line = _sql_category_check_line()
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
    SELECT id, name, category, serial_number, notes, created_at FROM assets;
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
    for i in range(max(0, 14 - len(names_by_cat["employee_assets"]))):
        names_by_cat["employee_assets"].append(f"Laptop — auto {i + 1}")
    while len(names_by_cat["internal_assets"]) < 4:
        names_by_cat["internal_assets"].append(
            f"Internal asset — {len(names_by_cat['internal_assets']) + 1}"
        )
    while len(names_by_cat["external_assets"]) < 3:
        names_by_cat["external_assets"].append(
            f"External asset — {len(names_by_cat['external_assets']) + 1}"
        )
    while len(names_by_cat["cloud_assets"]) < 3:
        names_by_cat["cloud_assets"].append(
            f"Cloud asset — {len(names_by_cat['cloud_assets']) + 1}"
        )
    while len(names_by_cat["admin_assets"]) < 4:
        names_by_cat["admin_assets"].append(
            f"Admin asset — {len(names_by_cat['admin_assets']) + 1}"
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
