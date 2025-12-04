from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse
from pathlib import Path

from .broadcast import register, unregister

router = APIRouter()

TEMPLATES_DIR = Path(__file__).parent / "templates"

@router.get("/", response_class=HTMLResponse)
async def index():
    html = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await register(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        unregister(ws)
