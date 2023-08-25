from sqlalchemy import select
from app.infra.models.uploadedimage import UploadedImage
from tests.factories_db import UploadedImageFactory


def test_create_user(session):
    """Must create valid user."""

    # Arrange
    new_image = UploadedImageFactory()
    session.add(new_image)
    session.commit()

    # Act
    image = session.scalar(
        select(UploadedImage).where(
            UploadedImage.uploaded_image_id == new_image.uploaded_image_id
        )
    )

    # Assert
    assert image.uploaded_image_id == new_image.uploaded_image_id
