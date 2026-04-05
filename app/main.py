"""Employee Asset Management Register — FastAPI."""
import csv
import io
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.dashboard_json import build_payload
from app.database import DB_PATH, get_connection, init_db

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Employee Asset Management Register")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/dashboard-data")
def api_dashboard_data():
    """Live counts from SQLite (same shape as static/dashboard-data.json)."""
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
    init_db()
