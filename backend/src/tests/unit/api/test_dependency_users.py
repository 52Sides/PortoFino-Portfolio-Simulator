import pytest

from unittest.mock import AsyncMock, patch
from fastapi.exceptions import WebSocketException
from jose import JWTError

from api.dependencies.users import get_current_user_ws, UserModel


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ws_no_token():
    ws = AsyncMock()
    ws.query_params = {}

    with pytest.raises(WebSocketException) as exc:
        await get_current_user_ws(ws, db=AsyncMock())

    assert exc.value.code == 1008


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ws_invalid_token():
    ws = AsyncMock()
    ws.query_params = {"token": "badtoken"}

    with patch("api.dependencies.users.decode_token", side_effect=JWTError("boom")):
        with pytest.raises(WebSocketException) as exc:
            await get_current_user_ws(ws, db=AsyncMock())

    assert exc.value.code == 1008


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ws_user_not_found():
    ws = AsyncMock()
    ws.query_params = {"token": "validtoken"}

    fake_db = AsyncMock()
    fake_db.get.return_value = None

    with patch("api.dependencies.users.decode_token", return_value={"sub": "123"}):
        with pytest.raises(WebSocketException) as exc:
            await get_current_user_ws(ws, db=fake_db)

    assert exc.value.code == 1008


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ws_user_found():
    ws = AsyncMock()
    ws.query_params = {"token": "validtoken"}

    fake_user = UserModel(id=123, email="a@b.com")
    fake_db = AsyncMock()
    fake_db.get.return_value = fake_user

    with patch("api.dependencies.users.decode_token", return_value={"sub": "123"}):
        user = await get_current_user_ws(ws, db=fake_db)

    assert user == fake_user
