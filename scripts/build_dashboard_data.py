#!/usr/bin/env python3
"""
Write static/dashboard-data.json from data/assets.db.
Usage (repo root):  python scripts/build_dashboard_data.py
GitHub Actions:      python scripts/build_dashboard_data.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dashboard_json import (  # noqa: E402
    build_payload,
    ensure_schema,
    seed_if_empty,
)

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "assets.db"
OUT_PATH = ROOT / "static" / "dashboard-data.json"


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "static").mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_schema(conn)
        seed_if_empty(conn)
        payload = build_payload(conn)
    finally:
        conn.close()

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"Wrote {OUT_PATH} ({len(payload['categories'])} categories, {len(payload['items'])} items)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
