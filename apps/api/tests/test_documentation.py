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
async def test_generate_documentation_route(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.documentation.AsyncSession.execute") as mock_execute, \
         patch("app.api.routes.documentation.AsyncSession.commit") as mock_commit:
         
        # Mock repository ownership check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.post(
            "/documentation/generate",
            json={
                "repository_id": str(mock_repo_id),
                "doc_type": "architecture"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["doc_type"] == "architecture"
        assert "content" in data


@pytest.mark.asyncio
async def test_list_documentations(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.documentation.AsyncSession.execute") as mock_execute:
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.get(f"/documentation?repository_id={mock_repo_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_generate_health_reports(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.documentation.AsyncSession.execute") as mock_execute, \
         patch("app.api.routes.documentation.AsyncSession.commit") as mock_commit:
         
        mock_execute.return_value = MagicMock()
        
        response = await client.post(
            "/reports/generate",
            json={
                "repository_id": str(mock_repo_id),
                "report_type": "health"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "health"
        assert "# Repository Engineering Health Assessment" in data["content"]
