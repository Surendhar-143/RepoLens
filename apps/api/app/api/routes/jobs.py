import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, RepositoryImport
from app.schemas.repository import JobStatusResponse
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])
logger = logging.getLogger("repolens.jobs_routes")


@router.get("/{id}", response_model=JobStatusResponse, status_code=status.HTTP_200_OK)
async def get_job_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check status, progress, and messages from background task jobs"""
    # Query database for matching import job ID
    # A user can only check jobs for repos they own
    query = (
        select(RepositoryImport)
        .join(RepositoryImport.repository)
        .where(
            RepositoryImport.job_id == id,
            RepositoryImport.repository.has(user_id=current_user.id)
        )
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        # Fallback check by repository_import primary key UUID
        try:
            uuid_val = __import__("uuid").UUID(id)
            query_uuid = (
                select(RepositoryImport)
                .join(RepositoryImport.repository)
                .where(
                    RepositoryImport.id == uuid_val,
                    RepositoryImport.repository.has(user_id=current_user.id)
                )
            )
            res_uuid = await db.execute(query_uuid)
            job = res_uuid.scalar_one_or_none()
        except ValueError:
            pass

    if not job:
        raise NotFoundError("Job")

    return JobStatusResponse(
        job_id=job.job_id or str(job.id),
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
