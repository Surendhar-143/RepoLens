import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    name: str | None = Field(None, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str | None
    name: str | None
    avatar_url: str | None
    github_username: str | None
    provider: str
    created_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class ProfileUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    avatar_url: str | None = Field(None, max_length=500)
