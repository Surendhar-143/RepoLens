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
@patch("app.api.routes.analysis.create_pool")
async def test_trigger_analysis(mock_pool, client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # Mock arq connection pool
    mock_arq = MagicMock()
    mock_arq.enqueue_job.return_value = MagicMock(job_id="mock_job_id_abc")
    mock_pool.return_value = mock_arq

    # Mock repository select query
    mock_repo = MagicMock()
    mock_repo.id = uuid.uuid4()
    mock_repo.user_id = uuid.UUID("a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1")
    
    with patch("app.api.routes.analysis.AsyncSession.execute") as mock_execute:
        # Mock database select repository query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_repo
        mock_execute.return_value = mock_result
        
        response = await client.post(f"/repositories/{mock_repo.id}/analyze")
        assert response.status_code == 202
        assert response.json()["success"] is True
        assert "job_id" in response.json()


@pytest.mark.asyncio
async def test_get_files_tree(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.files.AsyncSession.execute") as mock_execute:
        # Mock database checks
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        response = await client.get(f"/repositories/{mock_repo_id}/files")
        assert response.status_code == 200
        data = response.json()
        assert "folders" in data
        assert "files" in data
