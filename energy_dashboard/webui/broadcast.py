import json
from typing import Dict, Any
from fastapi import WebSocket
from utils.logging_utils import get_logger

LOGGER = get_logger(__name__)
active_connections: set[WebSocket] = set()

async def register(ws: WebSocket):
    await ws.accept()
    active_connections.add(ws)

def unregister(ws: WebSocket):
    active_connections.discard(ws)

async def broadcast_update(payload: Dict[str, Any]):
    if not active_connections:
        return
    msg = json.dumps(payload, default=str)
    for ws in list(active_connections):
        try:
            await ws.send_text(msg)
        except Exception as e:
            LOGGER.warning("WebSocket send failed: %s", e)
            unregister(ws)
