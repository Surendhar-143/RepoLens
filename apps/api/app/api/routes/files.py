import os
import uuid
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, RepositoryFolder, RepositoryFile
from app.core.exceptions import NotFoundError, RepoLensException

router = APIRouter(tags=["Codebase Files"])
logger = logging.getLogger("repolens.routes.files")


@router.get("/repositories/{id}/files", status_code=status.HTTP_200_OK)
async def get_repository_files_tree(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full lists of folders and files to render codebase hierarchies"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Fetch folders
    folders_query = await db.execute(
        select(RepositoryFolder).where(RepositoryFolder.repository_id == id)
    )
    folders = folders_query.scalars().all()

    # Fetch files
    files_query = await db.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == id)
    )
    files = files_query.scalars().all()

    return {
        "folders": [
            {
                "id": str(f.id),
                "parent_id": str(f.parent_id) if f.parent_id else None,
                "path": f.path,
                "name": f.name,
                "depth": f.depth,
                "size": f.size
            } for f in folders
        ],
        "files": [
            {
                "id": str(f.id),
                "folder_id": str(f.folder_id),
                "path": f.path,
                "name": f.name,
                "size": f.size,
                "mime_type": f.mime_type,
                "hash": f.hash
            } for f in files
        ]
    }


@router.get("/files/{id}", status_code=status.HTTP_200_OK)
async def get_file_content(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve file metadata details and raw text contents for coding viewports"""
    # Fetch file details, join Repository to verify user ownership
    file_query = await db.execute(
        select(RepositoryFile)
        .join(RepositoryFile.repository)
        .where(
            RepositoryFile.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    file_record = file_query.scalar_one_or_none()
    if not file_record:
        raise NotFoundError("File")

    # Read content from cached workspace directory
    # Verify local file path exists
    repo_local_path = file_record.repository.local_path
    absolute_filepath = os.path.join(repo_local_path, file_record.path)
    
    # Path traversal validation check
    if not os.path.abspath(absolute_filepath).startswith(os.path.abspath(repo_local_path)):
        raise RepoLensException("SECURITY_ERROR", "Unauthorized path access attempt.", 403)

    content = ""
    if os.path.exists(absolute_filepath):
        try:
            with open(absolute_filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read codebase file {absolute_filepath}: {str(e)}")
            raise RepoLensException("FILE_READ_FAILED", "Failed to retrieve local file content.", 500)
    else:
        raise NotFoundError("Physical File")

    return {
        "id": str(file_record.id),
        "name": file_record.name,
        "path": file_record.path,
        "size": file_record.size,
        "mime_type": file_record.mime_type,
        "content": content
    }
