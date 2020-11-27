from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from dynaconf import settings

from loguru import logger


def get_engine():
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=20, 
        max_overflow=0
    )
    return engine

def get_session():
    _engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return SessionLocal


@as_declarative()
class Base:
    id: Any
    __name__: str
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
