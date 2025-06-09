from datetime import timedelta
import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession, close_all_sessions

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.infra.database import get_session
from tests.factories_db import RoleDBFactory

from app.infra.constants import DocumentType, Roles
from app.user.services import create_access_token, gen_hash
from config import settings

from app.infra.models import Base, UserDB
from main import app
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope='session', autouse=True)
def _set_test_settings() -> None:
    """Force testing env."""
    settings.configure(FORCE_ENV_FOR_DYNACONF='testing')


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope='session')
def engine():
    """Create test engine."""
    with PostgresContainer('postgres:17', driver='psycopg') as postgres:

        engine = create_engine(
            postgres.get_connection_url(),
            poolclass=StaticPool,
        )

        yield engine
        engine.dispose()


@pytest.fixture(scope='session')
async def async_engine():
    """Create test async engine."""
    with PostgresContainer('postgres:17', driver='asyncpg') as postgres:

        engine = create_async_engine(
            postgres.get_connection_url(),
            poolclass=StaticPool,
        )
        yield engine
        await engine.dispose()

@pytest.fixture
def db(engine):
    """Generate db session."""
        # Reflect all tables from metadata
    metadata = Base.metadata
    metadata.create_all(engine)

    session = sessionmaker(
        autoflush=True,
        expire_on_commit=False,
        bind=engine,
    )
    yield session
    session().rollback()
    metadata.drop_all(engine)


@pytest.fixture
def client(db):
    with TestClient(app) as client:
        app.dependency_overrides[get_session] = lambda: db
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    new_role = RoleDBFactory(role_id=Roles.USER.value)
    db.add(new_role)

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
    db.add(user)
    db.commit()
    db.refresh(user)

    user.clean_password = 'testtest' # Noqa: S105

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
    new_role = RoleDBFactory(role_id=Roles.ADMIN.value)
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
    db.commit()
    db.refresh(user)
    db.commit()

    user.clean_password = 'testtest' # Noqa: S105

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
async def asyncdb(async_engine):
    """Generate asyncdb session."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async_session = async_sessionmaker(
            autoflush=True,
            expire_on_commit=False,
            bind=async_engine,
            class_=AsyncSession,
        )
        yield async_session
        await close_all_sessions()
        await conn.run_sync(Base.metadata.drop_all)
    await async_engine.dispose()


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
