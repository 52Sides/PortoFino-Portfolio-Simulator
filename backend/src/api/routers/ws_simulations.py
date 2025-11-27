import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from starlette.websockets import WebSocketState

from api.dependencies.users import get_current_user_ws
from db.models.user_model import UserModel
from services.redis.client import redis_client
from services.redis.pubsub import get_pubsub

router = APIRouter(prefix="/ws", tags=["WebSocket Simulations"])

logger = logging.getLogger(__name__)


def ws_can_close(ws: WebSocket) -> bool:
    return ws.application_state != WebSocketState.DISCONNECTED


@router.websocket("/simulations/{task_id}")
async def websocket_simulation(
    ws: WebSocket,
    task_id: str,
    user: Optional[UserModel] = Depends(get_current_user_ws),
):
    await ws.accept()

    buffer_key = f"buffer:simulation:{task_id}"

    # --- Cached events ---
    cached = await redis_client.lrange_list(buffer_key, 0, -1)
    if cached:
        for raw in cached:
            event = json.loads(raw)
            if user and event.get("user_id") != user.id:
                continue

            await ws.send_text(json.dumps(event))

            if event.get("status") == "done":
                if ws_can_close(ws):
                    await ws.close()
                return

    # --- Stream events ---
    pubsub = get_pubsub("simulation", task_id)
    logger.info(f"[WS] Connected to simulation:{task_id}, user={getattr(user, 'id', None)}")

    try:
        async for event in pubsub.subscribe():
            if user and event.get("user_id") != user.id:
                continue

            await ws.send_text(json.dumps(event))

            if event.get("status") == "done":
                if ws_can_close(ws):
                    await ws.close()
                break

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info(f"[WS] Disconnected: simulation:{task_id}")

    except Exception as e:
        logger.exception(f"[WS] Error: {e}")
        if ws_can_close(ws):
            try:
                await ws.send_text(json.dumps({"error": str(e)}))
            except RuntimeError:
                pass

    finally:
        await pubsub.close()
        if ws_can_close(ws):
            try:
                await ws.close()
            except RuntimeError:
                pass
