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
async def test_get_conversations_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.ai.AsyncSession.execute") as mock_execute:
        # Mock DB response
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.get(f"/ai/conversations?repository_id={mock_repo_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_providers_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("app.api.routes.ai.AsyncSession.execute") as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_execute.return_value = mock_result
        
        response = await client.get("/ai/providers")
        assert response.status_code == 200
        data = response.json()
        assert "active_provider" in data
        assert "providers" in data
        assert len(data["providers"]) >= 2
