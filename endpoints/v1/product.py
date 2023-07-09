from fastapi import APIRouter, Depends, File, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from domains import domain_order
from endpoints import deps
from endpoints.deps import get_db
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


@product.post('/create-product', status_code=201)
async def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_data: ProductSchema,
):
    product = domain_order.create_product(db=db, product_data=product_data)
    return ProductSchema.from_orm(product)


@product.post('/upload-image/{product_id}', status_code=200)
async def upload_image(
    product_id: int,
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
):
    try:
        return domain_order.upload_image(db, product_id, image)
    except Exception as e:
        raise e


@product.post('/upload-image-gallery/', status_code=200)
async def upload_image_gallery(
    product_id: int,
    db: Session = Depends(get_db),
    imageGallery: UploadFile = File(...),
):
    try:
        return domain_order.upload_image_gallery(product_id, db, imageGallery)
    except Exception as e:
        raise e


@catalog.get('/showcase/all', status_code=200)
async def get_showcase(*, db: Session = Depends(get_db)):
    try:
        return domain_order.get_showcase(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
        raise e


@product.get('/images/gallery/{uri}', status_code=200)
async def get_images_gallery(uri: str, db: Session = Depends(get_db)):
    try:
        return domain_order.get_images_gallery(db, uri)
    except Exception as e:
        raise e


@product.delete('/delete/image-gallery/{id}', status_code=200)
async def delete_image(id: int, db: Session = Depends(get_db)):
    try:
        return domain_order.delete_image_gallery(id, db)
    except Exception as e:
        raise e


@product.get('/{uri}', status_code=200)
async def get_product_uri(uri: str, db: Session = Depends(get_db)):
    try:
        return domain_order.get_product(db, uri)
    except Exception as e:
        logger.error(f'Erro em obter os produto - { e }')
        raise e


@catalog.get('/all', status_code=200)
async def get_products_all(db: Session = Depends(get_db)):
    try:
        return domain_order.get_product_all(db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos - { e }')
        raise e


@product.put('/update/{id}', status_code=200)
async def put_product(
    id: int,
    value: ProductFullResponse,
    db: Session = Depends(get_db),
):
    try:
        return domain_order.put_product(db, id, value)
    except Exception as e:
        raise e


@product.delete('/delete/{id}', status_code=200)
async def delete_product(id: int, db: Session = Depends(get_db)):
    try:
        return domain_order.delete_product(db, id)
    except Exception as e:
        raise e


@catalog.get('/all/categorys', status_code=200)
async def get_categorys(db: Session = Depends(get_db)):
    try:
        return domain_order.get_category(db)
    except Exception as e:
        logger.error(f'Erro em obter as categorias - { e }')
        raise e


@catalog.get('/category/products/{path}', status_code=200)
async def get_product_category(path: str, db: Session = Depends(get_db)):
    try:
        return domain_order.get_products_category(db, path)
    except Exception as e:
        raise e
