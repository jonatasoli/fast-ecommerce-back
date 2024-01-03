import pytest
from decimal import Decimal
from unittest.mock import MagicMock

from app.entities.cart import CartPayment
from app.order.entities import OrderDBUpdate
from app.infra.bootstrap.task_bootstrap import Command
from app.order.tasks import (
    create_order,
    update_order,
    create_order_status_step,
)


@pytest.fixture()
def mock_bootstrap():
    # Crie um objeto de mock para Command (ou bootstrap) para passar como argumento
    return Command()  # Você pode personalizar o mock conforme necessário


@pytest.fixture()
def mock_session(mocker):
    # Crie um mock para a sessão do SQLAlchemy usando pytest-mock
    return mocker.patch('your_module.order_task.bootstrap.db')


@pytest.fixture()
def mock_order_repository(mocker):
    # Crie um mock para o repositório de pedidos (ou outro repositório que você está usando)
    return mocker.patch('your_module.order_task.bootstrap.order_repository')


@pytest.fixture()
def mock_user_repository(mocker):
    # Crie um mock para o repositório de usuários (ou outro repositório que você está usando)
    return mocker.patch('your_module.order_task.bootstrap.user_repository')


def test_create_order(
    mocker,
    mock_bootstrap,
    mock_session,
    mock_order_repository,
    mock_user_repository,
):
    # Configure o comportamento esperado dos mocks
    mock_session_instance = mock_session.return_value.__enter__.return_value
    mock_order_repository.get_order_by_cart_uuid.return_value = None
    mock_user_repository.get_user_by_username.return_value = MagicMock()
    mock_session_instance.commit.return_value = None

    # Chame a função que você está testando
    result = create_order(
        CartPayment(),
        'affiliate',
        Decimal('10.0'),
        mock_bootstrap,
    )

    # Verifique o resultado esperado
    assert result is not None  # Substitua isso pelo que você espera da função


def test_update_order(
    mocker,
    mock_bootstrap,
    mock_session,
    mock_order_repository,
):
    # Configure o comportamento esperado dos mocks
    mock_session_instance = mock_session.return_value.__enter__.return_value
    mock_order_repository.update_order.return_value = MagicMock()
    mock_session_instance.commit.return_value = None

    # Chame a função que você está testando
    result = update_order(
        OrderDBUpdate(),
        mock_bootstrap,
    )

    # Verifique o resultado esperado
    assert result is not None  # Substitua isso pelo que você espera da função


def test_create_order_status_step(
    mocker,
    mock_bootstrap,
    mock_session,
    mock_order_repository,
):
    # Configure o comportamento esperado dos mocks
    mock_session_instance = mock_session.return_value.__enter__.return_value
    mock_order_repository.create_order_status_step.return_value = MagicMock()
    mock_session_instance.commit.return_value = None

    # Chame a função que você está testando
    result = create_order_status_step(
        1,
        'status',
        False,
        mock_bootstrap,
    )

    # Verifique o resultado esperado
    assert result is not None  # Substitua isso pelo que você espera da função
