"""SQLite helpers for the asset register."""
import sqlite3
from pathlib import Path

from eamr.employee_assets_ddl import ensure_employee_assets_tables

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "assets.db"
SCHEMA_PATH = DATA_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Apply migrations + schema (same as build script) so chips match `CATEGORIES_META`."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SCHEMA_PATH.is_file():
        return
    conn = get_connection()
    try:
        from eamr.dashboard_json import ensure_schema, seed_if_empty

        ensure_schema(conn)
        ensure_employee_assets_tables(conn)
        seed_if_empty(conn)
        conn.commit()
    finally:
        conn.close()
