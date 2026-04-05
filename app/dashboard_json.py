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
    {"id": "admin_assets", "label": "Admin_Assets", "color": "#8B3A3A"},
]

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
    conn.executescript(
        """
    CREATE TABLE assets__new (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      category TEXT NOT NULL CHECK (category IN (
        'employee_assets', 'internal_assets', 'external_assets',
        'cloud_assets', 'admin_assets'
      )),
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
        WHEN 'infodesk_apps' THEN 'internal_assets'
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


def migrate_four_category_table_add_cloud(conn: sqlite3.Connection) -> None:
    """SQLite CHECK cannot alter in place — widen 4-category table to include cloud_assets."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='assets'"
    ).fetchone()
    if not row or not row[0]:
        return
    ddl = row[0]
    if "employee_devices" in ddl:
        return
    if "cloud_assets" in ddl:
        return
    if "employee_assets" not in ddl:
        return
    conn.executescript(
        """
    CREATE TABLE assets__new (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      category TEXT NOT NULL CHECK (category IN (
        'employee_assets', 'internal_assets', 'external_assets',
        'cloud_assets', 'admin_assets'
      )),
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
    migrate_four_category_table_add_cloud(conn)
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
        "generated_by": "app.dashboard_json",
        "categories": categories_out,
        "items": items,
    }
