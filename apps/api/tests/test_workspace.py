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
async def test_get_workspace_state(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.workspace.AsyncSession.execute") as mock_execute, \
         patch("app.api.routes.workspace.AsyncSession.commit") as mock_commit:
         
        # Mock repo validation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_execute.return_value = mock_result
        
        response = await client.get(f"/workspace/{mock_repo_id}")
        assert response.status_code == 200
        data = response.json()
        assert "active_layout" in data


@pytest.mark.asyncio
async def test_annotations_crud(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.workspace.AsyncSession.execute") as mock_execute, \
         patch("app.api.routes.workspace.AsyncSession.commit") as mock_commit:
         
        # Mock insert return
        mock_execute.return_value = MagicMock()
        
        response = await client.post(
            "/workspace/annotations",
            json={
                "repository_id": str(mock_repo_id),
                "target_id": "auth.py",
                "note_type": "file",
                "content": "Verify JWT signature check parameters."
            }
        )
        assert response.status_code == 201
        assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_graph_export(client):
    response = await client.post(
        "/workspace/export",
        json={
            "format": "dot",
            "nodes": [{"id": "node-1", "label": "main.py"}],
            "edges": [{"source": "node-1", "target": "node-2"}]
        }
    )
    assert response.status_code == 200
    assert b"digraph CodebaseGraph" in response.content
