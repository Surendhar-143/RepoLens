import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User
from app.schemas.repository import (
    RepositoryGitHubImport,
    RepositoryResponse,
    RepositoryUpdate
)
from app.services.repositories import RepositoryService
from app.core.exceptions import RepoLensException

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("", response_model=List[RepositoryResponse], status_code=status.HTTP_200_OK)
async def list_repositories(
    search: str | None = Query(None, description="Filter repositories by name or description"),
    visibility: str | None = Query(None, description="Filter by visibility (public, private)"),
    import_method: str | None = Query(None, description="Filter by import type (github, upload)"),
    sort_by: str = Query("recent", description="Sort by 'recent', 'name', 'updated'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List authenticated user's workspace repositories"""
    repos = await RepositoryService.list_repositories(
        db, current_user, search, visibility, import_method, None, sort_by, skip, limit
    )
    return repos


@router.post("/github", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def import_github_repository(
    data: RepositoryGitHubImport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import a public repository from GitHub using URL clone details"""
    repo = await RepositoryService.create_github_import(db, current_user, data)
    return repo


@router.post("/upload", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def upload_local_repository(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a local codebase repository as a ZIP archive"""
    if not file.filename.endswith(".zip"):
        raise RepoLensException("INVALID_FILE_TYPE", "Only ZIP archive files are allowed.", 400)
        
    content = await file.read()
    # Check max file size limit (50MB = 50 * 1024 * 1024)
    if len(content) > 50 * 1024 * 1024:
        raise RepoLensException("FILE_TOO_LARGE", "The uploaded ZIP file exceeds the maximum limit of 50MB.", 400)

    repo = await RepositoryService.create_zip_import(db, current_user, file.filename, content)
    return repo


@router.get("/{id}", response_model=RepositoryResponse, status_code=status.HTTP_200_OK)
async def get_repository_details(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get metadata details of an index repository"""
    repo = await RepositoryService.get_repository(db, current_user, id)
    return repo


@router.patch("/{id}", response_model=RepositoryResponse, status_code=status.HTTP_200_OK)
async def update_repository_metadata(
    id: uuid.UUID,
    data: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update settings or details of a workspace repository"""
    repo = await RepositoryService.update_repository(db, current_user, id, data)
    return repo


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_repository(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a repository and clear files from the local storage cache"""
    await RepositoryService.delete_repository(db, current_user, id)
    return {"success": True, "message": "Repository deletion initiated successfully."}


@router.post("/{id}/refresh", status_code=status.HTTP_200_OK)
async def refresh_repository(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger background metadata and commits updates on a repository"""
    job_info = await RepositoryService.refresh_repository(db, current_user, id)
    return {
        "success": True,
        "message": "Repository refresh job enqueued.",
        "job_id": job_info.job_id
    }
