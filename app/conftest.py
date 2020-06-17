from typing import Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from dynaconf import settings
from app.ext.database import SessionLocal, Base
from app.main import app
from app.endpoints.deps import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db() -> Generator:
    yield TestingSessionLocal()


@pytest.fixture(scope="module")
def test_client() -> Generator:
    with TestClient(app) as c:
        yield c

