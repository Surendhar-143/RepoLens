import logging
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.services.github import GitHubService
from app.core.security import create_access_token, create_refresh_token, decode_access_token
from app.database.models import User, Settings
from app.core.exceptions import AuthenticationError, RepoLensException
from app.core.config import settings

logger = logging.getLogger("repolens.github_routes")
router = APIRouter(prefix="/github", tags=["GitHub Integration"])


@router.get("/connect", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def connect_github(
    state: str | None = Query(None, description="Optional access token to connect account to current session")
):
    """Redirect user to GitHub OAuth login page"""
    # Create authorize redirect URL
    client_id = settings.GITHUB_CLIENT_ID or "mock_client_id"
        
    redirect_uri = "http://localhost:8000/api/v1/github/callback"
    state_val = state if state else "login"
    
    auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&state={state_val}&scope=user,repo"
    return RedirectResponse(url=auth_url)


@router.get("/callback", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def github_callback(
    code: str,
    state: str = "login",
    db: AsyncSession = Depends(get_db)
):
    """Handle callback from GitHub, connect user account or perform session login"""
    try:
        # 1. Exchange OAuth code for GitHub token
        access_token = await GitHubService.exchange_oauth_code(code)
        
        # 2. Check if we are connecting an active session or performing login
        if state and state != "login":
            # Attempt to decode state as user access token
            user_id = decode_access_token(state)
            if not user_id:
                raise AuthenticationError("OAuth state verification failed. Invalid user session.")
                
            # Connect GitHub account to current session
            user_query = await db.execute(select(User).where(User.id == user_id))
            user = user_query.scalar_one_or_none()
            if not user:
                raise AuthenticationError("User session not found.")
                
            await GitHubService.connect_github_account(db, user, access_token)
            return RedirectResponse(url="http://localhost:3000/dashboard/settings?connected=true")
            
        else:
            # Execute login flow (fetch user info, log in or register if email is new)
            profile = await GitHubService.get_github_user_profile(access_token)
            email = profile.get("email")
            if not email:
                email = f"{profile['login']}@github.repolens.com"
                
            user_query = await db.execute(select(User).where(User.email == email))
            user = user_query.scalar_one_or_none()
            
            if not user:
                # Auto register new user
                user = User(
                    email=email,
                    username=profile["login"],
                    name=profile.get("name"),
                    avatar_url=profile.get("avatar_url"),
                    github_username=profile["login"],
                    provider="github"
                )
                db.add(user)
                await db.flush()
                
                # Default settings
                default_settings = Settings(
                    user_id=user.id,
                    theme="dark",
                    preferences={}
                )
                db.add(default_settings)
                await db.commit()
                await db.refresh(user)
            
            # Connect GitHub Account
            await GitHubService.connect_github_account(db, user, access_token)
            
            # Generate JWT credentials
            acc_token = create_access_token(user.id)
            ref_token = create_refresh_token(user.id)
            
            # Redirect to web app dashboard with tokens
            return RedirectResponse(
                url=f"http://localhost:3000/dashboard?access_token={acc_token}&refresh_token={ref_token}"
            )
            
    except Exception as e:
        logger.error(f"GitHub OAuth callback failure: {str(e)}", exc_info=True)
        return RedirectResponse(url="http://localhost:3000/login?error=github_auth_failed")


@router.delete("/disconnect", status_code=status.HTTP_200_OK)
async def disconnect_github(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect GitHub account links from active user profile"""
    await GitHubService.disconnect_github_account(db, current_user)
    return {"success": True, "message": "GitHub account disconnected successfully."}


@router.get("/repositories", status_code=status.HTTP_200_OK)
async def get_github_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List authenticated user's remote repositories from GitHub API"""
    # Fetch connected account tokens
    github_acc = current_user.github_account
    if not github_acc:
        raise RepoLensException("GITHUB_NOT_CONNECTED", "GitHub account is not connected.", 400)
        
    repos = await GitHubService.get_user_repositories(github_acc.access_token)
    return {"success": True, "repositories": repos}
