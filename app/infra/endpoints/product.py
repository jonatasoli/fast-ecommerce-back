from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy.orm import Session
from app.entities.product import ProductInDB

from domains import domain_order
from app.infra import deps
from app.infra.deps import get_db
from payment.schema import ProductSchema
from schemas.order_schema import (
    ProductFullResponse,
    ProductSchemaResponse,
)

product = APIRouter(
    prefix='/product',
    tags=['product'],
)


@product.post(
    '/create-product',
    status_code=201,
    response_model=ProductSchemaResponse,
)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_data: ProductSchema,
) -> ProductSchema:
    """Create product."""
    return domain_order.create_product(db=db, product_data=product_data)


@product.post('/upload-image/{product_id}', status_code=200)
def upload_image(
    product_id: int,
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
) -> None:
    """Upload image."""
    try:
        return domain_order.upload_image(db, product_id, image)
    except Exception:
        raise


@product.post('/upload-image-gallery/', status_code=200)
def upload_image_gallery(
    product_id: int,
    db: Session = Depends(get_db),
    imagegallery: UploadFile = File(...),
) -> None:
    """Upload image gallery."""
    try:
        return domain_order.upload_image_gallery(product_id, db, imagegallery)
    except Exception:
        raise


@product.get('/images/gallery/{uri}', status_code=200)
def get_images_gallery(uri: str, db: Session = Depends(get_db)) -> None:
    """Get images gallery."""
    try:
        return domain_order.get_images_gallery(db, uri)
    except Exception:
        raise


@product.delete('/delete/image-gallery/{id}', status_code=200)
def delete_image(id: int, db: Session = Depends(get_db)) -> None:
    """Delete image."""
    try:
        return domain_order.delete_image_gallery(id, db)
    except Exception:
        raise


@product.get('/{uri}', status_code=200, response_model=ProductInDB)
def get_product_uri(uri: str, db: Session = Depends(get_db)) -> ProductInDB:
    """GET product uri."""
    try:
        product = domain_order.get_product(db, uri)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found',
            )

        return product
    except Exception as e:
        logger.error(f'Erro em obter os produto - { e }')
        raise


@product.put('/update/{id}', status_code=200)
def put_product(
    id: int,
    value: ProductFullResponse,
    db: Session = Depends(get_db),
) -> None:
    """Put product."""
    try:
        return domain_order.put_product(db, id, value)
    except Exception:
        raise


@product.delete('/delete/{id}', status_code=200)
def delete_product(id: int, db: Session = Depends(get_db)) -> None:
    """Delete product."""
    try:
        return domain_order.delete_product(db, id)
    except Exception:
        raise
