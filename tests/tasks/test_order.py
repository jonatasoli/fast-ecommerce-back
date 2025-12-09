import pytest


@pytest.fixture
def mock_session(mocker):
    return mocker.patch('your_module.order_task.bootstrap.db')


@pytest.fixture
def mock_order_repository(mocker):
    return mocker.patch('your_module.order_task.bootstrap.order_repository')


@pytest.fixture
def mock_user_repository(mocker):
    return mocker.patch('your_module.order_task.bootstrap.user_repository')
