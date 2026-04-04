"""Database helpers (STEP 1 scaffold)."""
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "assets.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if missing (expand in later steps)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _schema_placeholder (id INTEGER PRIMARY KEY)"
        )
        conn.commit()
    finally:
        conn.close()
