import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "status" in data
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_read_version(client):
    response = await client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "env" in data


@pytest.mark.asyncio
@patch("app.api.routes.health.verify_redis_connection")
@patch("app.api.routes.health.verify_qdrant_connection")
async def test_health_endpoint(mock_qdrant, mock_redis, client):
    # Mock services as online
    mock_redis.return_value = True
    mock_qdrant.return_value = True

    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
