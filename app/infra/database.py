from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker

from config import settings


def get_engine() -> Engine:
    """Return an instance of a database connection engine using SQLAlchemy.

    Return:
    ------
        sqlalchemy.engine.base.Engine: An instance of the configured SQLAlchemy
        connection engine.

    Example:
    -------
        engine = get_engine()
        connection = engine.connect()
        result = connection.execute("SELECT * FROM table")
        connection.close()
    """
    sqlalchemy_database_url = settings.DATABASE_URL

    return create_engine(
        sqlalchemy_database_url,
        pool_size=10,
        max_overflow=0,
    )


def get_session() -> sessionmaker:
    """Return a SQLAlchemy session factory with a configured engine.

    Return:
    ------
        sqlalchemy.orm.session.Session: A session factory configured to interact with
        the database using the specified engine.

    Example:
    -------
        session_factory = get_session()
        session = session_factory()

    Note:
    ----
        To use this function, ensure that the 'get_engine()' function is correctly
        implemented and that the necessary database URL is provided in the project's
        settings.

    """
    _engine = get_engine()
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )
