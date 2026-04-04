import os
import io
import json
import aiosqlite
from datetime import datetime
from typing import Optional

from fastapi import (
    FastAPI, Request, HTTPException, UploadFile, File,
    Query, BackgroundTasks,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import (
    DATABASE_PATH,
    LOCATIONS,
    ALLOWED_TABLES,
    init_db,
    get_all,
    get_by_id,
    create,
    update,
    delete,
    get_count,
    get_all_stats,
    log_audit,
    generate_gatepass_no,
    upload_evidence_to_s3,
    get_presigned_url,
)
from app.utils.pdf_generator import generate_gatepass_pdf, generate_leaver_pdf
from app.utils.excel_exporter import export_all_assets, export_gatepass, export_leavers

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_TABLES = [
    "laptops", "desktops", "monitors", "accessories",
    "networking", "cloud_assets", "infodesk_applications",
    "third_party_software", "ups", "mobile_phones",
    "scanners_printers", "cameras_dvr",
    "gatepass", "leavers_checklist", "audit_log",
]

ALLOWED_EVIDENCE_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
MAX_EVIDENCE_BYTES = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Employee Asset Register", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    await init_db()


# ---------------------------------------------------------------------------
# Middleware — log every API call to audit_log
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_audit_middleware(request: Request, call_next):
    start = datetime.utcnow()
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        await log_audit(
            table="api_request",
            record_id=None,
            action=request.method,
            old_values=None,
            new_values={"path": request.url.path, "query": str(request.query_params)},
            performed_by=request.headers.get("X-User", "anonymous"),
            ip_address=ip,
        )
    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _validate_table(table: str) -> None:
    if table not in VALID_TABLES:
        raise HTTPException(status_code=400, detail=f"Invalid table: {table}")


def _get_ip(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")


def _get_user(request: Request) -> str:
    return request.headers.get("X-User", "anonymous")


async def _get_table_columns(table: str) -> list[str]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(f"PRAGMA table_info({table})") as cur:
            rows = await cur.fetchall()
    return [r[1] for r in rows]


async def _search_table(
    table: str,
    search: Optional[str] = None,
    status: Optional[str] = None,
    dept: Optional[str] = None,
    location: Optional[str] = None,
    pii: Optional[str] = None,
) -> list[dict]:
    cols = await _get_table_columns(table)
    conditions: list[str] = []
    params: list = []

    if search:
        skip = {"id", "created_at", "updated_at", "created_by", "updated_by"}
        text_cols = [c for c in cols if c not in skip]
        if text_cols:
            like_parts = " OR ".join(f"{c} LIKE ?" for c in text_cols)
            conditions.append(f"({like_parts})")
            params.extend([f"%{search}%"] * len(text_cols))

    if status:
        if "asset_status" in cols:
            conditions.append("asset_status = ?"); params.append(status)
        elif "status" in cols:
            conditions.append("status = ?"); params.append(status)
        elif "overall_status" in cols:
            conditions.append("overall_status = ?"); params.append(status)

    if dept and "dept" in cols:
        conditions.append("dept = ?"); params.append(dept)

    if location:
        if "location" in cols:
            conditions.append("location = ?"); params.append(location)
        elif "asset_location" in cols:
            conditions.append("asset_location = ?"); params.append(location)

    if pii and "contains_pii" in cols:
        conditions.append("contains_pii = ?"); params.append(pii)

    query = f"SELECT * FROM {table}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
@app.get("/api/stats")
async def api_stats():
    try:
        stats = await get_all_stats()
        return JSONResponse(content=stats)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Generic table CRUD
# ---------------------------------------------------------------------------
@app.get("/api/{table}")
async def api_get_all(
    table: str,
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    dept: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    pii: Optional[str] = Query(None),
    iso_class: Optional[str] = Query(None),  # accepted but no-op (column removed)
):
    _validate_table(table)
    try:
        rows = await _search_table(table, search, status, dept, location, pii)
        return JSONResponse(content={"data": rows, "count": len(rows)})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/{table}")
async def api_create(table: str, request: Request):
    _validate_table(table)
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    # Validate location if present
    for loc_field in ("location", "asset_location"):
        if loc_field in data and data[loc_field] not in LOCATIONS:
            raise HTTPException(
                status_code=422,
                detail=f"location must be one of {LOCATIONS}",
            )
    try:
        new_id = await create(table, data, performed_by=_get_user(request), ip_address=_get_ip(request))
        return JSONResponse(content={"id": new_id, "message": "Created"}, status_code=201)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.put("/api/{table}/{record_id}")
async def api_update(table: str, record_id: int, request: Request):
    _validate_table(table)
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    for loc_field in ("location", "asset_location"):
        if loc_field in data and data[loc_field] not in LOCATIONS:
            raise HTTPException(
                status_code=422,
                detail=f"location must be one of {LOCATIONS}",
            )
    try:
        ok = await update(table, record_id, data, performed_by=_get_user(request), ip_address=_get_ip(request))
        if not ok:
            raise HTTPException(status_code=404, detail="Record not found")
        return JSONResponse(content={"message": "Updated"})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/{table}/{record_id}")
async def api_delete(table: str, record_id: int, request: Request):
    _validate_table(table)
    try:
        ok = await delete(table, record_id, performed_by=_get_user(request), ip_address=_get_ip(request))
        if not ok:
            raise HTTPException(status_code=404, detail="Record not found")
        return JSONResponse(content={"message": "Deleted"})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Gatepass PDF
# ---------------------------------------------------------------------------
@app.get("/api/gatepass/{record_id}/pdf")
async def api_gatepass_pdf(record_id: int):
    try:
        row = await get_by_id("gatepass", record_id)
        if not row:
            raise HTTPException(status_code=404, detail="Gatepass not found")
        pdf_bytes = generate_gatepass_pdf(row)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="gatepass-{row.get("gatepass_no","unknown")}.pdf"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Leavers — evidence upload
# ---------------------------------------------------------------------------
@app.post("/api/leavers/{record_id}/upload-evidence")
async def api_upload_evidence(record_id: int, request: Request, file: UploadFile = File(...)):
    row = await get_by_id("leavers_checklist", record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Leaver record not found")

    if file.content_type not in ALLOWED_EVIDENCE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type not allowed. Accepted: PDF, JPG, PNG, DOCX",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in (file.filename or "file"))
    s3_key = f"leavers/evidence/{record_id}/{timestamp}_{safe_name}"

    try:
        await upload_evidence_to_s3(file_bytes, s3_key, file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"S3 upload failed: {exc}")

    now_str = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    await update(
        "leavers_checklist",
        record_id,
        {
            "evidence_file_name": file.filename,
            "evidence_file_s3_key": s3_key,
            "evidence_file_url": "",          # never expose raw bucket URL
            "evidence_uploaded_at": now_str,
            "evidence_uploaded_by": _get_user(request),
        },
        performed_by=_get_user(request),
        ip_address=_get_ip(request),
    )

    await log_audit(
        table="leavers_checklist",
        record_id=record_id,
        action="UPLOAD_EVIDENCE",
        old_values=None,
        new_values={"s3_key": s3_key, "filename": file.filename},
        performed_by=_get_user(request),
        ip_address=_get_ip(request),
    )

    return JSONResponse(
        content={"s3_key": s3_key, "message": "Evidence uploaded successfully"},
        status_code=201,
    )


# ---------------------------------------------------------------------------
# Leavers — evidence download (pre-signed URL, never raw S3)
# ---------------------------------------------------------------------------
@app.get("/api/leavers/{record_id}/evidence")
async def api_get_evidence(record_id: int):
    row = await get_by_id("leavers_checklist", record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Leaver record not found")
    s3_key = row.get("evidence_file_s3_key")
    if not s3_key:
        raise HTTPException(status_code=404, detail="No evidence file uploaded")
    try:
        url = await get_presigned_url(s3_key, expiry=3600)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not generate URL: {exc}")
    return JSONResponse(content={"url": url, "expires_in": 3600})


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
@app.get("/api/export/all")
async def api_export_all():
    try:
        xlsx_bytes = await export_all_assets()
        return StreamingResponse(
            io.BytesIO(xlsx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="asset-register.xlsx"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/gatepass/export")
async def api_export_gatepass():
    try:
        xlsx_bytes = await export_gatepass()
        return StreamingResponse(
            io.BytesIO(xlsx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="gatepass-export.xlsx"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/leavers/export")
async def api_export_leavers():
    try:
        xlsx_bytes = await export_leavers()
        return StreamingResponse(
            io.BytesIO(xlsx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="leavers-export.xlsx"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Leavers PDF — IT exit clearance
# ---------------------------------------------------------------------------
@app.get("/api/leavers/{record_id}/pdf")
async def api_leaver_pdf(record_id: int):
    try:
        row = await get_by_id("leavers_checklist", record_id)
        if not row:
            raise HTTPException(status_code=404, detail="Leaver record not found")
        pdf_bytes = generate_leaver_pdf(row)
        safe_name = "".join(c if c.isalnum() else "_" for c in row.get("employee_name", str(record_id)))
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="exit-clearance-{safe_name}.pdf"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Compliance summary report
# ---------------------------------------------------------------------------
@app.get("/api/iso-report")
async def api_compliance_report():
    try:
        stats = await get_all_stats()
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM leavers_checklist WHERE overall_status != 'Complete'"
            ) as cur:
                pending_leavers = (await cur.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM gatepass WHERE status = 'Open'"
            ) as cur:
                open_gatepasses = (await cur.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM audit_log WHERE performed_at >= date('now','-7 days')"
            ) as cur:
                recent_audit_events = (await cur.fetchone())[0]
            async with db.execute(
                "SELECT COUNT(*) FROM leavers_checklist WHERE hw_handed_over = 'Pending'"
            ) as cur:
                hw_pending = (await cur.fetchone())[0]
            pii_counts: dict[str, int] = {}
            for t in ["laptops", "desktops", "networking", "cloud_assets",
                       "infodesk_applications", "third_party_software", "cameras_dvr"]:
                async with db.execute(
                    f"SELECT COUNT(*) FROM {t} WHERE contains_pii = 'Yes'"
                ) as cur:
                    pii_counts[t] = (await cur.fetchone())[0]

        return JSONResponse(content={
            "asset_totals": stats,
            "pending_leavers": pending_leavers,
            "open_gatepasses": open_gatepasses,
            "recent_audit_events_7d": recent_audit_events,
            "hw_handover_pending": hw_pending,
            "pii_asset_counts": pii_counts,
            "generated_at": datetime.utcnow().isoformat(),
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Audit log — paginated with filters
# ---------------------------------------------------------------------------
@app.get("/api/audit-log")
async def api_audit_log(
    table: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    conditions: list[str] = []
    params: list = []

    if table:
        conditions.append("table_name = ?"); params.append(table)
    if from_date:
        conditions.append("performed_at >= ?"); params.append(from_date)
    if to_date:
        conditions.append("performed_at <= ?"); params.append(to_date + " 23:59:59")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * limit

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT COUNT(*) FROM audit_log {where}", params
            ) as cur:
                total = (await cur.fetchone())[0]
            async with db.execute(
                f"SELECT * FROM audit_log {where} ORDER BY performed_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ) as cur:
                rows = [dict(r) for r in await cur.fetchall()]

        return JSONResponse(content={
            "data": rows,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
