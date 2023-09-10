from sqlalchemy.exc import SQLAlchemyError
from app.infra.database import get_session


def get_db() -> None:
    """Get db."""
    local_session = get_session()
    db = local_session()
    try:
        yield db
    except SQLAlchemyError:
        raise
