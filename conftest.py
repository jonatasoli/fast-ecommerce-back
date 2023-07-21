import sys
from os.path import abspath
from os.path import dirname as d
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from loguru import logger
from sqlalchemy.engine import reflection
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import (
    DropConstraint,
    DropTable,
    ForeignKeyConstraint,
    MetaData,
    Table,
)

root_dir = d(abspath(__file__))
print(f'ROOT {root_dir}')
sys.path.append(root_dir)

from config import settings

from app.infra.base import Base
from app.infra.database import get_engine

from app.infra.deps import get_db
from main import app


@pytest.fixture(scope='session', autouse=True)
def set_test_settings():
    settings.configure(FORCE_ENV_FOR_DYNACONF='testing')


@pytest.fixture(scope='session')
def clean_db():
    _engine = get_engine()

    db_DropEverything()
    Base.metadata.create_all(bind=_engine)


def db_DropEverything():
    _engine = get_engine()
    conn = _engine.connect()

    # the transaction only applies if the DB supports
    # transactional DDL, i.e. Postgresql, MS SQL Server
    trans = conn.begin()

    inspector = reflection.Inspector.from_engine(_engine)

    # gather all data first before dropping anything.
    # some DBs lock after things have been dropped in
    # a transaction.
    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(ForeignKeyConstraint((), (), name=fk['name']))
        t = Table(table_name, metadata, *fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        conn.execute(DropConstraint(fkc))

    for table in tbs:
        conn.execute(DropTable(table))

    trans.commit()


@pytest.fixture(scope='session')
def override_get_db():
    try:
        _engine = get_engine()
        logger.info(f'----- ADD DB {Base.metadata}-------')
        TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope='function')
def db() -> Generator:
    _engine = get_engine()
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )
    return TestingSessionLocal()


@pytest.fixture(scope='session')
def db_models(clean_db) -> Generator:
    _engine = get_engine()
    logger.info('-----GENERATE DB------')
    _engine = get_engine()
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )
    return TestingSessionLocal()


@pytest.fixture(scope='session')
def t_client(clean_db, override_get_db) -> Generator:
    def _get_db_override():
        return override_get_db

    logger.info('-----GENERATE APP------')
    app.dependency_overrides[get_db] = _get_db_override
    logger.info(f'{ settings.current_env }')
    with TestClient(app) as c:
        yield c

