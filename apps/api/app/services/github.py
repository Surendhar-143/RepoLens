import logging
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import RepoLensException
from app.database.models import GitHubAccount, User

logger = logging.getLogger("repolens.github_service")


class GitHubService:
    @staticmethod
    async def exchange_oauth_code(code: str) -> str:
        """Exchange OAuth code for GitHub Access Token"""
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            # For development purposes, if credentials aren't set, return mock token
            logger.warning("GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET is missing. Defaulting to mock token.")
            return "mock_github_access_token_12345"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "code": code,
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise RepoLensException(
                        "GITHUB_OAUTH_ERROR", 
                        f"GitHub OAuth error: {data.get('error_description', data['error'])}", 
                        400
                    )
                
                return data["access_token"]
            except httpx.HTTPError as e:
                logger.error(f"Failed to communicate with GitHub OAuth endpoint: {str(e)}")
                raise RepoLensException("GITHUB_CONNECTION_FAILED", "Failed to connect to GitHub OAuth server.", 502)

    @staticmethod
    async def get_github_user_profile(access_token: str) -> dict:
        """Fetch GitHub authenticated user profile metadata"""
        if access_token == "mock_github_access_token_12345":
            return {
                "id": "999999",
                "login": "repolens-dev",
                "name": "RepoLens Local Developer",
                "email": "dev@repolens.local",
                "avatar_url": "https://avatars.githubusercontent.com/u/999999?v=4"
            }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json",
                        "User-Agent": "RepoLens-Code-Intelligence-Platform"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                profile = response.json()
                
                # Fetch email if private
                if not profile.get("email"):
                    email_resp = await client.get(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"token {access_token}",
                            "Accept": "application/json",
                            "User-Agent": "RepoLens-Code-Intelligence-Platform"
                        },
                        timeout=5.0
                    )
                    if email_resp.status_code == 200:
                        emails = email_resp.json()
                        primary_email = next((e["email"] for e in emails if e["primary"] and e["verified"]), None)
                        if primary_email:
                            profile["email"] = primary_email
                
                return profile
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch GitHub profile details: {str(e)}")
                raise RepoLensException("GITHUB_API_ERROR", "Failed to retrieve user profile from GitHub API.", 502)

    @staticmethod
    async def get_user_repositories(access_token: str) -> list[dict]:
        """Fetch list of user's remote repositories from GitHub"""
        if access_token == "mock_github_access_token_12345":
            return [
                {
                    "name": "RepoLens",
                    "owner": "Surendhar-143",
                    "description": "AI-powered Codebase Intelligence Platform.",
                    "visibility": "public",
                    "default_branch": "main",
                    "languages": {"TypeScript": 10000, "Python": 8000},
                    "clone_url": "https://github.com/Surendhar-143/RepoLens.git",
                    "size": 1250,
                    "stars": 42,
                    "forks": 12,
                    "updated_at": "2026-07-17T12:00:00Z"
                },
                {
                    "name": "sample-project",
                    "owner": "repolens-dev",
                    "description": "A demo repository for parsing checks.",
                    "visibility": "private",
                    "default_branch": "master",
                    "languages": {"Go": 5000},
                    "clone_url": "https://github.com/repolens-dev/sample-project.git",
                    "size": 430,
                    "stars": 2,
                    "forks": 0,
                    "updated_at": "2026-07-16T10:00:00Z"
                }
            ]

        async with httpx.AsyncClient() as client:
            try:
                # Retrieve repos (includes owned and collab repos)
                repos_list = []
                page = 1
                while True:
                    response = await client.get(
                        f"https://api.github.com/user/repos?per_page=100&page={page}&sort=updated",
                        headers={
                            "Authorization": f"token {access_token}",
                            "Accept": "application/json",
                            "User-Agent": "RepoLens-Code-Intelligence-Platform"
                        },
                        timeout=15.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    if not data:
                        break
                    
                    for r in data:
                        repos_list.append({
                            "name": r["name"],
                            "owner": r["owner"]["login"],
                            "description": r.get("description"),
                            "visibility": "private" if r.get("private") else "public",
                            "default_branch": r.get("default_branch", "main"),
                            "clone_url": r.get("clone_url"),
                            "size": r.get("size", 0),
                            "stars": r.get("stargazers_count", 0),
                            "forks": r.get("forks_count", 0),
                            "updated_at": r.get("updated_at")
                        })
                    
                    if len(data) < 100:
                        break
                    page += 1
                
                return repos_list
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch GitHub user repositories: {str(e)}")
                raise RepoLensException("GITHUB_API_ERROR", "Failed to retrieve remote repository list from GitHub.", 502)

    @staticmethod
    async def connect_github_account(db: AsyncSession, user: User, access_token: str) -> GitHubAccount:
        # Fetch GitHub User Details
        github_profile = await GitHubService.get_github_user_profile(access_token)
        
        # Check if already connected by another user
        account_query = await db.execute(
            select(GitHubAccount).where(GitHubAccount.github_user_id == str(github_profile["id"]))
        )
        existing = account_query.scalar_one_or_none()
        if existing and existing.user_id != user.id:
            raise RepoLensException("GITHUB_ALREADY_CONNECTED", "This GitHub account is already connected to another user.", 400)

        if not existing:
            existing = GitHubAccount(
                user_id=user.id,
                github_user_id=str(github_profile["id"]),
                github_username=github_profile["login"],
                avatar_url=github_profile.get("avatar_url"),
                access_token=access_token
            )
            db.add(existing)
        else:
            existing.access_token = access_token
            existing.github_username = github_profile["login"]
            existing.avatar_url = github_profile.get("avatar_url")
            existing.updated_at = datetime.utcnow()

        user.github_username = github_profile["login"]
        user.avatar_url = github_profile.get("avatar_url") if not user.avatar_url else user.avatar_url
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(existing)
        return existing

    @staticmethod
    async def disconnect_github_account(db: AsyncSession, user: User) -> None:
        account_query = await db.execute(select(GitHubAccount).where(GitHubAccount.user_id == user.id))
        github_acc = account_query.scalar_one_or_none()
        
        if not github_acc:
            raise RepoLensException("GITHUB_NOT_CONNECTED", "No GitHub account is connected to this profile.", 404)
            
        await db.delete(github_acc)
        user.github_username = None
        user.updated_at = datetime.utcnow()
        await db.commit()
