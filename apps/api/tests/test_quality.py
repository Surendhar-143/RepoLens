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
async def test_analyze_codebase_quality_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.quality.AsyncSession.execute") as mock_execute, \
         patch("app.api.routes.quality.AsyncSession.commit") as mock_commit:
         
        # Mock repo checking
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.post(
            "/quality/analyze",
            json={
                "repository_id": str(mock_repo_id)
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "quality" in data


@pytest.mark.asyncio
async def test_list_quality_findings(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.quality.AsyncSession.execute") as mock_execute:
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.get(f"/quality/findings?repository_id={mock_repo_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_rules_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("app.api.routes.quality.AsyncSession.execute") as mock_execute:
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.get("/quality/rules")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
