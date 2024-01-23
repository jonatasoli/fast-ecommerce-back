# ruff: noqa: ANN401 TRY301 TRY300
from typing import Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy.orm import Session
from app.entities.product import ProductInDB
from app.infra.models import ProductDB

from app.order import services
from app.infra import deps
from app.infra.deps import get_db
from payment.schema import ProductSchema
from schemas.order_schema import (
    ProductFullResponse,
    ProductSchemaResponse,
    ProductPatchRequest,
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
) -> ProductSchemaResponse:
    """Create product."""
    product = services.create_product(db=db, product_data=product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Error in create product',
        )
    return product


@product.post('/upload-image/{product_id}', status_code=200)
def upload_image(
    product_id: int,
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
) -> None:
    """Upload image."""
    try:
        return services.upload_image(db, product_id, image)
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
        return services.upload_image_gallery(product_id, db, imagegallery)
    except Exception:
        raise


@product.get('/images/gallery/{uri}', status_code=200)
def get_images_gallery(uri: str, db: Session = Depends(get_db)) -> None:
    """Get images gallery."""
    try:
        return services.get_images_gallery(db, uri)
    except Exception:
        raise


@product.delete('/delete/image-gallery/{id}', status_code=200)
def delete_image(id: int, db: Session = Depends(get_db)) -> None:
    """Delete image."""
    try:
        return services.delete_image_gallery(id, db)
    except Exception:
        raise


@product.get('/{uri:path}', status_code=200, response_model=ProductInDB)
def get_product_uri(uri: str, db: Session = Depends(get_db)) -> ProductInDB:
    """GET product uri."""
    try:
        product = services.get_product(db, uri)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found',
            )

        return product
    except Exception as e:
        logger.error(f'Erro em obter os produto - { e }')
        raise e from Exception


@product.patch(
    '/update/{id}',
    status_code=200,
    response_model=ProductFullResponse,
)
def patch_product(
    id: int,
    value: ProductPatchRequest,
    db: Session = Depends(get_db),
) -> ProductFullResponse:
    """Put product."""
    try:
        return services.patch_product(db, id, value)
    except Exception as e:
        logger.error(f'Erro em atualizar o produto - { e }')
        raise


@product.delete('/delete/{id}', status_code=200)
def delete_product(id: int, db: Session = Depends(get_db)) -> None:
    """Delete product."""
    try:
        return services.delete_product(db, id)
    except Exception:
        raise


@product.get('/cart/installments', status_code=200)
def get_installments(
    *,
    db: Session = Depends(get_db),
    product_id: int,
) -> Any:
    """Get installments."""
    try:
        return services.get_installments(product_id, db=db)
    except Exception as e:
        logger.error(f'Erro ao coletar o parcelamento - {e}')
        raise
