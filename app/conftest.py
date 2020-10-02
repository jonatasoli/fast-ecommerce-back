from typing import Dict, Generator
from loguru import logger

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ext.base import Base
from dynaconf import settings
from .ext.database import get_session
from .main import app
from .endpoints.deps import get_db
from ext.database import get_engine


@pytest.fixture(scope="session", autouse=True)
def set_test_settings():
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")


@pytest.fixture(scope="session")
def override_get_db():
    try:
        _engine = get_engine()
        Base.metadata.drop_all(bind=_engine)
        Base.metadata.create_all(bind=_engine)
        logger.info(f"----- ADD DB {Base.metadata}-------")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        db = TestingSessionLocal() 
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def db() -> Generator:
    _engine = get_engine()
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    logger.info("-----GENERATE DB------")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    yield TestingSessionLocal()


@pytest.fixture(scope="session")
def t_client(override_get_db) -> Generator:

    def _get_db_override():
        return override_get_db

    logger.info("-----GENERATE APP------")
    app.dependency_overrides[get_db] = _get_db_override
    logger.info(f"{ settings.current_env }")
    with TestClient(app) as c:
        yield c

