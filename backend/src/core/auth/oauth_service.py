from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.utils import create_access_token, create_refresh_token
from core.auth.oauth import get_oauth_client
from core.config import settings
from db.models.user_model import UserModel


class OAuthService:
    """Authorization service through external providers (Google)"""

    @staticmethod
    async def google_login(request):
        """Initiates Google login"""
        oauth_client = get_oauth_client()
        redirect_uri = f"{settings.API_BASE_URL}/auth/google/callback"
        return await oauth_client.authorize_redirect(request, redirect_uri)

    @staticmethod
    async def google_callback(request, db: AsyncSession) -> dict:
        """Processes the Google OAuth response and issues tokens."""

        oauth_client = get_oauth_client()
        token = await oauth_client.authorize_access_token(request)

        userinfo_endpoint = oauth_client.server_metadata.get("userinfo_endpoint")
        if not userinfo_endpoint:
            raise HTTPException(500, "Google OAuth userinfo_endpoint not found")

        resp = await oauth_client.get(userinfo_endpoint, token=token)
        user_info = await resp.json()

        if not user_info:
            raise HTTPException(status_code=400, detail="Google OAuth failed")

        email = user_info["email"]

        q = await db.execute(select(UserModel).where(UserModel.email == email))
        user = q.scalar_one_or_none()

        if not user:
            user = UserModel(email=email, hashed_password=None)
            db.add(user)
            await db.flush()
            await db.refresh(user)
            await db.commit()

        ac_token = create_access_token(str(user.id))
        ref_token = await create_refresh_token(user.id, db)

        redirect_to = f"{settings.FRONTEND_URL}/oauth-callback?access_token={ac_token}&refresh_token={ref_token}"

        return RedirectResponse(url=redirect_to)
