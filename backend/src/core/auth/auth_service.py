from fastapi import HTTPException, status
from sqlalchemy.future import select

from core.auth.utils import hash_password, verify_password, create_access_token, create_refresh_token
from db.models.user_model import UserModel
from schemas.auth import RegisterSchema, LoginSchema, TokenResponse


class AuthService:
    """User Authentication and Registration Service"""

    @staticmethod
    async def register_user(data: RegisterSchema, db):
        q = await db.execute(select(UserModel).where(UserModel.email == data.email))
        if q.scalar():
            raise HTTPException(status_code=400, detail="User already exists")

        user = UserModel(email=data.email, hashed_password=hash_password(data.password))
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {"id": user.id, "email": user.email}

    @staticmethod
    async def login_user(data: LoginSchema, db) -> TokenResponse:
        q = await db.execute(select(UserModel).where(UserModel.email == data.email))
        user = q.scalar_one_or_none()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(str(user.id))
        refresh_token = await create_refresh_token(user.id, db)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
