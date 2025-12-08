# ruff: noqa: I001
from sqlalchemy.sql import select
from app.infra.models import RoleDB
from tests.factories_db import RoleDBFactory


def test_create_role(session):
    # Setup
    new_role = RoleDBFactory()
    session.add(new_role)
    session.commit()

    # Act
    role = session.scalar(
        select(RoleDB).where(RoleDB.role_id == new_role.role_id),
    )

    # Assert
    assert role.role_id is not None
    assert role == new_role
