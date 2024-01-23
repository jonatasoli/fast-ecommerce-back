# import pytest
# from app.infra.bootstrap.cart_bootstrap import bootstrap
# from main import app
# from httpx import AsyncClient
# from config import settings


# @pytest.fixture(scope='session', autouse=True)
# def set_test_settings() -> None:
#     settings.configure(FORCE_ENV_FOR_DYNACONF='testing')


# @pytest.fixture(scope='session')
# def anyio_backend():
#     return 'asyncio'


# @pytest.fixture(scope='session')
# async def client():
#     async with AsyncClient(app=app, base_url='http://test') as client:
#         yield client
