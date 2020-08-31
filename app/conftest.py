from typing import Dict, Generator
from loguru import logger

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ext.base import Base
from dynaconf import settings
from .ext.database import SessionLocal, Base
from .main import app
from .endpoints.deps import get_db


SQLALCHEMY_DATABASE_URL = settings.DATABASE_TEST

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("----- ADD DB -------")
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db() -> Generator:
    logger.info("-----GENERATE DB------")
    yield TestingSessionLocal()


@pytest.fixture(scope="module")
def test_client() -> Generator:
    with TestClient(app) as c:
        yield c

