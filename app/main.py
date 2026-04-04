"""
FastAPI Employee Asset Register — API routes, CORS, static files, request audit logging.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app import database
from app.utils.excel_exporter import export_all_assets, export_gatepass, export_leavers
from app.utils.iso_audit import generate_iso_report
from app.utils.pdf_generator import generate_gatepass_pdf, generate_it_exit_pdf

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EVIDENCE_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
ALLOWED_EVIDENCE_CT = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_client_ip(request: Request) -> Optional[str]:
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _status_column(table: str) -> Optional[str]:
    if table == "gatepass":
        return "status"
    if table == "leavers_checklist":
        return "overall_status"
    if table in ("laptops", "desktops", "monitors", "accessories"):
        return "asset_status"
    return None


def _dept_column(table: str) -> Optional[str]:
    if table == "leavers_checklist":
        return "department"
    if table == "gatepass":
        return "dept_head"
    if table in (
        "cloud_assets",
        "infodesk_applications",
        "third_party_software",
        "audit_log",
    ):
        return None
    return "dept"


def _location_column(table: str) -> Optional[str]:
    if table == "leavers_checklist":
        return "hw_inventory_location"
    if table in ("cloud_assets", "infodesk_applications", "third_party_software"):
        return "asset_location"
    if table == "audit_log":
        return None
    return "location"


def _pii_column(table: str) -> Optional[str]:
    if table in ("gatepass", "leavers_checklist", "audit_log"):
        return None
    return "contains_pii"


def _iso_column(table: str) -> Optional[str]:
    if table in ("gatepass", "leavers_checklist", "audit_log"):
        return None
    return "iso_classification"


def _apply_list_filters(
    table: str,
    rows: list[dict[str, Any]],
    search: Optional[str],
    status: Optional[str],
    dept: Optional[str],
    location: Optional[str],
    pii: Optional[str],
    iso_class: Optional[str],
) -> list[dict[str, Any]]:
    out = rows
    sc = _status_column(table)
    if status and str(status).strip() and str(status).lower() != "all" and sc:
        sv = str(status).strip()
        out = [r for r in out if str(r.get(sc) or "").strip() == sv]
    dc = _dept_column(table)
    if dept and str(dept).strip() and str(dept).lower() != "all" and dc:
        dv = str(dept).strip()
        out = [r for r in out if str(r.get(dc) or "").strip() == dv]
    lc = _location_column(table)
    if location and str(location).strip() and str(location).lower() != "all" and lc:
        lv = str(location).strip()
        out = [r for r in out if lv in str(r.get(lc) or "")]
    pc = _pii_column(table)
    if pii and str(pii).strip() and str(pii).lower() != "all" and pc:
        pv = str(pii).strip()
        out = [r for r in out if str(r.get(pc) or "").strip() == pv]
    ic = _iso_column(table)
    if iso_class and str(iso_class).strip() and str(iso_class).lower() != "all" and ic:
        iv = str(iso_class).strip()
        out = [r for r in out if str(r.get(ic) or "").strip() == iv]
    if search and str(search).strip():
        q = str(search).strip().lower()
        out = [r for r in out if _row_matches_search(r, q)]
    return out


def _row_matches_search(row: dict[str, Any], q: str) -> bool:
    for v in row.values():
        if v is None:
            continue
        if q in str(v).lower():
            return True
    return False


def _safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]+", "_", base)
    return base[:180] if base else "file"


class ApiAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/api"):
            try:
                database.log_audit(
                    "api",
                    0,
                    request.method,
                    None,
                    {"path": path, "status_code": response.status_code},
                    performed_by=request.headers.get("x-user") or None,
                    ip_address=get_client_ip(request),
                    iso_ref=None,
                    changed_fields=[path],
                )
            except Exception:
                pass
        return response


app = FastAPI(title="Employee Asset Register", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiAuditMiddleware)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)


@app.get("/")
def serve_index():
    return FileResponse(BASE_DIR / "templates" / "index.html")


@app.get("/api/stats")
def api_stats():
    try:
        return database.get_all_stats()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/export/all")
def api_export_all():
    try:
        return export_all_assets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/gatepass/export")
def api_export_gatepass():
    try:
        return export_gatepass()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/gatepass/next-number")
def api_gatepass_next_number():
    """Next gatepass number (GP-YYYYMMDD-###); must be registered before /api/gatepass/{row_id}/pdf."""
    try:
        return {"gatepass_no": database.generate_gatepass_no()}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/leavers/export")
def api_export_leavers():
    try:
        return export_leavers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/gatepass/{row_id}/pdf")
def api_gatepass_pdf(row_id: int):
    try:
        row = database.get_by_id("gatepass", row_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="Gatepass not found")
    try:
        pdf = generate_gatepass_pdf(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return StreamingResponse(
        iter([pdf]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="gatepass-{row_id}.pdf"'
        },
    )


@app.get("/api/leavers/{row_id}/pdf")
def api_leaver_pdf(row_id: int):
    try:
        row = database.get_by_id("leavers_checklist", row_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="Leaver record not found")
    try:
        pdf = generate_it_exit_pdf(row, row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return StreamingResponse(
        iter([pdf]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="it-exit-{row_id}.pdf"'
        },
    )


@app.post("/api/leavers/{row_id}/upload-evidence")
async def api_leaver_upload_evidence(
    request: Request,
    row_id: int,
    file: UploadFile = File(...),
    updated_by: Optional[str] = Form(None),
):
    try:
        row = database.get_by_id("leavers_checklist", row_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="Leaver record not found")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10MB limit")
    fn = _safe_filename(file.filename or "upload")
    ext = Path(fn).suffix.lower()
    if ext not in ALLOWED_EVIDENCE_EXT:
        raise HTTPException(
            status_code=400,
            detail="Allowed types: PDF, JPG, PNG, DOCX",
        )
    ct = (file.content_type or "").split(";")[0].strip().lower()
    if ct and ct not in ALLOWED_EVIDENCE_CT:
        raise HTTPException(status_code=400, detail="Invalid content type")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    s3_key = f"leavers/evidence/{row_id}/{ts}_{fn}"
    try:
        database.upload_evidence_to_s3(
            raw, s3_key, file.content_type or "application/octet-stream"
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    performer = updated_by
    patch = {
        "evidence_file_name": fn,
        "evidence_file_s3_key": s3_key,
        "evidence_file_url": "",
        "evidence_uploaded_at": now_iso,
        "evidence_uploaded_by": performer,
        "updated_by": performer,
    }
    ip = get_client_ip(request)
    try:
        database.update("leavers_checklist", row_id, patch, client_ip=ip)
        database.log_audit(
            "leavers_checklist",
            row_id,
            "UPLOAD_EVIDENCE",
            {"evidence_file_s3_key": row.get("evidence_file_s3_key")},
            {"evidence_file_s3_key": s3_key, "evidence_file_name": fn},
            performed_by=performer,
            ip_address=ip,
            iso_ref="A.5.11",
            changed_fields=["evidence_file_s3_key", "evidence_file_name"],
        )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"ok": True, "s3_key": s3_key, "message": "Evidence uploaded"}


@app.get("/api/leavers/{row_id}/evidence")
def api_leaver_evidence(row_id: int):
    try:
        row = database.get_by_id("leavers_checklist", row_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="Leaver record not found")
    key = row.get("evidence_file_s3_key")
    if not key:
        raise HTTPException(status_code=404, detail="No evidence file")
    try:
        url = database.get_presigned_url(str(key), 3600)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {"url": url, "expires_in": 3600}


@app.get("/api/iso-report")
def api_iso_report():
    try:
        return generate_iso_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/audit-log")
def api_audit_log(
    table: Optional[str] = Query(None, description="Filter by table_name"),
    from_date: Optional[str] = Query(None, alias="from_date"),
    to_date: Optional[str] = Query(None, alias="to_date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    try:
        rows, total = database.fetch_audit_log_page(
            table_name=table,
            from_date=from_date,
            to_date=to_date,
            page=page,
            limit=limit,
        )
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"items": rows, "total": total, "page": page, "limit": limit}


@app.get("/api/{table}")
def api_list_table(
    table: str,
    search: Optional[str] = None,
    status: Optional[str] = None,
    dept: Optional[str] = None,
    location: Optional[str] = None,
    pii: Optional[str] = None,
    iso_class: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(500, ge=1, le=5000),
):
    if table not in database.VALID_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table")
    if table == "audit_log":
        try:
            rows, total = database.fetch_audit_log_page(
                table_name=None,
                from_date=None,
                to_date=None,
                page=page,
                limit=min(limit, 500),
            )
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return {"items": rows, "total": total, "page": page, "limit": limit}
    try:
        rows = database.get_all(table)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    filtered = _apply_list_filters(
        table, rows, search, status, dept, location, pii, iso_class
    )
    return filtered


@app.post("/api/{table}")
def api_create_table(table: str, request: Request, body: dict[str, Any] = Body(...)):
    if table not in database.VALID_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table")
    if table == "audit_log":
        raise HTTPException(status_code=400, detail="Cannot create audit_log via API")
    ip = get_client_ip(request)
    try:
        new_id = database.create(table, body, client_ip=ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    try:
        row = database.get_by_id(table, new_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return row


@app.put("/api/{table}/{row_id}")
def api_update_table(
    table: str,
    row_id: int,
    request: Request,
    body: dict[str, Any] = Body(...),
):
    if table not in database.VALID_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table")
    if table == "audit_log":
        raise HTTPException(status_code=400, detail="Cannot update audit_log via API")
    ip = get_client_ip(request)
    try:
        ok = database.update(table, row_id, body, client_ip=ip)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        return database.get_by_id(table, row_id)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/{table}/{row_id}")
def api_delete_table(table: str, row_id: int, request: Request):
    if table not in database.VALID_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table")
    if table == "audit_log":
        raise HTTPException(status_code=400, detail="Cannot delete audit_log via API")
    ip = get_client_ip(request)
    try:
        ok = database.delete(table, row_id, client_ip=ip)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}
