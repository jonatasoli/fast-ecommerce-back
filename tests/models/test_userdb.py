from sqlalchemy import select
from app.infra.models import UserDB
from tests.factories_db import UserDBFactory


def test_create_user(session):
    # Setup
    new_user = UserDBFactory()
    session.add(new_user)
    session.commit()

    # Act
    user = session.scalar(
        select(UserDB).where(UserDB.user_id == new_user.user_id),
    )

    assert user.user_id == 1
    assert user.role_id == 2
    assert user == new_user
