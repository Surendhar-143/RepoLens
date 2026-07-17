import uuid
from typing import Annotated
from fastapi import Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.database.models import User

# OAuth GitHub flow interface definition
class GitHubOAuthProvider:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_login_url(self, redirect_uri: str, state: str) -> str:
        return f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}&scope=user,repo"

    async def get_access_token(self, code: str, redirect_uri: str) -> str:
        # Abstract implementation to exchange code for token
        return "mock_github_access_token"

    async def get_user_profile(self, access_token: str) -> dict:
        # Mock retrieval of user info
        return {
            "id": "1234567",
            "email": "developer@repolens.com",
            "name": "RepoLens Developer"
        }


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None
) -> uuid.UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Authorization header is missing or invalid.")
        
    token = authorization.split(" ")[1]
    sub = decode_access_token(token)
    if not sub:
        raise AuthenticationError("Token is invalid or has expired.")
        
    try:
        return uuid.UUID(sub)
    except ValueError:
        raise AuthenticationError("Token payload is invalid.")


async def get_current_user(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("User session not found.")
    return user
