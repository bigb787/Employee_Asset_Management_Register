"""CRUD for summary-only categories (main `assets` rows: GatePass, InfoDesk_Leavers)."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Body, HTTPException

from eamr.dashboard_json import SUMMARY_ONLY_CATEGORY_IDS
from eamr.database import get_connection

router = APIRouter()


def _require_summary_category(category: str) -> None:
    if category not in SUMMARY_ONLY_CATEGORY_IDS:
        raise HTTPException(
            status_code=404,
            detail=f"Use /api/register-tables for category {category!r}",
        )


def _row_dict(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "category": r["category"],
        "serial_number": r["serial_number"],
        "notes": r["notes"],
        "created_at": r["created_at"],
    }


@router.get("/{category}")
def list_by_category(category: str):
    _require_summary_category(category)
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT id, name, category, serial_number, notes, created_at
            FROM assets
            WHERE category = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (category,),
        )
        return {"category": category, "rows": [_row_dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()


@router.post("/{category}")
def create_row(category: str, body: dict = Body(default_factory=dict)):
    _require_summary_category(category)
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    serial_number = body.get("serial_number")
    notes = body.get("notes")
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO assets (name, category, serial_number, notes)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                category,
                serial_number if serial_number is not None else None,
                notes if notes is not None else None,
            ),
        )
        conn.commit()
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"id": new_id, "ok": True}
    finally:
        conn.close()


@router.put("/row/{row_id}")
def update_row(row_id: int, body: dict = Body(default_factory=dict)):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, category FROM assets WHERE id = ?", (row_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Row not found")
        if row["category"] not in SUMMARY_ONLY_CATEGORY_IDS:
            raise HTTPException(
                status_code=400,
                detail="This row is not a summary-only asset; edit it via register tables",
            )
        name = str(body.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
        serial_number = body.get("serial_number")
        notes = body.get("notes")
        cur = conn.execute(
            """
            UPDATE assets
            SET name = ?, serial_number = ?, notes = ?
            WHERE id = ?
            """,
            (
                name,
                serial_number if serial_number is not None else None,
                notes if notes is not None else None,
                row_id,
            ),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Row not found")
        return {"ok": True}
    finally:
        conn.close()


@router.delete("/row/{row_id}")
def delete_row(row_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, category FROM assets WHERE id = ?", (row_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Row not found")
        if row["category"] not in SUMMARY_ONLY_CATEGORY_IDS:
            raise HTTPException(
                status_code=400,
                detail="This row is not a summary-only asset",
            )
        cur = conn.execute("DELETE FROM assets WHERE id = ?", (row_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Row not found")
        return {"ok": True}
    finally:
        conn.close()
