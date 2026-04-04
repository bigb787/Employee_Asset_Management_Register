"""Employee Asset Management Register — FastAPI entrypoint (STEP 1 scaffold)."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.routers import (
    admin_devices,
    cloud_assets,
    employee_devices,
    gatepass,
    infodesk_apps,
    leavers,
    networking,
    third_party_software,
)

app = FastAPI(title="Employee Asset Management Register")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(employee_devices.router, prefix="/api/employee-devices", tags=["employee-devices"])
app.include_router(networking.router, prefix="/api/networking", tags=["networking"])
app.include_router(cloud_assets.router, prefix="/api/cloud-assets", tags=["cloud-assets"])
app.include_router(infodesk_apps.router, prefix="/api/infodesk-apps", tags=["infodesk-apps"])
app.include_router(third_party_software.router, prefix="/api/third-party-software", tags=["third-party"])
app.include_router(admin_devices.router, prefix="/api/admin-devices", tags=["admin-devices"])
app.include_router(gatepass.router, prefix="/api/gatepass", tags=["gatepass"])
app.include_router(leavers.router, prefix="/api/leavers", tags=["leavers"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}
