# ruff: noqa: I001
import pytest

from app.entities.user import UserFilters, UsersDBResponse
from app.user.repository import get_users
from app.infra.constants import Direction
from tests.factories_db import RoleDBFactory, UserDBFactory


@pytest.mark.asyncio
async def test_get_users_with_name_filter(mocker, db):
    # Setup
    with db().begin() as transaction:
        role = RoleDBFactory()
        transaction.session.add(role)
        transaction.session.flush()
        user_response = UserDBFactory(role_id=role.role_id)
        transaction.session.add(user_response)
        transaction.session.flush()
        user_response.addresses = []
    transaction = mocker.MagicMock()
    transaction.session.scalars = mocker.AsyncMock(return_value=[user_response])
    transaction.session.scalar = mocker.AsyncMock(return_value=10)

    filters = UserFilters(
        search_name=user_response.name,
        direction=Direction.asc,
    )

    # Act
    response = await get_users(filters=filters, transaction=transaction)

    # Assert
    transaction.session.scalars.assert_called_once()

    # Check the query string
    query_str = str(transaction.session.scalars.call_args[0][0])
    assert 'LIKE' in query_str
    assert 'ORDER BY' in query_str

    assert transaction.session.scalar.called
    assert isinstance(response, UsersDBResponse)
    assert response.total_records == 10
    assert len(response.users) == 1
    assert response.users[0].name == user_response.name


@pytest.mark.asyncio
async def test_get_users_with_document_filter(mocker, db):
    # Setup
    with db().begin() as transaction:
        role = RoleDBFactory()
        transaction.session.add(role)
        transaction.session.flush()
        user_response = UserDBFactory(role_id=role.role_id)
        transaction.session.add(user_response)
        transaction.session.flush()
        user_response.addresses = []
    transaction = mocker.MagicMock()
    transaction.session.scalars = mocker.AsyncMock(return_value=[user_response])
    transaction.session.scalar = mocker.AsyncMock(return_value=5)

    filters = UserFilters(
        search_document=user_response.document,
        direction=Direction.asc,
    )

    # Act
    response = await get_users(filters=filters, transaction=transaction)

    # Assert
    transaction.session.scalars.assert_called_once()
    query_str = str(transaction.session.scalars.call_args[0][0])
    assert 'LIKE' in query_str
    assert 'ORDER BY' in query_str

    assert transaction.session.scalar.called
    assert isinstance(response, UsersDBResponse)
    assert response.total_records == 5


@pytest.mark.asyncio
async def test_get_users_with_ordering_and_pagination(mocker, db):
    # Setup
    with db().begin() as transaction:
        role = RoleDBFactory()
        transaction.session.add(role)
        transaction.session.flush()
        users = UserDBFactory.create_batch(size=3, role_id=role.role_id)
        transaction.session.add_all(users)
        transaction.session.flush()
        for index in range(3):
            users[index].addresses = []
    transaction = mocker.MagicMock()
    transaction.session.scalars = mocker.AsyncMock(return_value=users)
    transaction.session.scalar = mocker.AsyncMock(return_value=15)

    filters = UserFilters(
        order_by='username',
        direction=Direction.desc,
        page=2,
        limit=5,
    )

    # Act
    response = await get_users(filters=filters, transaction=transaction)

    # Assert
    transaction.session.scalars.assert_called_once()
    query_str = str(transaction.session.scalars.call_args[0][0])
    assert 'DESC' in query_str
    assert 'ORDER BY' in query_str
    assert 'OFFSET' in query_str
    assert transaction.session.scalar.called
    assert isinstance(response, UsersDBResponse)
    assert response.total_pages == 3


@pytest.mark.asyncio
async def test_get_users_no_filters(mocker, db):
    # Setup
    with db().begin() as transaction:
        role = RoleDBFactory()
        transaction.session.add(role)
        transaction.session.flush()
        users = UserDBFactory.create_batch(size=3, role_id=role.role_id)
        transaction.session.add_all(users)
        transaction.session.flush()
        for index in range(3):
            users[index].addresses = []
    transaction = mocker.MagicMock()
    transaction.session.scalars = mocker.AsyncMock(return_value=users)
    transaction.session.scalar = mocker.AsyncMock(return_value=15)

    filters = UserFilters(
        search_name=None,
        search_document=None,
        order_by='user_id',
        direction=Direction.asc,
        page=1,
        limit=10,
    )

    # Act
    response = await get_users(filters=filters, transaction=transaction)

    # Assert
    transaction.session.scalars.assert_called_once()
    query_str = str(transaction.session.scalars.call_args[0][0])
    assert 'ORDER BY' in query_str
    assert transaction.session.scalar.called
    assert isinstance(response, UsersDBResponse)
    assert response.total_records == 15
