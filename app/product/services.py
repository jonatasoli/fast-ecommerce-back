from typing import Callable
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.infra import file_upload
from app.product import repository


def upload_image(
    product_id: int,
    *,
    db: Session,
    image: UploadFile,
    image_client: Callable = file_upload,
) -> str:
    """Upload image."""
    image_path = image_client.optimize_image(image)
    new_image_path = ''
    with db:
        db_product = repository.get_product_by_id(product_id, db=db)
        db_product.image_path = image_path
        db.commit()
        new_image_path = db_product.image_path
    return new_image_path
