from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.oauth_service import OAuthService
from db.database import get_db

router = APIRouter(prefix="/auth/google", tags=["OAuth"])


@router.get("/login")
async def google_login(request: Request):
    return await OAuthService.google_login(request)


@router.get("/callback", name="google_callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    return await OAuthService.google_callback(request, db)
