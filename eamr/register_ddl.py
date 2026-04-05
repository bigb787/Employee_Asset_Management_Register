"""CREATE TABLE for register kinds that use reg_* tables (ea_* come from schema.sql)."""
from __future__ import annotations

import sqlite3

from eamr.register_schema import KIND_SPECS


def _create_table_sql(table: str, field_names: list[str]) -> str:
    body = ",\n  ".join(f"{name} TEXT" for name in field_names)
    return f"""CREATE TABLE IF NOT EXISTS {table} (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  {body},
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);"""


def build_register_tables_ddl() -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for spec in KIND_SPECS.values():
        table = spec["table"]
        if table.startswith("ea_") or table in seen:
            continue
        seen.add(table)
        fields = [c[0] for c in spec["columns"]]
        parts.append(_create_table_sql(table, fields))
    return "\n\n".join(parts)


REGISTER_TABLES_DDL = build_register_tables_ddl()


def ensure_register_tables(conn: sqlite3.Connection) -> None:
    if not REGISTER_TABLES_DDL.strip():
        return
    conn.executescript(REGISTER_TABLES_DDL)
