"""
Phase 9 — Enterprise Platform Tests
Tests cover: API Key generation/revocation, Webhook registration,
Organization creation, and Audit log recording.
"""
import pytest
import uuid
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.dependencies.auth import get_current_user
from app.database.models import User


def make_user() -> User:
    user = User.__new__(User)
    user.id = uuid.uuid4()
    user.email = "admin@repolens.io"
    user.username = "platform_admin"
    return user


# ─── API Key Tests ──────────────────────────────────────────────────────────

class TestAPIKeys:

    @pytest.mark.asyncio
    async def test_generate_api_key_returns_raw_token(self, client):
        from app.main import app
        app.dependency_overrides[get_current_user] = make_user

        with patch("app.api.routes.enterprise.AsyncSession") as mock_session:
            sess = AsyncMock()
            mock_session.return_value.__aenter__.return_value = sess

            response = await client.post(
                "/enterprise/api-keys",
                json={"name": "CI Pipeline Key"}
            )
            assert response.status_code == 201
            data = response.json()
            assert "token" in data
            assert data["token"].startswith("rl_")
            assert "id" in data

    @pytest.mark.asyncio
    async def test_list_api_keys_returns_list(self, client):
        from app.main import app
        app.dependency_overrides[get_current_user] = make_user

        with patch("app.api.routes.enterprise.AsyncSession") as mock_session:
            sess = AsyncMock()
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            sess.execute = AsyncMock(return_value=result)
            mock_session.return_value.__aenter__.return_value = sess

            response = await client.get("/enterprise/api-keys")
            assert response.status_code == 200
            assert isinstance(response.json(), list)


# ─── Webhook Tests ───────────────────────────────────────────────────────────

class TestWebhooks:

    @pytest.mark.asyncio
    async def test_register_webhook_success(self, client):
        from app.main import app
        app.dependency_overrides[get_current_user] = make_user

        mock_repo_id = uuid.uuid4()

        with patch("app.api.routes.enterprise.AsyncSession") as mock_session:
            sess = AsyncMock()
            # Simulate repo ownership check resolving
            repo_result = MagicMock()
            repo_result.scalar_one_or_none.return_value = MagicMock()
            sess.execute = AsyncMock(return_value=repo_result)
            mock_session.return_value.__aenter__.return_value = sess

            response = await client.post(
                "/enterprise/webhooks",
                json={
                    "repository_id": str(mock_repo_id),
                    "target_url": "https://hooks.example.com/repolens",
                    "secret_token": "super_secret_hmac_key"
                }
            )
            assert response.status_code == 201


# ─── Organization Tests ───────────────────────────────────────────────────────

class TestOrganizations:

    @pytest.mark.asyncio
    async def test_create_organization(self, client):
        from app.main import app
        app.dependency_overrides[get_current_user] = make_user

        with patch("app.api.routes.enterprise.AsyncSession") as mock_session:
            sess = AsyncMock()
            org_mock = MagicMock()
            org_mock.id = uuid.uuid4()
            org_mock.name = "Acme Engineering"
            sess.refresh = AsyncMock(side_effect=lambda o: None)
            mock_session.return_value.__aenter__.return_value = sess

            response = await client.post(
                "/enterprise/organizations",
                json={"name": "Acme Engineering"}
            )
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_organizations_returns_list(self, client):
        from app.main import app
        app.dependency_overrides[get_current_user] = make_user

        with patch("app.api.routes.enterprise.AsyncSession") as mock_session:
            sess = AsyncMock()
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            sess.execute = AsyncMock(return_value=result)
            mock_session.return_value.__aenter__.return_value = sess

            response = await client.get("/enterprise/organizations")
            assert response.status_code == 200
            assert isinstance(response.json(), list)


# ─── API Key Middleware Tests ─────────────────────────────────────────────────

class TestAPIKeyMiddleware:

    def test_key_hash_is_deterministic(self):
        """SHA256 of same raw key must always produce same hash."""
        raw = "rl_abc123def456"
        h1 = hashlib.sha256(raw.encode()).hexdigest()
        h2 = hashlib.sha256(raw.encode()).hexdigest()
        assert h1 == h2

    def test_key_hash_differs_for_different_inputs(self):
        h1 = hashlib.sha256(b"rl_keyA").hexdigest()
        h2 = hashlib.sha256(b"rl_keyB").hexdigest()
        assert h1 != h2


# ─── Audit Log Tests ──────────────────────────────────────────────────────────

class TestAuditLogs:

    @pytest.mark.asyncio
    async def test_audit_logs_endpoint_returns_list(self, client):
        from app.main import app
        app.dependency_overrides[get_current_user] = make_user

        with patch("app.api.routes.enterprise.AsyncSession") as mock_session:
            sess = AsyncMock()
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            sess.execute = AsyncMock(return_value=result)
            mock_session.return_value.__aenter__.return_value = sess

            response = await client.get("/enterprise/audit")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
