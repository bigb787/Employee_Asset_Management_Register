"""REST API for Employee_Assets sub-tables (laptops, desktops, monitors)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Body, HTTPException

from eamr.database import get_connection
from eamr.employee_assets_ddl import ensure_employee_assets_tables
from eamr.employee_assets_schema import KIND_SPECS, fields_for_kind, meta_payload

router = APIRouter()


def _table(kind: str) -> str:
    if kind not in KIND_SPECS:
        raise HTTPException(status_code=404, detail=f"Unknown kind: {kind}")
    return KIND_SPECS[kind]["table"]


@router.get("/meta")
def employee_assets_meta():
    """Column keys and labels for each sub-table (for forms and grids)."""
    conn = get_connection()
    try:
        ensure_employee_assets_tables(conn)
        conn.commit()
    finally:
        conn.close()
    return meta_payload()


@router.get("/{kind}")
def list_rows(kind: str):
    _table(kind)
    spec = KIND_SPECS[kind]
    table = spec["table"]
    fields = fields_for_kind(kind)
    cols_sql = "id, " + ", ".join(fields) + ", created_at, updated_at"
    conn = get_connection()
    try:
        ensure_employee_assets_tables(conn)
        conn.commit()
        try:
            cur = conn.execute(f"SELECT {cols_sql} FROM {table} ORDER BY id DESC")
            rows = [{k: r[k] for k in r.keys()} for r in cur.fetchall()]
            return {"kind": kind, "rows": rows}
        except sqlite3.OperationalError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Database error (try restarting the server): {e}",
            ) from e
    finally:
        conn.close()


@router.post("/{kind}")
def create_row(kind: str, body: dict = Body(default_factory=dict)):
    _table(kind)
    fields = fields_for_kind(kind)
    table = KIND_SPECS[kind]["table"]
    vals = [body.get(f) if body.get(f) is not None else None for f in fields]
    placeholders = ", ".join("?" * len(fields))
    colnames = ", ".join(fields)
    conn = get_connection()
    try:
        ensure_employee_assets_tables(conn)
        conn.execute(
            f"INSERT INTO {table} ({colnames}, updated_at) VALUES ({placeholders}, datetime('now'))",
            vals,
        )
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"id": new_id, "ok": True}
    finally:
        conn.close()


@router.put("/{kind}/{row_id}")
def update_row(kind: str, row_id: int, body: dict = Body(default_factory=dict)):
    _table(kind)
    fields = fields_for_kind(kind)
    table = KIND_SPECS[kind]["table"]
    sets = ", ".join(f"{f} = ?" for f in fields)
    vals = [body.get(f) if body.get(f) is not None else None for f in fields]
    vals.append(row_id)
    conn = get_connection()
    try:
        ensure_employee_assets_tables(conn)
        cur = conn.execute(
            f"UPDATE {table} SET {sets}, updated_at = datetime('now') WHERE id = ?",
            vals,
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Row not found")
        return {"ok": True}
    finally:
        conn.close()


@router.delete("/{kind}/{row_id}")
def delete_row(kind: str, row_id: int):
    _table(kind)
    table = KIND_SPECS[kind]["table"]
    conn = get_connection()
    try:
        ensure_employee_assets_tables(conn)
        cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Row not found")
        return {"ok": True}
    finally:
        conn.close()
