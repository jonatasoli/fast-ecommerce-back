from io import BytesIO
from pydantic import ValidationError
import pytest
from faker import Faker
from fastapi import UploadFile
from app.entities.product import UploadedMediaCreate
from app.infra.constants import MediaType
from faker_file.providers.png_file import GraphicPngFileProvider

fake = Faker()
fake.add_provider(GraphicPngFileProvider)

def test_uploaded_create_model_should_valid_data():
    """Must create model return data."""
    # Setup
    order = fake.random_int()
    image_path = f'/{fake.graphic_png_file()}'
    headers = { 'content-type': 'mime_type' }

    # Act
    with open(image_path, "wb") as file: # noqa: PTH123
        media_file= UploadFile(
            file=file,
            filename='file',
            headers=headers,
        )
        upload_media = UploadedMediaCreate(
            media=media_file,
            type = MediaType.photo,
            order = order,
        )

    #Arrange
    assert upload_media.media == media_file
    assert upload_media.type == MediaType.photo
    assert upload_media.order == order


def test_uploaded_create_model_with_invalid_type_should_exception():
    """Must create model with invalid type return exception."""
    # Setup
    invalid_type = "error"  # valor inválido
    dummy_file = BytesIO(b"dummy image content")
    upload_file = UploadFile(file=dummy_file, filename="image.png")

    # Act / Assert
    with pytest.raises(ValidationError) as exc_info:
        UploadedMediaCreate(
            media=upload_file,
            type=invalid_type,
            order=1,
        )

    assert "type" in str(exc_info.value)
