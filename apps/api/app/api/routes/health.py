from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import verify_redis_connection
from app.core.qdrant import verify_qdrant_connection
from app.core.config import settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def check_health(db: AsyncSession = Depends(get_db)):
    # Check Database Connection
    db_healthy = False
    try:
        await db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        pass
        
    # Check Redis
    redis_healthy = await verify_redis_connection()
    
    # Check Qdrant
    qdrant_healthy = await verify_qdrant_connection()

    all_healthy = db_healthy and redis_healthy and qdrant_healthy
    
    if not all_healthy:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "components": {
                    "database": "up" if db_healthy else "down",
                    "redis": "up" if redis_healthy else "down",
                    "qdrant": "up" if qdrant_healthy else "down"
                }
            }
        )

    return {
        "status": "healthy"
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "description": "RepoLens AI-powered Codebase Intelligence Platform API",
        "status": "online"
    }


@router.get("/version", status_code=status.HTTP_200_OK)
async def read_version():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "env": settings.ENV
    }
