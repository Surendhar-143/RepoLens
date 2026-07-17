import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch("app.api.routes.auth.AuthService.register_user")
async def test_user_registration(mock_register, client):
    # Mock user registration response
    mock_user = MagicMock()
    mock_user.id = "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
    mock_user.email = "test@repolens.com"
    mock_user.username = "testuser"
    mock_user.name = "Test User"
    mock_user.avatar_url = None
    mock_user.github_username = None
    mock_user.provider = "local"
    mock_user.created_at = "2026-07-17T12:00:00Z"
    mock_user.last_login_at = None
    
    mock_register.return_value = mock_user

    response = await client.post(
        "/auth/register",
        json={
            "email": "test@repolens.com",
            "username": "testuser",
            "password": "testpassword123",
            "name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@repolens.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
@patch("app.api.routes.auth.AuthService.authenticate_user")
async def test_user_login(mock_auth, client):
    mock_auth.return_value = {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "user": MagicMock()
    }

    response = await client.post(
        "/auth/login",
        json={
            "email": "test@repolens.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
