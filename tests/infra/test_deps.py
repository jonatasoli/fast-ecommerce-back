"""Tests for deps module."""
import contextlib

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.infra.deps import get_db


def test_get_db_yields_session(mocker):
    """Test get_db yields database session."""
    # Setup
    mock_session = mocker.Mock()
    mock_session_factory = mocker.Mock(return_value=mock_session)
    mocker.patch('app.infra.deps.get_session', return_value=mock_session_factory)

    # Act
    db_gen = get_db()
    db = next(db_gen)

    assert db == mock_session


def test_get_db_closes_session(mocker):
    """Test get_db closes session after use."""
    # Setup
    mock_session = mocker.Mock()
    mock_session_factory = mocker.Mock(return_value=mock_session)
    mocker.patch('app.infra.deps.get_session', return_value=mock_session_factory)

    # Act
    db_gen = get_db()
    next(db_gen)
    with contextlib.suppress(StopIteration):
        next(db_gen)

    assert mock_session is not None


def test_get_db_raises_sqlalchemy_error(mocker):
    """Test get_db re-raises SQLAlchemyError."""
    # Setup
    mock_session = mocker.Mock()
    mock_session_factory = mocker.Mock(return_value=mock_session)
    mocker.patch('app.infra.deps.get_session', return_value=mock_session_factory)

    # Act
    db_gen = get_db()
    db = next(db_gen)

    def raise_error():
        raise SQLAlchemyError('Database error')

    mock_session.some_operation = raise_error

    with pytest.raises(SQLAlchemyError):
        db.some_operation()
