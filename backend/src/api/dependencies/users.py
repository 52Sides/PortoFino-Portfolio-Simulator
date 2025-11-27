import logging

from jose import JWTError
from fastapi import Depends, WebSocket, WebSocketException, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.utils import decode_token
from db.database import get_db
from db.models.user_model import UserModel

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    """
    Returns the current user if the token is valid
    Used for secure endpoints.
    """
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    q = await db.execute(select(UserModel).where(UserModel.id == int(user_id)))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


async def get_current_user_ws(
    ws: WebSocket,
    db: AsyncSession = Depends(get_db)
) -> UserModel | None:
    """
    WebSocket version of get_current_user.
    Does NOT close the websocket — raises WebSocketException instead.
    """
    token = ws.query_params.get("token")
    if not token:
        logger.warning("[WebSocket] No token provided")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        logger.warning("[WebSocket] Invalid token")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user = await db.get(UserModel, user_id)
    if not user:
        logger.warning(f"[WebSocket] User not found: {user_id}")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return user
