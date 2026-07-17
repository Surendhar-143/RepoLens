from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    TokenResponse,
    UserResponse,
    PasswordChange,
    ProfileUpdate
)
from app.services.auth import AuthService
from app.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register_user(db, data)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    auth_data = await AuthService.authenticate_user(db, data)
    return TokenResponse(
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"]
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService.refresh_tokens(db, data.refresh_token)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"]
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)):
    # Simply return OK; client handles deleting token on logout
    return {"success": True, "message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.change_password(db, current_user, data)
    return {"success": True, "message": "Password updated successfully."}


@router.patch("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated = await AuthService.update_profile(db, current_user, data)
    return updated


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.delete_user_account(db, current_user)
    return {"success": True, "message": "Account deleted successfully."}
