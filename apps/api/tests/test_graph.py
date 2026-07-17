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
async def test_get_graph_data(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.graph.AsyncSession.execute") as mock_execute:
        # Mock database select repository check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        
        # Mock adapter get_nodes and get_edges calls
        mock_nodes = [
            {"id": "node-1", "name": "app", "type": "folder", "parent_id": None, "file_path": "/app", "language": None, "metadata_json": {}},
            {"id": "node-2", "name": "main.py", "type": "file", "parent_id": "node-1", "file_path": "/app/main.py", "language": "Python", "metadata_json": {}}
        ]
        mock_edges = [
            {"id": "edge-1", "source_id": "node-2", "target_id": "node-1", "edge_type": "BELONGS_TO", "strength": 1.0, "metadata_json": {}}
        ]
        
        mock_execute.return_value = mock_result
        
        with patch("repolens.graph.postgres_adapter.PostgresGraphAdapter.get_nodes", return_value=mock_nodes), \
             patch("repolens.graph.postgres_adapter.PostgresGraphAdapter.get_edges", return_value=mock_edges):
             
            response = await client.get(f"/repositories/{mock_repo_id}/graph")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "edges" in data
            assert len(data["nodes"]) == 2
            assert data["nodes"][0]["position"] is not None


@pytest.mark.asyncio
async def test_get_metrics(client):
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    mock_repo_id = uuid.uuid4()
    
    with patch("app.api.routes.graph.AsyncSession.execute") as mock_execute:
        # Mock database select repository check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_execute.return_value = mock_result
        
        # Mock adapter get_nodes/get_edges
        with patch("repolens.graph.postgres_adapter.PostgresGraphAdapter.get_nodes", return_value=[]), \
             patch("repolens.graph.postgres_adapter.PostgresGraphAdapter.get_edges", return_value=[]):
             
            response = await client.get(f"/repositories/{mock_repo_id}/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "coupling" in data
            assert "cohesion" in data
            assert "circular_dependencies" in data
