from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger
from config import settings
from main import app
import pytest


@pytest.fixture(scope='session', autouse=True)
def set_test_settings():
    settings.configure(FORCE_ENV_FOR_DYNACONF='testing')


@pytest.fixture(name='client', scope='function')
def _client() -> TestClient:
    # app.dependency_overrides[get_db] = _get_db_override
    logger.info(f'{ settings.current_env }')
    return TestClient(app, raise_server_exceptions=False)
