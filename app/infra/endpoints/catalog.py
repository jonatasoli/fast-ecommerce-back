# ruff: noqa: ANN401 FBT002 TRY300 TRY301 PLR0913
from typing import Any

from fastapi.security import OAuth2PasswordBearer
from app.infra.constants import CurrencyType, MediaType
from app.infra.database import get_async_session, get_session
from fastapi import APIRouter, Depends, requests, status
from fastapi import APIRouter, Depends, status, File, UploadFile
from app.entities.catalog import (
    Categories,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.entities.category import CategoryNotFoundError
from app.catalog import services as catalog_services
from app.catalog.services import get_categories_by_filter
from app.entities.product import ProductsResponse
from app.infra.bootstrap.catalog_bootstrap import Command, bootstrap
from config import settings
from app.order import services
from sqlalchemy.orm import Session

from loguru import logger

from app.infra import deps
from app.user.services import verify_admin_async

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')

catalog = APIRouter(
    prefix='/catalog',
    tags=['catalog'],
)


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@catalog.get(
    '/showcase/all',
    summary='Get products in showcase',
    description='Return all products in flag with showcase in ProductDB',
    status_code=status.HTTP_200_OK,
)
def get_showcase(
    *,
    currency: CurrencyType = CurrencyType.BRL,
    db = Depends(get_session),
) -> Any:
    """Get showcase."""
    try:
        return services.get_showcase(currency=currency, db=db)
    except Exception as e:
        logger.error(f'Erro em obter os produtos dentro do showcase - { e }')
        raise


@catalog.get(
    '/all',
    summary='Get all products',
    description='Return all products in ProductDB',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
async def get_products_all(
    *,
    offset: int = 10,
    page: int = 1,
    currency: CurrencyType = CurrencyType.BRL,
    db = Depends(get_async_session),
) -> ProductsResponse:
    """Get products all."""
    return await services.get_product_all(
        page=page,
        offset=offset,
        currency=currency,
        db=db,
    )


@catalog.get(
    '/latest',
    summary='Get latest products',
    description='Return latest add products in ProductDB',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
async def get_latest_products(
    offset: int = 10,
    page: int = 1,
    currency: CurrencyType = CurrencyType.BRL,
    db: Session = Depends(get_async_session),
) -> ProductsResponse:
    """Get latest products."""
    return await services.get_latest_products(
        currency=currency,
        page=page,
        offset=offset,
        db=db,
    )


@catalog.get(
    '/featured',
    summary='Get featured products',
    description='Return products is flagged with ProductDB limited for offset',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
async def get_products_featured(
    offset: int = 2,
    page: int = 1,
    currency: CurrencyType = CurrencyType.BRL,
    db: Session = Depends(get_async_session),
) -> ProductsResponse:
    """Get products all."""
    return await services.get_featured_products(
        currency=currency,
        page=page,
        offset=offset,
        db=db,
    )


@catalog.get(
    '/',
    summary='Get searched term products',
    description='Return products with machted term in ProductDB',
    status_code=status.HTTP_200_OK,
    response_model=ProductsResponse,
)
async def search_products(
    search: str,
    offset: int = 2,
    page: int = 1,
    currency: CurrencyType = CurrencyType.BRL,
    db: Session = Depends(get_async_session),
) -> ProductsResponse:
    """Get search term products."""
    return await services.search_products(
        currency=currency,
        search=search,
        offset=offset,
        page=page,
        db=db,
    )


@catalog.get(
    '/categories',
    status_code=status.HTTP_200_OK,
    response_model=Categories,
)
async def get_categories(
    menu: bool = False,
    showcase: bool = False,
    db = Depends(get_async_session),
) -> Categories:
    """GET categories."""
    try:
        return await get_categories_by_filter(
            menu=menu,
            showcase=showcase,
            db=db,
        )
    except Exception as e:
        logger.error(f'Erro em obter as categorias - { e }')
        raise


@catalog.get('/category/products/{path}', status_code=status.HTTP_200_OK)
async def get_product_category(
    path: str,
    offset: int = 2,
    page: int = 1,
    currency: CurrencyType = CurrencyType.BRL,
    db = Depends(get_async_session),
) -> ProductsResponse:
    """Get product category."""
    try:
        return await services.get_products_category(
            currency=currency,
            offset=offset,
            page=page,
            path=path,
            db=db,
        )
    except Exception:
        raise

@catalog.get(
    '/category/{category_id}',
    status_code=status.HTTP_200_OK,
    response_model=CategoryResponse,
)
async def get_category_by_id(
    category_id: int,
    db = Depends(get_async_session),
) -> CategoryResponse:
    """Get category by ID."""
    category = await catalog_services.get_category_by_id(
        category_id,
        db=db,
    )
    if not category:
        raise CategoryNotFoundError
    return category


@verify_admin_async()
@catalog.post(
    '/category',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryResponse,
    tags=['admin'],
)
async def create_category(
    category_data: CategoryCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
) -> CategoryResponse:
    """Create new category."""
    _ = token
    return await catalog_services.create_category(
        category_data,
        db=db,
    )


@verify_admin_async()
@catalog.patch(
    '/category/{category_id}',
    status_code=status.HTTP_200_OK,
    response_model=CategoryResponse,
    tags=['admin'],
)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
) -> CategoryResponse:
    """Update category."""
    _ = token
    return await catalog_services.update_category(
        category_id,
        category_data,
        db=db,
    )


@verify_admin_async()
@catalog.delete(
    '/category/{category_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=['admin'],
)
async def delete_category(
    category_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
) -> None:
    """Delete category."""
    _ = token
    await catalog_services.delete_category(category_id, db=db)


@verify_admin_async()
@catalog.post(
    '/category/upload-image/{category_id}',
    summary='Upload image for category',
    description='Upload an image file and update category image_path',
    status_code=status.HTTP_200_OK,
    tags=['admin'],
)
async def upload_category_image(
    category_id: int,
    image: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
) -> str:
    """Upload image for category."""
    _ = token
    return await catalog_services.upload_category_image(
        category_id,
        db=db,
        image=image,
    )


@verify_admin_async()
@catalog.post(
    '/category/media/{category_id}',
    status_code=status.HTTP_201_CREATED,
    tags=['admin'],
)
async def upload_category_media_gallery(
    category_id: int,
    media_type: MediaType,
    order: int,
    new_media: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
) -> str:
    """Upload media to category gallery."""
    _ = token
    return await catalog_services.upload_category_media_gallery(
        category_id,
        media_type=media_type,
        order=order,
        media=new_media,
        db=db,
    )


@catalog.get(
    '/category/media/{category_id}',
    status_code=status.HTTP_200_OK,
    tags=['admin'],
)
async def get_category_media_gallery(
    category_id: int,
    db = Depends(get_async_session),
):
    """Get category media gallery."""
    return await catalog_services.get_category_media_gallery(
        category_id,
        db=db,
    )


@verify_admin_async()
@catalog.delete(
    '/category/media/{category_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=['admin'],
)
async def delete_category_media_gallery(
    category_id: int,
    media_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
) -> None:
    """Delete media from category gallery."""
    _ = token
    await catalog_services.delete_category_media_gallery(
        category_id,
        media_id=media_id,
        db=db,
    )
