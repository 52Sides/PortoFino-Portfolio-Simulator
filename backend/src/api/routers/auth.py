from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from core.auth.auth_service import AuthService
from schemas.auth import RegisterSchema, LoginSchema, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(data: RegisterSchema, db: AsyncSession = Depends(get_db)):
    return await AuthService.register_user(data, db)


@router.post("/login", response_model=TokenResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    login_data = LoginSchema(email=form_data.username, password=form_data.password)
    return await AuthService.login_user(login_data, db)
