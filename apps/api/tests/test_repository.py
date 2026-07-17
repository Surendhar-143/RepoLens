import pytest
from unittest.mock import patch, MagicMock

# Dependency override user verification bypass
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
@patch("app.api.routes.repositories.RepositoryService.list_repositories")
async def test_list_repositories(mock_list, client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_list.return_value = []

    response = await client.get("/repositories")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@patch("app.api.routes.repositories.RepositoryService.create_github_import")
async def test_import_github_repository(mock_import, client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user

    mock_repo = MagicMock()
    mock_repo.id = "b2b2b2b2-b2b2-b2b2-b2b2-b2b2b2b2b2b2"
    mock_repo.name = "RepoLens"
    mock_repo.owner = "Surendhar-143"
    mock_repo.description = "AI codebase platforms"
    mock_repo.visibility = "public"
    mock_repo.default_branch = "main"
    mock_repo.languages = {}
    mock_repo.clone_url = "https://github.com/Surendhar-143/RepoLens.git"
    mock_repo.local_path = "/workspace_cache/repo"
    mock_repo.size = 0
    mock_repo.last_commit_hash = None
    mock_repo.last_commit_message = None
    mock_repo.last_commit_at = None
    mock_repo.import_method = "github"
    mock_repo.created_at = "2026-07-17T12:00:00Z"
    mock_repo.updated_at = "2026-07-17T12:00:00Z"
    mock_repo.settings = None
    mock_repo.tags = []
    mock_repo.import_status = "queued"
    mock_repo.import_progress = 0.0

    mock_import.return_value = mock_repo

    response = await client.post(
        "/repositories/github",
        json={"clone_url": "https://github.com/Surendhar-143/RepoLens.git"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "RepoLens"
    assert data["import_method"] == "github"
