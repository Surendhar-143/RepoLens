import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, Settings
from app.schemas.auth import UserRegister, UserLogin, PasswordChange, ProfileUpdate
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_refresh_token
from app.core.exceptions import RepoLensException, AuthenticationError

logger = logging.getLogger("repolens.auth_service")


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, data: UserRegister) -> User:
        # Check duplicate email
        email_query = await db.execute(select(User).where(User.email == data.email))
        if email_query.scalar_one_or_none():
            raise RepoLensException("EMAIL_ALREADY_REGISTERED", "This email address is already in use.", 400)
            
        # Check duplicate username
        username_query = await db.execute(select(User).where(User.username == data.username))
        if username_query.scalar_one_or_none():
            raise RepoLensException("USERNAME_TAKEN", "This username is already taken.", 400)

        # Hash password and create user
        password_hash = get_password_hash(data.password)
        new_user = User(
            email=data.email,
            username=data.username,
            password_hash=password_hash,
            name=data.name,
            provider="local"
        )
        
        db.add(new_user)
        await db.flush()  # populate ID
        
        # Initialize default settings
        default_settings = Settings(
            user_id=new_user.id,
            theme="dark",
            preferences={}
        )
        db.add(default_settings)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.email}")
        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, data: UserLogin) -> dict:
        user_query = await db.execute(select(User).where(User.email == data.email))
        user = user_query.scalar_one_or_none()
        
        if not user or not user.password_hash:
            raise AuthenticationError("Invalid email or password.")
            
        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")

        # Update last login timestamp
        user.last_login_at = datetime.utcnow()
        await db.commit()

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }

    @staticmethod
    async def refresh_tokens(db: AsyncSession, token: str) -> dict:
        user_id_str = decode_refresh_token(token)
        if not user_id_str:
            raise AuthenticationError("Invalid or expired refresh token.")
            
        user_query = await db.execute(select(User).where(User.id == user_id_str))
        user = user_query.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User session not found.")

        # Generate new credentials
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    @staticmethod
    async def change_password(db: AsyncSession, user: User, data: PasswordChange) -> None:
        if not user.password_hash or not verify_password(data.old_password, user.password_hash):
            raise RepoLensException("INVALID_PASSWORD", "The current password entered is incorrect.", 400)
            
        user.password_hash = get_password_hash(data.new_password)
        user.updated_at = datetime.utcnow()
        await db.commit()

    @staticmethod
    async def update_profile(db: AsyncSession, user: User, data: ProfileUpdate) -> User:
        if data.name is not None:
            user.name = data.name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
            
        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user_account(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.commit()
        logger.info(f"User account deleted: {user.email}")
