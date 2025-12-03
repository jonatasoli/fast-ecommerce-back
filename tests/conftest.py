from datetime import timedelta
import asyncio
import redis
import sys
import types
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession, close_all_sessions
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from faststream.rabbit.fastapi import RabbitRouter

from app.infra.database import get_session
from tests.factories_db import RoleDBFactory
from app.infra.constants import DocumentType, Roles
from app.user.services import create_access_token, gen_hash
from config import settings
from app.infra.models import Base, UserDB


class MockRabbitRouter:
    """Mock RabbitRouter to avoid actual broker connections during tests."""

    def __init__(self, *args, **kwargs):
        self._broker = MagicMock()
        self._broker.start = AsyncMock()
        self._broker.close = AsyncMock()
        self._broker.connect = AsyncMock()
        self.routes = []
        self.prefix = ''
        self.tags = []
        self.dependencies = []
        self.on_startup = []
        self.on_shutdown = []
        self.lifespan_context = self._mock_lifespan_context
        self.deprecated = None
        self.include_in_schema = True
        self.default_response_class = None
        self.responses = {}
        self.callbacks = []
        self.redirect_slashes = True
        self.default = None

    @property
    def broker(self):
        return self._broker

    @asynccontextmanager
    async def _mock_lifespan_context(self, app):
        yield {}

    def subscriber(self, queue_name):
        """Mock subscriber decorator."""
        def decorator(func):
            return func
        return decorator

    def __call__(self, *args, **kwargs):
        return self

def pytest_configure(config):
    """Configure pytest - mock RabbitRouter before any app modules are imported."""
    mock_faststream_module = types.ModuleType('faststream.rabbit.fastapi')
    mock_faststream_module.RabbitRouter = MockRabbitRouter
    sys.modules['faststream.rabbit.fastapi'] = mock_faststream_module

@pytest.fixture(scope='session', autouse=True)
def _set_test_settings() -> None:
    """Force testing env."""
    settings.configure(FORCE_ENV_FOR_DYNACONF='testing')

@pytest.fixture(scope='session')
def postgres_container():
    """Create single PostgreSQL container for all tests."""
    with PostgresContainer('postgres:17', driver='psycopg') as postgres:
        yield postgres

@pytest.fixture(scope='session')
def engine(postgres_container):
    """Create test engine."""
    engine = create_engine(
        postgres_container.get_connection_url(),
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope='session')
def redis_container():
    """Create test Redis container."""
    with RedisContainer('redis:7-alpine') as redis:
        # Override settings for tests
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        settings.REDIS_URL = f"redis://{host}:{port}"
        settings.REDIS_DB = 0
        yield redis


@pytest.fixture(scope='session')
def redis_client(redis_container):
    """Get Redis client for tests."""
    pool = redis.ConnectionPool.from_url(
        url=settings.REDIS_URL,
        db=settings.REDIS_DB,
    )
    client = redis.Redis(connection_pool=pool)
    yield client
    client.close()
    pool.disconnect()

@pytest.fixture
async def async_engine(postgres_container, engine):
    """Create test async engine using same PostgreSQL container."""
    connection_url = postgres_container.get_connection_url()
    async_url = connection_url.replace('postgresql+psycopg://', 'postgresql+asyncpg://')

    async_engine_instance = create_async_engine(
        async_url,
        poolclass=StaticPool,
    )
    # Don't create all tables here - they're already created by the sync engine fixture
    yield async_engine_instance

    # Don't drop tables on teardown - sync tests may still need them
    await async_engine_instance.dispose()


def _truncate_tables(connection):
    """Truncate all tables to clean data between tests."""
    for table in reversed(Base.metadata.sorted_tables):
        connection.execute(table.delete())
    connection.commit()

async def _async_truncate_tables(connection):
    """Async version to truncate all tables between tests."""
    def truncate(conn):
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()

    await connection.run_sync(truncate)

