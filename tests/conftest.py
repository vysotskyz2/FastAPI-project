import asyncio
import json as jsonlib
from collections.abc import AsyncGenerator
from urllib.parse import urlencode

import asyncpg
import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.infrastructure.models.base import Base
from src.settings import settings

from src.infrastructure import models  # noqa: F401
from src.infrastructure.celery.celery_app import celery_app


def _admin_dsn() -> str:
    return f"postgresql://postgres:{settings.db.password}@{settings.db.host}:{settings.db.port}/postgres"


def _ensure_test_db() -> None:
    async def _create() -> None:
        admin = await asyncpg.connect(_admin_dsn())
        try:
            exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", "task_test")
            if not exists:
                await admin.execute("CREATE DATABASE task_test")
        finally:
            await admin.close()

    asyncio.run(_create())


def _drop_test_db() -> None:
    async def _drop() -> None:
        admin = await asyncpg.connect(_admin_dsn())
        try:
            await admin.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'task_test' AND pid <> pg_backend_pid()"
            )
            await admin.execute("DROP DATABASE IF EXISTS task_test")
        finally:
            await admin.close()

    asyncio.run(_drop())


@pytest.fixture(scope="session")
def faker() -> Faker:
    return Faker()


@pytest.fixture(scope="session", autouse=True)
def _db_schema() -> AsyncGenerator[None, None]:
    _ensure_test_db()
    yield
    _drop_test_db()


@pytest.fixture(scope="session", autouse=True)
def celery_eager() -> None:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
        result_backend="cache+memory://",
    )


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(settings.db.url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("TRUNCATE users, transactions, user_balances RESTART IDENTITY CASCADE"))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with db_engine.connect() as conn:
        await conn.begin()
        sess = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        yield sess
        await sess.close()


class _Response:
    def __init__(self, status_code: int, body: bytes) -> None:
        self.status_code = status_code
        self._body = body

    def json(self):
        return jsonlib.loads(self._body) if self._body else None

    @property
    def text(self) -> str:
        return self._body.decode()


class AsgiClient:
    def __init__(self, app) -> None:
        self._app = app

    async def _request(self, method: str, path: str, json_body=None) -> _Response:
        body = jsonlib.dumps(json_body).encode() if json_body is not None else b""
        headers: list[tuple[bytes, bytes]] = [(b"host", b"test")]
        if json_body is not None:
            headers.append((b"content-type", b"application/json"))
            headers.append((b"content-length", str(len(body)).encode()))

        path_only, _, query = path.partition("?")
        scope = {
            "type": "http",
            "method": method,
            "path": path_only,
            "raw_path": path_only.encode(),
            "query_string": query.encode(),
            "headers": headers,
            "client": ("testclient", 0),
            "server": ("test", 80),
        }
        status = [500]
        chunks: list[bytes] = []
        sent = [False]

        async def receive():
            if not sent[0]:
                sent[0] = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                status[0] = message["status"]
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))

        await self._app(scope, receive, send)
        return _Response(status[0], b"".join(chunks))

    async def get(self, path: str, params: dict | None = None) -> _Response:
        if params:
            path = f"{path}?{urlencode(params)}"
        return await self._request("GET", path)

    async def post(self, path: str, json=None) -> _Response:
        return await self._request("POST", path, json_body=json)

    async def patch(self, path: str, json=None) -> _Response:
        return await self._request("PATCH", path, json_body=json)


@pytest_asyncio.fixture
async def client(session: AsyncSession):
    from src.interfaces.api.app import app
    from src.interfaces.api.deps import get_session

    app.dependency_overrides[get_session] = lambda: session
    yield AsgiClient(app)
    app.dependency_overrides.clear()
