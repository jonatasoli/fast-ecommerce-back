import pytest


@pytest.fixture
def mock_session(mocker):
    # Crie um mock para a sessão do SQLAlchemy usando pytest-mock
    return mocker.patch('your_module.order_task.bootstrap.db')


@pytest.fixture
def mock_order_repository(mocker):
    # Crie um mock para o repositório de pedidos
    return mocker.patch('your_module.order_task.bootstrap.order_repository')


@pytest.fixture
def mock_user_repository(mocker):
    # Crie um mock para o repositório de usuários
    return mocker.patch('your_module.order_task.bootstrap.user_repository')
