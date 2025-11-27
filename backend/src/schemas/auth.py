from pydantic import BaseModel, EmailStr, constr


class RegisterSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str
