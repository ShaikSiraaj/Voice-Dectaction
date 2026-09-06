"""
Lets the React dashboard subscribe to live updates for a real phone call.

The Twilio stream handler (twilio_stream.py) processes audio and calls
broadcast_to_dashboard(call_id, payload) after each chunk; any frontend
client connected on /ws/dashboard/{call_id} receives that payload instantly.
"""
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

_subscribers: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/dashboard/{call_id}")
async def dashboard_socket(websocket: WebSocket, call_id: str):
    await websocket.accept()
    _subscribers.setdefault(call_id, []).append(websocket)
    logger.info(f"Dashboard client subscribed to call {call_id}")
    try:
        while True:
            await websocket.receive_text()  # dashboard doesn't need to send anything; just keep alive
    except WebSocketDisconnect:
        _subscribers[call_id].remove(websocket)
        logger.info(f"Dashboard client unsubscribed from call {call_id}")


async def broadcast_to_dashboard(call_id: str, payload: dict):
    for ws in list(_subscribers.get(call_id, [])):
        try:
            await ws.send_json(payload)
        except Exception:
            _subscribers[call_id].remove(ws)
