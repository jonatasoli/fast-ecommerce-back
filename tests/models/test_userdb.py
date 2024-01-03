from sqlalchemy import select
from app.infra.models import UserDB
from tests.factories_db import UserFactory


def test_create_user(session):
    """Must create valid user."""
    # Arrange
    new_user = UserFactory()
    session.add(new_user)
    session.commit()

    # Act
    user = session.scalar(select(UserDB).where(UserDB.user_id == new_user.user_id))

    # Assert
    assert user.user_id == 1
    assert user.role_id == 2
    assert user == new_user
