import asyncio
from typing import AsyncGenerator, Optional
from collections import defaultdict

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.rabbitmq import get_rabbitmq
from app.main import app


# --- Mock RabbitMQ ---

class MockRabbitMQ:
    def __init__(self):
        self._queues: dict[str, list[dict]] = defaultdict(list)
        self.published: list[dict] = []
        self._connection_closed = False

    async def publish(self, routing_key: str, body: dict):
        self._queues[routing_key].append(body)
        self.published.append({"routing_key": routing_key, "body": body})

    async def pull_one(self, queue_name: str) -> Optional[dict]:
        queue = self._queues.get(queue_name, [])
        if not queue:
            return None
        return queue.pop(0)

    @property
    def is_connected(self) -> bool:
        return True


# --- Test DB ---

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def mock_rabbitmq():
    return MockRabbitMQ()


@pytest_asyncio.fixture
async def client(mock_rabbitmq) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    async def override_get_rabbitmq():
        return mock_rabbitmq

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_rabbitmq] = override_get_rabbitmq

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
