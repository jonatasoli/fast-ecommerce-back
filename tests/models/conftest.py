import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infra.models import Base


@pytest.fixture
def session() -> sessionmaker:
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield Session()
    Base.metadata.drop_all(engine)
