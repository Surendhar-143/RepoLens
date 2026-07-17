import os
import uuid
import shutil
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.exceptions import RepoLensException, NotFoundError
from app.database.models import User, Repository, RepositoryImport, RepositorySettings, RepositoryTag
from app.schemas.repository import RepositoryGitHubImport, RepositoryUpdate

logger = logging.getLogger("repolens.repository_service")
CACHE_DIR = "c:\\Users\\ADK\\Desktop\\RepoLens\\workspace_cache"


class RepositoryService:
    @staticmethod
    async def _get_arq_pool():
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        return await create_pool(redis_settings)

    @staticmethod
    async def list_repositories(
        db: AsyncSession,
        user: User,
        search: str | None = None,
        visibility: str | None = None,
        import_method: str | None = None,
        language: str | None = None,
        sort_by: str = "recent",
        skip: int = 0,
        limit: int = 20
    ) -> list[Repository]:
        # Exclude soft deleted items
        query = select(Repository).where(
            and_(
                Repository.user_id == user.id,
                Repository.is_deleted == False
            )
        )

        # Filters
        if search:
            query = query.where(
                or_(
                    Repository.name.ilike(f"%{search}%"),
                    Repository.owner.ilike(f"%{search}%"),
                    Repository.description.ilike(f"%{search}%")
                )
            )
        if visibility:
            query = query.where(Repository.visibility == visibility)
        if import_method:
            query = query.where(Repository.import_method == import_method)

        # Sorting
        if sort_by == "name":
            query = query.order_by(Repository.name)
        elif sort_by == "updated":
            query = query.order_by(desc(Repository.updated_at))
        else: # default recent
            query = query.order_by(desc(Repository.created_at))

        result = await db.execute(query.offset(skip).limit(limit))
        repos = list(result.scalars().all())

        # Bind import status attributes manually for display
        for r in repos:
            # Fetch latest import status
            import_query = await db.execute(
                select(RepositoryImport)
                .where(RepositoryImport.repository_id == r.id)
                .order_by(desc(RepositoryImport.created_at))
                .limit(1)
            )
            latest_import = import_query.scalar_one_or_none()
            if latest_import:
                r.import_status = latest_import.status
                r.import_progress = latest_import.progress
            else:
                r.import_status = "none"
                r.import_progress = 0.0

        return repos

    @staticmethod
    async def get_repository(db: AsyncSession, user: User, repo_id: uuid.UUID) -> Repository:
        query = select(Repository).where(
            and_(
                Repository.id == repo_id,
                Repository.user_id == user.id,
                Repository.is_deleted == False
            )
        )
        result = await db.execute(query)
        repo = result.scalar_one_or_none()
        if not repo:
            raise NotFoundError("Repository")

        # Bind import status attributes
        import_query = await db.execute(
            select(RepositoryImport)
            .where(RepositoryImport.repository_id == repo.id)
            .order_by(desc(RepositoryImport.created_at))
            .limit(1)
        )
        latest_import = import_query.scalar_one_or_none()
        if latest_import:
            repo.import_status = latest_import.status
            repo.import_progress = latest_import.progress
        else:
            repo.import_status = "none"
            repo.import_progress = 0.0

        return repo

    @staticmethod
    async def create_github_import(db: AsyncSession, user: User, data: RepositoryGitHubImport) -> Repository:
        url_str = data.clone_url.strip()
        # Parse GitHub URL e.g. https://github.com/owner/repo
        if not url_str.startswith("https://github.com/"):
            raise RepoLensException("INVALID_GITHUB_URL", "Please enter a valid HTTPS GitHub repository URL.", 400)
            
        parts = url_str.replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            raise RepoLensException("INVALID_GITHUB_URL", "Could not parse repository owner and name.", 400)
            
        owner = parts[0]
        name = parts[1].replace(".git", "")

        # Check duplicate
        dup_query = await db.execute(
            select(Repository).where(
                and_(
                    Repository.user_id == user.id,
                    Repository.clone_url == url_str,
                    Repository.is_deleted == False
                )
            )
        )
        if dup_query.scalar_one_or_none():
            raise RepoLensException("DUPLICATE_IMPORT", "This repository is already imported in your workspace.", 400)

        # Allocate unique folder path in local cache
        repo_uuid = uuid.uuid4()
        local_path = os.path.join(CACHE_DIR, str(repo_uuid))

        # Create record
        repo = Repository(
            id=repo_uuid,
            user_id=user.id,
            name=name,
            owner=owner,
            clone_url=url_str,
            local_path=local_path,
            import_method="github"
        )
        db.add(repo)
        await db.flush()

        # Add settings
        repo_settings = RepositorySettings(
            repository_id=repo.id,
            is_auto_sync=False,
            sync_interval_hours=24
        )
        db.add(repo_settings)

        # Add Import job tracking record
        repo_import = RepositoryImport(
            repository_id=repo.id,
            status="queued",
            progress=0.0
        )
        db.add(repo_import)
        await db.commit()
        await db.refresh(repo)

        # Enqueue background clone task
        try:
            pool = await RepositoryService._get_arq_pool()
            job = await pool.enqueue_job("clone_repository_task", str(repo.id), url_str, local_path, str(repo_import.id))
            repo_import.job_id = job.job_id
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to enqueue arq clone job: {str(e)}")
            repo_import.status = "failed"
            repo_import.error_message = f"Background task enqueuing failed: {str(e)}"
            await db.commit()

        # Bind parameters
        repo.import_status = repo_import.status
        repo.import_progress = repo_import.progress
        return repo

    @staticmethod
    async def create_zip_import(db: AsyncSession, user: User, filename: str, file_content: bytes) -> Repository:
        # Create record
        repo_uuid = uuid.uuid4()
        name = filename.replace(".zip", "")
        local_path = os.path.join(CACHE_DIR, str(repo_uuid))

        repo = Repository(
            id=repo_uuid,
            user_id=user.id,
            name=name,
            owner="local-upload",
            local_path=local_path,
            import_method="upload"
        )
        db.add(repo)
        await db.flush()

        # Settings
        repo_settings = RepositorySettings(
            repository_id=repo.id,
            is_auto_sync=False,
            sync_interval_hours=24
        )
        db.add(repo_settings)

        # Job tracking
        repo_import = RepositoryImport(
            repository_id=repo.id,
            status="queued",
            progress=0.0
        )
        db.add(repo_import)
        await db.commit()
        await db.refresh(repo)

        # Write uploaded bytes to a temp zip location for worker processing
        temp_dir = os.path.join(CACHE_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_zip = os.path.join(temp_dir, f"{str(repo_uuid)}.zip")
        with open(temp_zip, "wb") as f:
            f.write(file_content)

        # Enqueue background zip extract task
        try:
            pool = await RepositoryService._get_arq_pool()
            job = await pool.enqueue_job("extract_zip_repository_task", str(repo.id), temp_zip, local_path, str(repo_import.id))
            repo_import.job_id = job.job_id
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to enqueue zip task: {str(e)}")
            repo_import.status = "failed"
            repo_import.error_message = f"Background task enqueuing failed: {str(e)}"
            await db.commit()

        repo.import_status = repo_import.status
        repo.import_progress = repo_import.progress
        return repo

    @staticmethod
    async def update_repository(db: AsyncSession, user: User, repo_id: uuid.UUID, data: RepositoryUpdate) -> Repository:
        repo = await RepositoryService.get_repository(db, user, repo_id)
        
        if data.name is not None:
            repo.name = data.name
        if data.description is not None:
            repo.description = data.description
            
        if repo.settings:
            if data.is_auto_sync is not None:
                repo.settings.is_auto_sync = data.is_auto_sync
            if data.sync_interval_hours is not None:
                repo.settings.sync_interval_hours = data.sync_interval_hours
        
        # Tags updates
        if data.tags is not None:
            # Delete existing tags
            await db.execute(
                __import__("sqlalchemy").delete(RepositoryTag).where(RepositoryTag.repository_id == repo.id)
            )
            for t_name in data.tags:
                tag = RepositoryTag(repository_id=repo.id, tag_name=t_name)
                db.add(tag)

        repo.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(repo)
        return await RepositoryService.get_repository(db, user, repo_id)

    @staticmethod
    async def refresh_repository(db: AsyncSession, user: User, repo_id: uuid.UUID) -> RepositoryImport:
        repo = await RepositoryService.get_repository(db, user, repo_id)

        # Enqueue refresh job
        repo_import = RepositoryImport(
            repository_id=repo.id,
            status="queued",
            progress=0.0
        )
        db.add(repo_import)
        await db.commit()

        try:
            pool = await RepositoryService._get_arq_pool()
            job = await pool.enqueue_job("refresh_repository_task", str(repo.id), repo.clone_url, repo.local_path, str(repo_import.id))
            repo_import.job_id = job.job_id
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to enqueue refresh: {str(e)}")
            repo_import.status = "failed"
            repo_import.error_message = f"Refresh enqueue failed: {str(e)}"
            await db.commit()

        return repo_import

    @staticmethod
    async def delete_repository(db: AsyncSession, user: User, repo_id: uuid.UUID) -> None:
        repo = await RepositoryService.get_repository(db, user, repo_id)
        
        # Soft delete in Postgres
        repo.is_deleted = True
        repo.deleted_at = datetime.utcnow()
        repo.updated_at = datetime.utcnow()
        await db.commit()

        # Enqueue file delete cleanup job
        try:
            pool = await RepositoryService._get_arq_pool()
            await pool.enqueue_job("delete_repository_files_task", repo.local_path)
        except Exception as e:
            logger.error(f"Failed to trigger delete cache task: {str(e)}")
            # Fallback direct delete (if worker is down, delete sync)
            if os.path.exists(repo.local_path):
                shutil.rmtree(repo.local_path, ignore_errors=True)
