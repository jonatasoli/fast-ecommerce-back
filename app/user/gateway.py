from app.infra.database import get_session
from app.user.services import get_current_user


def get_user(token: str):
    db = get_session()
    return get_current_user(token, db=db)
