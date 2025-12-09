"""Tests for custom_decorators module."""
import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.infra.custom_decorators import database_uow


@pytest.mark.asyncio
async def test_database_uow_decorator_success(mocker):
    """Test database_uow decorator commits transaction on success."""
    # Setup
    mock_bootstrap = mocker.Mock()
    mock_inner_session = mocker.Mock()
    mock_inner_session.session.commit = mocker.AsyncMock()
    mock_context = mocker.AsyncMock()
    mock_context.__aenter__ = mocker.AsyncMock(return_value=mock_inner_session)
    mock_context.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_bootstrap.db.return_value.begin.return_value = mock_context

    @database_uow()
    async def test_function(*args, **kwargs):
        """Test function."""
        return 'success'

    # Act
    result = await test_function(bootstrap=mock_bootstrap)

    # Assert
    assert result == 'success'
    mock_inner_session.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_database_uow_decorator_rollback_on_error(mocker):
    """Test database_uow decorator rolls back on SQLAlchemyError."""
    # Setup
    mock_bootstrap = mocker.Mock()
    mock_inner_session = mocker.Mock()
    mock_inner_session.session.commit = mocker.AsyncMock()
    mock_inner_session.rollback = mocker.Mock()
    mock_context = mocker.AsyncMock()
    mock_context.__aenter__ = mocker.AsyncMock(return_value=mock_inner_session)
    mock_context.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_bootstrap.db.return_value.begin.return_value = mock_context

    @database_uow()
    async def test_function(*args, **kwargs):
        """Test function that raises error."""
        raise SQLAlchemyError('Database error')

    with pytest.raises(SQLAlchemyError):
        await test_function(bootstrap=mock_bootstrap)

    # Assert
    mock_inner_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_database_uow_decorator_passes_transaction(mocker):
    """Test database_uow decorator passes transaction to function."""
    # Setup
    mock_bootstrap = mocker.Mock()
    mock_inner_session = mocker.Mock()
    mock_inner_session.session.commit = mocker.AsyncMock()
    mock_context = mocker.AsyncMock()
    mock_context.__aenter__ = mocker.AsyncMock(return_value=mock_inner_session)
    mock_context.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_bootstrap.db.return_value.begin.return_value = mock_context

    @database_uow()
    async def test_function(*args, transaction=None, **kwargs):
        """Test function that receives transaction."""
        assert transaction == mock_inner_session
        return 'success'

    # Act
    result = await test_function(bootstrap=mock_bootstrap)

    # Assert
    assert result == 'success'
