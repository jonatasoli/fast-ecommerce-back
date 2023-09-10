from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile
from loguru import logger
from sqlalchemy.orm import Session
from app.entities.product import ProductInDB

from domains import domain_order
from app.infra import deps
from app.infra.deps import get_db
from payment.schema import ProductSchema
from schemas.order_schema import (
    ProductFullResponse,
)

product = APIRouter(
    prefix='/product',
    tags=['product'],
)
catalog = APIRouter(
    prefix='/catalog',
    tags=['catalog'],
)


@product.post('/create-product', status_code=201, response_model=ProductSchema)
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


@catalog.get('/showcase/all', status_code=200)
def get_showcase(*, db: Session = Depends(get_db)) -> Any:
    """Get showcase."""
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
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


@product.get('/{uri}', status_code=200)
def get_product_uri(uri: str, db: Session = Depends(get_db)) -> None:
    """GET product uri."""
    try:
        return domain_order.get_product(db, uri)
    except Exception as e:
        logger.error(f'Erro em obter os produto - { e }')
        raise


@catalog.get('/all', status_code=200)
def get_products_all(db: Session = Depends(get_db)) -> None:
    """Get products all."""
    try:
        return domain_order.get_product_all(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
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


@catalog.get('/all/categorys', status_code=200)
def get_categorys(db: Session = Depends(get_db)) -> None:
    """GET categorys."""
    try:
        return domain_order.get_category(db)
    except Exception as e:
        logger.error(f'Erro em obter as categorias - { e }')
        raise


@catalog.get('/category/products/{path}', status_code=200)
def get_product_category(
    path: str,
    db: Session = Depends(get_db),
) -> None:
    """Get product category."""
    try:
        return domain_order.get_products_category(db, path)
    except Exception:
        raise
