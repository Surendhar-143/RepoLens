import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db

# Override get_db for testing (returns a mock or stub context if database is down)
async def override_get_db() -> AsyncGenerator:
    # We yield a dummy object in mock test situations
    # For actual integration tests, we can supply a SQLite/Postgres test engine
    class MockSession:
        async def execute(self, *args, **kwargs):
            class Result:
                def scalar_one_or_none(self):
                    return None
            return Result()
        async def commit(self):
            pass
        async def rollback(self):
            pass
        async def close(self):
            pass
    yield MockSession()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
