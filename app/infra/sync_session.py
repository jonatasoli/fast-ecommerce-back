from sqlalchemy.orm import sessionmaker
from config import settings
from sqlalchemy import Engine, create_engine


def get_engine() -> Engine:
    """Create a new engine."""
    return create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=0,
        echo=True,
    )


def get_session() -> sessionmaker:
    """Create a new session."""
    return sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
    )
