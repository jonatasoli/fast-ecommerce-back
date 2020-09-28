from ext.database import get_session
from dynaconf import settings
from loguru import logger


def get_db():
    SessionLocal = get_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
