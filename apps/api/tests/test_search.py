import pytest
import uuid
from unittest.mock import patch, MagicMock

# Auth overrides
from app.api.dependencies.auth import get_current_user
from app.database.models import User

async def mock_get_current_user():
    user = User(
        email="developer@repolens.com",
        username="repolens-dev",
        name="RepoLens Dev"
    )
    user.id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
    return user


@pytest.mark.asyncio
async def test_hybrid_search_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    # Mock database select repository check and search history insert
    with patch("app.api.routes.search.AsyncSession.execute") as mock_execute, \
         patch("app.api.routes.search.AsyncSession.commit") as mock_commit:
         
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_execute.return_value = mock_result
        
        # Mock searcher results return
        mock_search_results = [
            {
                "title": "Auth Middleware",
                "type": "class",
                "file_id": "file-abc",
                "file_path": "/app/auth.py",
                "content_preview": "class AuthMiddleware...",
                "score": 0.95,
                "metadata": {}
            }
        ]
        
        with patch("repolens.search.hybrid_searcher.HybridSearcher.search", return_value=mock_search_results):
            response = await client.post(
                "/search",
                json={
                    "repository_id": str(mock_repo_id),
                    "query": "authentication middleware",
                    "limit": 5
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Auth Middleware"
            assert data[0]["score"] == 0.95


@pytest.mark.asyncio
async def test_search_history_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("app.api.routes.search.AsyncSession.execute") as mock_execute:
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(query="JWT auth", created_at="2026-07-17T12:00:00Z"),
            MagicMock(query="db init", created_at="2026-07-17T12:05:00Z")
        ]
        mock_execute.return_value = mock_result
        
        response = await client.get("/search/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["query"] == "JWT auth"
