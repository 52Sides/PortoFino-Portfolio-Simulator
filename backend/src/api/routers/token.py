from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.token_service import TokenService
from db.database import get_db
from schemas.auth import LogoutRequest, RefreshRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/refresh")
async def refresh_access_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    return await TokenService.refresh_access_token(data.refresh_token, db)


@router.post("/logout")
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    """Deletes the refresh token (logout)"""
    return await TokenService.logout(data.refresh_token, db)
