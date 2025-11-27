from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from db.models.refresh_token_model import RefreshTokenModel
from core.auth.utils import create_access_token


class TokenService:
    """Token Management Service (refresh / logout)"""

    @staticmethod
    async def refresh_access_token(refresh_token: str, db: AsyncSession):
        """Creates a new access token based on the refresh token"""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == refresh_token)
        result = await db.execute(stmt)
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        token_expires = token_obj.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)

        if token_expires < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired refresh token"
            )

        new_access = create_access_token(str(token_obj.user_id))
        return {"access_token": new_access, "token_type": "bearer"}

    @staticmethod
    async def logout(refresh_token: str, db: AsyncSession):
        """Deletes the refresh token (logout)"""
        await db.execute(delete(RefreshTokenModel).where(RefreshTokenModel.token == refresh_token))
        await db.commit()
        return {"detail": "Logged out"}
