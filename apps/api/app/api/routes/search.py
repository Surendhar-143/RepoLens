import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, delete

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, SearchHistory, Symbol, RepositoryFile
from app.core.exceptions import NotFoundError
from app.core.config import settings

from repolens.embeddings.providers import OpenAIEmbeddingProvider, SentenceTransformersProvider
from repolens.search.hybrid_searcher import HybridSearcher

router = APIRouter(prefix="/search", tags=["Semantic Search Engine"])
logger = logging.getLogger("repolens.routes.search")


# Initialize default hybrid searcher
# Load key if OpenAI is configured, else fallback to SentenceTransformers / Mock
api_key = settings.OPENAI_API_KEY if hasattr(settings, "OPENAI_API_KEY") else None
embed_provider = None
if api_key:
    embed_provider = OpenAIEmbeddingProvider(api_key=api_key)
else:
    embed_provider = SentenceTransformersProvider()

searcher = HybridSearcher(
    qdrant_host=settings.QDRANT_HOST,
    qdrant_port=settings.QDRANT_PORT,
    qdrant_api_key=settings.QDRANT_API_KEY,
    embedding_provider=embed_provider
)


class SearchRequest(BaseModel):
    repository_id: uuid.UUID
    query: str = Field(..., min_length=1, max_length=500)
    chunk_type: Optional[str] = None # file, class, function, api, model
    limit: Optional[int] = 10


class SearchResultItem(BaseModel):
    title: str
    type: str
    file_id: str
    file_path: str
    content_preview: str
    score: float
    metadata: dict


@router.post("", response_model=List[SearchResultItem], status_code=status.HTTP_200_OK)
async def perform_hybrid_search(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute hybrid vector similarity and keyword query search across codebase elements"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == req.repository_id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Record search history
    hist = SearchHistory(
        user_id=current_user.id,
        query=req.query
    )
    db.add(hist)
    await db.commit()

    results = await searcher.search(
        db=db,
        repository_id=str(req.repository_id),
        query=req.query,
        limit=req.limit,
        chunk_type=req.chunk_type
    )

    return results


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve recent queries history list for the user"""
    query = (
        select(SearchHistory.query, SearchHistory.created_at)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(20)
    )
    res = await db.execute(query)
    history = []
    seen = set()
    for row in res.fetchall():
        if row.query not in seen:
            history.append({"query": row.query, "created_at": row.created_at})
            seen.add(row.query)
    return history


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete all queries history for the user"""
    await db.execute(
        delete(SearchHistory).where(SearchHistory.user_id == current_user.id)
    )
    await db.commit()


@router.get("/suggestions", status_code=status.HTTP_200_OK)
async def get_search_suggestions(
    repository_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List autocompletes suggestions for files and symbol names in the repository"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Match matching symbols names
    sym_query = await db.execute(
        select(Symbol.name)
        .join(RepositoryFile, Symbol.file_id == RepositoryFile.id)
        .where(RepositoryFile.repository_id == repository_id, Symbol.name.ilike(f"{q}%"))
        .limit(5)
    )
    suggestions = [row[0] for row in sym_query.all()]

    # Match files path
    file_query = await db.execute(
        select(RepositoryFile.name)
        .where(RepositoryFile.repository_id == repository_id, RepositoryFile.name.ilike(f"{q}%"))
        .limit(5)
    )
    suggestions.extend([row[0] for row in file_query.all()])

    return list(set(suggestions))[:7]
