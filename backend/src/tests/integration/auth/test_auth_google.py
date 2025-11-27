import pytest
from unittest.mock import AsyncMock, patch

from core.config import settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_google_callback_creates_user(test_client, db_session):
    mock_userinfo = {"email": "google@test.com"}

    mock_resp = AsyncMock()
    mock_resp.json.return_value = mock_userinfo

    mock_oauth_client = AsyncMock()
    mock_oauth_client.authorize_access_token.return_value = {"access_token": "token"}
    mock_oauth_client.get.return_value = mock_resp
    mock_oauth_client.server_metadata = {"userinfo_endpoint": "https://example.com/userinfo"}

    with patch("core.auth.oauth_service.get_oauth_client", return_value=mock_oauth_client):
        r = await test_client.get("/auth/google/callback", follow_redirects=False)

        assert r.status_code == 307
        location = r.headers["location"]
        assert location.startswith(f"{settings.FRONTEND_URL}/oauth-callback")
        assert "access_token=" in location
        assert "refresh_token=" in location
