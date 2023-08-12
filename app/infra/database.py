from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker

from config import settings


def get_engine() -> None:
    """Get engine."""
    sqlalchemy_database_url = settings.DATABASE_URL

    return create_engine(
        sqlalchemy_database_url,
        pool_size=10,
        max_overflow=0,
    )


def get_session() -> None:
    """Get session."""
    _engine = get_engine()
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )


@as_declarative()
class Base:
    id: Any
    __name__: str
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(self: None) -> str:
        """Return a string representation of the table name."""
        return self.__name__.lower()
