from sqlalchemy import select
from app.infra.models import UploadedMediaDB
from tests.factories_db import UploadedMediaFactory


def test_create_media(session):
    """Must create valid media."""
    # Arrange
    new_image = UploadedMediaFactory()
    session.add(new_image)
    session.commit()

    # Act
    image = session.scalar(
        select(UploadedMediaDB).where(
            UploadedMediaDB.media_id == new_image.media_id,
        ),
    )

    # Assert
    assert image.media_id == new_image.media_id
