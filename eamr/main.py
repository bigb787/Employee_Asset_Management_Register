"""Employee Asset Management Register — FastAPI."""
import base64
import csv
import io
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from eamr import dashboard_json as _dashboard_json
from eamr.dashboard_json import CATEGORIES_META, build_payload, verify_categories_meta_or_die
from eamr.database import DB_PATH, get_connection, init_db
from eamr.register_ddl import ensure_register_tables
from eamr.register_schema import register_bootstrap_dict
from eamr.register_tables_api import router as register_tables_router
from eamr.summary_assets_api import router as summary_assets_router

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
_LOG = logging.getLogger("uvicorn.error")

app = FastAPI(title="Employee Asset Management Register")


@app.get("/api/register-tables/meta")
def api_register_tables_meta():
    """Kinds, columns, and panel/tab layout for register detail grids."""
    conn = get_connection()
    try:
        ensure_register_tables(conn)
        conn.commit()
    finally:
        conn.close()
    return register_bootstrap_dict()


app.include_router(register_tables_router, prefix="/api/register-tables")
app.include_router(summary_assets_router, prefix="/api/summary-assets")
templates = Jinja2Templates(directory=str(ROOT / "templates"))


def categories_for_index() -> list[dict]:
    """Chips always match live code (`CATEGORIES_META`), even if API/JSON is stale."""
    if DB_PATH.is_file():
        conn = get_connection()
        try:
            return build_payload(conn)["categories"]
        finally:
            conn.close()
    counts = {}
    p = STATIC_DIR / "dashboard-data.json"
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for x in data.get("categories", []):
                if isinstance(x, dict) and x.get("id") is not None:
                    counts[str(x["id"])] = int(x.get("count") or 0)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
    return [
        {
            "id": c["id"],
            "label": c["label"],
            "color": c["color"],
            "count": int(counts.get(c["id"], 0)),
        }
        for c in CATEGORIES_META
    ]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    cats = categories_for_index()
    ui_verify = (
        f"Dashboard ({len(cats)} category chips). Project folder: {ROOT.name}. Python: "
        f"{Path(_dashboard_json.__file__).resolve()}"
    )
    cats_json = json.dumps(cats)
    bootstrap_b64 = base64.b64encode(cats_json.encode("utf-8")).decode("ascii")
    chip_defs = [{"id": c["id"], "color": c["color"]} for c in CATEGORIES_META]
    chip_defs_json = json.dumps(chip_defs)
    _register_payload = json.dumps(
        register_bootstrap_dict(), separators=(",", ":"), ensure_ascii=True
    )
    register_bootstrap_b64 = base64.b64encode(_register_payload.encode("utf-8")).decode("ascii")
    base = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "api_base": base,
            "api_base_js": json.dumps(base),
            "register_bootstrap_b64": register_bootstrap_b64,
            "categories": cats,
            "categories_bootstrap_json": cats_json,
            "bootstrap_b64": bootstrap_b64,
            "chip_defs_json": chip_defs_json,
            "ui_verify": ui_verify,
            "html_title": f"Asset register ({len(cats)} categories)",
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/debug-ui")
def api_debug_ui(response: Response):
    """Open this URL in the browser to prove which code + folder is serving the app."""
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return {
        "app": "Employee_Asset_Management_Register",
        "category_count": len(CATEGORIES_META),
        "labels": [c["label"] for c in CATEGORIES_META],
        "ids": [c["id"] for c in CATEGORIES_META],
        "project_root": str(ROOT.resolve()),
        "dashboard_json_py": str(Path(_dashboard_json.__file__).resolve()),
        "database_exists": DB_PATH.is_file(),
        "database_path": str(DB_PATH.resolve()) if DB_PATH.is_file() else None,
        "read_me": "If labels do not match the home page chips, another app may be on this port. Use ASSET_REGISTER_PORT=8010 and run.ps1.",
    }


@app.get("/api/dashboard-data")
def api_dashboard_data(response: Response):
    """Live counts from SQLite (same shape as static/dashboard-data.json)."""
    response.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    if not DB_PATH.is_file():
        p = STATIC_DIR / "dashboard-data.json"
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
        return {
            "title": "Asset register",
            "subtitle": "All company assets in one place",
            "categories": [],
            "items": [],
        }
    conn = get_connection()
    try:
        return build_payload(conn)
    finally:
        conn.close()


@app.get("/api/assets/export.csv")
def export_assets_csv():
    if not DB_PATH.is_file():
        return Response(content="id,name,category\n", media_type="text/csv")
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, category, serial_number, notes, created_at FROM assets ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "name", "category", "serial_number", "notes", "created_at"])
    for r in rows:
        w.writerow(list(r))
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="assets-export.csv"'},
    )


@app.on_event("startup")
def _startup():
    verify_categories_meta_or_die()
    init_db()
    ids = [c["id"] for c in CATEGORIES_META]
    _LOG.warning(
        "Asset register UI: %s categories from %s (open / and view page source for <!-- ui-categories:)",
        len(ids),
        ROOT,
    )


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
