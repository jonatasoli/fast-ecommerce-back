import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infra.custom_decorators import database_uow
from sqlalchemy.exc import SQLAlchemyError
from faker import Faker

fake = Faker()


async def example_function(arg1=None, arg2=None):
    return fake.random_int()


@pytest.fixture()
def temporary_async_sessionmaker():
    engine = create_async_engine(
        'sqlite+aiosqlite:///mydatabase.db',
        echo=True,
    )
    SessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return SessionLocal


# @pytest.mark.asyncio()
@pytest.mark.skip()
async def test_database_uow_success_should_call_begin(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(temporary_async_sessionmaker, 'begin')
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(example_function)

    # Act
    result = await decorated_function()

    # Assert
    assert result is not None
    assert isinstance(result, int)
    session_spy.assert_called_once()


@pytest.mark.skip()
async def test_database_uow_success_should_call_commit(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(
        temporary_async_sessionmaker.begin().async_session,
        'commit',
    )
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(example_function)

    # Act
    result = await decorated_function()

    # Assert
    assert result is not None
    assert isinstance(result, int)
    session_spy.assert_called_once()


# Exceção do SQLAlchemy
# @pytest.mark.asyncio()
@pytest.mark.skip()
async def test_database_uow_sqlalchemy_error_should_call_begin(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    async def example_function(*args, **kwargs):
        raise SQLAlchemyError('Simulated SQLAlchemy Error')

    session = mocker.spy(temporary_async_sessionmaker, 'begin')
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(example_function)

    # Act
    with pytest.raises(SQLAlchemyError):
        await decorated_function()

    session.assert_called_once()


@pytest.mark.skip()
async def test_database_uow_sqlalchemy_error_should_call_rollback(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(temporary_async_sessionmaker, 'rollback')
    temporary_async_sessionmaker.begin.side_effect = SQLAlchemyError(
        'Simulated SQLAlchemy Error',
    )
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(example_function)

    # Act
    with pytest.raises(SQLAlchemyError):
        await decorated_function()

    # Assert
    session_spy.assert_called_once()


# Preservação de Argumentos
# @pytest.mark.asyncio()
@pytest.mark.skip()
async def test_database_uow_preserve_args_should_call_begin(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(temporary_async_sessionmaker, 'begin')
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(example_function)

    # Act
    arg1, arg2 = faker.random_int(), faker.random_int()
    result = await decorated_function(arg1=arg1, arg2=arg2)

    # Assert
    assert result is not None
    assert isinstance(result, int)
    session_spy.assert_called_once()


@pytest.mark.skip()
async def test_database_uow_preserve_args_should_call_commit(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(temporary_async_sessionmaker, 'commit')
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(example_function)

    # Act
    arg1, arg2 = faker.random_int(), faker.random_int()
    result = await decorated_function(arg1=arg1, arg2=arg2)

    # Assert
    assert result is not None
    assert isinstance(result, int)
    session_spy.assert_called_once()


# Teste com Função Assíncrona
async def async_example_function():
    return fake.random_int()


# @pytest.mark.asyncio()
@pytest.mark.skip()
async def test_database_uow_async_function_should_call_begin(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(temporary_async_sessionmaker, 'begin')
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(async_example_function)

    # Act
    result = await decorated_function()

    # Assert
    assert result is not None
    assert isinstance(result, int)
    session_spy.assert_called_once()


@pytest.mark.skip()
async def test_database_uow_async_function_should_call_commit(
    temporary_async_sessionmaker,
    mocker,
    faker,
):
    # Arrange
    session_spy = mocker.spy(temporary_async_sessionmaker, 'commit')
    decorator = database_uow(temporary_async_sessionmaker)
    decorated_function = decorator(async_example_function)

    # Act
    result = await decorated_function()

    # Assert
    assert result is not None
    assert isinstance(result, int)
    session_spy.assert_called_once()