@pytest.fixture
def db(engine, redis_container):
    """Generate db session."""
    session = sessionmaker(
        autoflush=True,
        expire_on_commit=False,
        bind=engine,
    )
    yield session
    with engine.begin() as conn:
        _truncate_tables(conn)


@pytest.fixture
def client(db, monkeypatch):
    from contextlib import asynccontextmanager
    import app.infra.worker
    import app.mail.tasks
    import app.cart.tasks
    import app.report.tasks
    from main import app as fastapi_app

    @asynccontextmanager
    async def mock_lifespan(app_instance):
        yield {}

    monkeypatch.setattr(app.infra.worker.task_message_bus, 'lifespan_context', mock_lifespan)
    monkeypatch.setattr(app.mail.tasks.task_message_bus, 'lifespan_context', mock_lifespan)
    monkeypatch.setattr(app.cart.tasks.task_message_bus, 'lifespan_context', mock_lifespan)
    monkeypatch.setattr(app.report.tasks.task_message_bus, 'lifespan_context', mock_lifespan)

    try:
        with TestClient(fastapi_app) as test_client:
            fastapi_app.dependency_overrides[get_session] = lambda: db
            yield test_client
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    session = db()
    new_role = RoleDBFactory(role_id=Roles.USER.value)
    session.add(new_role)

    user = UserDB(
        name='Teste',
        username='Teste',
        email='teste@test.com',
        password=gen_hash('testtest'),
        document_type=DocumentType.CPF.value,
        document='12345678901',
        phone='11123456789',
        role_id=Roles.USER.value,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    user.clean_password = 'testtest' # Noqa: S105

    session.close()
    return user

@pytest.fixture
def token(user):
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return create_access_token(
        data={'sub': user.document},
        expires_delta=access_token_expires,
    )


@pytest.fixture
def admin_user(db):
    session = db()
    new_role = RoleDBFactory(role_id=Roles.ADMIN.value)
    session.add(new_role)

    user = UserDB(
        name='Teste',
        username='Teste',
        email='teste@test.com',
        password=gen_hash('testtest'),
        document_type=DocumentType.CPF.value,
        document='12345678901',
        phone='11123456789',
        role_id=Roles.ADMIN.value,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.commit()

    user.clean_password = 'testtest' # Noqa: S105

    session.close()
    return user

@pytest.fixture
def admin_token(admin_user):
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return create_access_token(
        data={'sub': admin_user.document},
        expires_delta=access_token_expires,
    )


@pytest.fixture
async def asyncdb(async_engine, redis_container):
    """Generate asyncdb session with data cleanup between tests."""
    async_session = async_sessionmaker(
        autoflush=True,
        expire_on_commit=False,
        bind=async_engine,
        class_=AsyncSession,
    )
    yield async_session
    await close_all_sessions()
    async with async_engine.begin() as conn:
        await _async_truncate_tables(conn)


@pytest.fixture
async def async_admin_user(asyncdb):
    """Generate admin user in asyncdb."""
    new_role = RoleDBFactory(role_id=Roles.ADMIN.value)
    async with asyncdb.begin() as db:
        db.add(new_role)

        user = UserDB(
            name='Teste',
            username='Teste',
            email='teste@test.com',
            password=gen_hash('testtest'),
            document_type=DocumentType.CPF.value,
            document='12345678901',
            phone='11123456789',
            role_id=Roles.ADMIN.value,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        await db.commit()

        user.clean_password = 'testtest' # Noqa: S105

        return user


@pytest.fixture
def async_admin_token(async_admin_user):
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return create_access_token(
        data={'sub': async_admin_user.document},
        expires_delta=access_token_expires,
    )

@pytest.fixture
async def async_client(asyncdb):
    """Generate async HTTP client for testing."""
    from httpx import ASGITransport, AsyncClient
    from app.infra.database import get_async_session
    from main import app as fastapi_app

    # Override returns the sessionmaker directly
    fastapi_app.dependency_overrides[get_async_session] = lambda: asyncdb

    try:
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        fastapi_app.dependency_overrides.clear()
