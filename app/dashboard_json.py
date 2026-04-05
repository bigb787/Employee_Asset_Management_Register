"""Build dashboard JSON payload from SQLite (used by API and build script)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_PATH = DATA_DIR / "schema.sql"

CATEGORIES_META = [
    {"id": "employee_devices", "label": "Employee devices", "color": "#185FA5"},
    {"id": "network", "label": "Network", "color": "#4B2E83"},
    {"id": "cloud_assets", "label": "Cloud assets", "color": "#1E3A5F"},
    {"id": "infodesk_apps", "label": "Infodesk apps", "color": "#8B3A3A"},
    {"id": "third_party", "label": "3rd party software", "color": "#9B7EBD"},
]

DEMO_ROWS = [
    ("employee_devices", "Laptop — Finance-01"),
    ("employee_devices", "Laptop — HR-02"),
    ("employee_devices", "Monitor — Desk A"),
    ("employee_devices", "Phone — Sales lead"),
    ("network", "Core switch — DC1"),
    ("network", "Firewall — edge"),
    ("cloud_assets", "AWS account — prod"),
    ("infodesk_apps", "Service desk portal"),
    ("third_party", "O365 tenant"),
]


def ensure_schema(conn: sqlite3.Connection) -> None:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Missing {SCHEMA_PATH}")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def seed_if_empty(conn: sqlite3.Connection) -> None:
    n = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    if n > 0:
        return
    names_by_cat: dict[str, list[str]] = {c["id"]: [] for c in CATEGORIES_META}
    for cat, name in DEMO_ROWS:
        names_by_cat[cat].append(name)
    for i in range(max(0, 14 - len(names_by_cat["employee_devices"]))):
        names_by_cat["employee_devices"].append(f"Laptop — auto {i + 1}")
    while len(names_by_cat["network"]) < 4:
        names_by_cat["network"].append(f"Switch — rack {len(names_by_cat['network']) + 1}")
    while len(names_by_cat["cloud_assets"]) < 3:
        names_by_cat["cloud_assets"].append(f"S3 bucket — set {len(names_by_cat['cloud_assets']) + 1}")
    while len(names_by_cat["infodesk_apps"]) < 4:
        names_by_cat["infodesk_apps"].append(f"Infodesk app — {len(names_by_cat['infodesk_apps']) + 1}")
    while len(names_by_cat["third_party"]) < 5:
        names_by_cat["third_party"].append(f"Vendor SaaS — {len(names_by_cat['third_party']) + 1}")

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
