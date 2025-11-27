from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import secrets
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models.refresh_token_model import RefreshTokenModel

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create JWT access token"""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expires,
        "iat": now,
        "jti": jti,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decoding a JWT, throwing a JWTError if the token is invalid"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise JWTError("Invalid or expired token") from e


async def create_refresh_token(user_id: int, db: AsyncSession) -> str:
    """Generate a new refresh token and delete old ones."""
    await db.execute(delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id))

    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshTokenModel(user_id=user_id, token=token, expires_at=expires_at))

    await db.commit()

    return token
