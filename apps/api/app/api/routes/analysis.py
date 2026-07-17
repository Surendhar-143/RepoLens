import uuid
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from arq import create_pool
from arq.connections import RedisSettings

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, RepositoryImport, AnalysisStatistics
from app.core.config import settings
from app.core.exceptions import NotFoundError, RepoLensException

router = APIRouter(prefix="/repositories", tags=["Code Analysis"])
logger = logging.getLogger("repolens.routes.analysis")


@router.post("/{id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_repository(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger deterministic static analysis of a code repository"""
    # Verify repository ownership
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

    # Insert a new import/analysis job tracking record
    analysis_job = RepositoryImport(
        repository_id=repo.id,
        status="queued",
        progress=0.0
    )
    db.add(analysis_job)
    await db.commit()

    try:
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        pool = await create_pool(redis_settings)
        job = await pool.enqueue_job("analyze_repository_task", str(repo.id), str(analysis_job.id))
        analysis_job.job_id = job.job_id
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to dispatch analyze_repository_task: {str(e)}")
        analysis_job.status = "failed"
        analysis_job.error_message = f"Enqueue failed: {str(e)}"
        await db.commit()

    return {
        "success": True,
        "message": "Repository analysis queued.",
        "job_id": analysis_job.job_id or str(analysis_job.id)
    }


@router.get("/{id}/analysis", status_code=status.HTTP_200_OK)
async def get_analysis_status(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve details and progress logs of the latest analysis task"""
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

    job_query = await db.execute(
        select(RepositoryImport)
        .where(RepositoryImport.repository_id == id)
        .order_by(desc(RepositoryImport.created_at))
        .limit(1)
    )
    job = job_query.scalar_one_or_none()
    if not job:
        return {"status": "none", "progress": 0.0, "error_message": None}

    return {
        "job_id": job.job_id or str(job.id),
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message,
        "updated_at": job.updated_at
    }


@router.get("/{id}/statistics", status_code=status.HTTP_200_OK)
async def get_repository_statistics(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve aggregated stats including LOC counts and files size summaries"""
    stats_query = await db.execute(
        select(AnalysisStatistics)
        .join(Repository)
        .where(
            AnalysisStatistics.repository_id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    stats = stats_query.scalar_one_or_none()
    if not stats:
        return {"loc": 0, "files_count": 0, "folders_count": 0, "languages": {}, "frameworks": []}

    return {
        "loc": stats.loc,
        "files_count": stats.files_count,
        "folders_count": stats.folders_count,
        "languages": stats.languages_json,
        "frameworks": stats.frameworks_json
    }


@router.get("/{id}/languages", status_code=status.HTTP_200_OK)
async def get_repository_languages(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List codebase language distributions"""
    stats = await get_repository_statistics(id, current_user, db)
    return stats.get("languages", {})


@router.get("/{id}/frameworks", status_code=status.HTTP_200_OK)
async def get_repository_frameworks(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List detected codebase frameworks"""
    stats = await get_repository_statistics(id, current_user, db)
    return stats.get("frameworks", [])
