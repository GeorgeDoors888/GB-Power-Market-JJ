import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dashboard import run_dashboard
from utils.logging_utils import get_logger

LOGGER = get_logger(__name__)
OUT_DIR = "out"

app = FastAPI(title="GB Energy Dashboard Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DashboardFilters(BaseModel):
    dateRange: str = "7D"
    mode: str = "ALL"          # ALL / VLP_ONLY / BESS_ONLY
    gsp: str | None = None
    dno: str | None = None
    interconnectors: str | None = None
    heatmap: bool = False
    timeline: bool = False

@app.get("/api/status")
async def status():
    return {"status": "ok"}

@app.post("/api/run_dashboard")
async def api_run_dashboard(filters: DashboardFilters):
    try:
        LOGGER.info("API run_dashboard called with %s", filters.dict())
        run_dashboard(filters.dict())
        return JSONResponse({"status": "success"})
    except Exception as e:
        LOGGER.exception("run_dashboard failed: %s", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/map")
async def serve_map():
    path = f"{OUT_DIR}/map.html"
    if not os.path.exists(path):
        return JSONResponse({"error": "Map not generated"}, status_code=404)
    return FileResponse(path)

@app.get("/chart/{name}")
async def serve_chart(name: str):
    path = f"{OUT_DIR}/{name}.png"
    if not os.path.exists(path):
        return JSONResponse({"error": "Chart not found"}, status_code=404)
    return FileResponse(path)

# Attach static front-end
from webui.app import router as web_router  # noqa

app.mount("/static", StaticFiles(directory="webui/static"), name="static")
app.include_router(web_router, prefix="")
