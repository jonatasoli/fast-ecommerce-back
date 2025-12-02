# ruff: noqa: ANN401 TRY301 TRY300
from typing import Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.infra.constants import CurrencyType, MediaType
from app.user.services import verify_admin, verify_admin_sync
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.orm import Session
from app.entities.product import (
    InventoryTransaction,
    ProductCreate,
    ProductInDB,
    ProductInDBResponse,
    ProductPatchRequest,
)
from app.infra.database import get_async_session, get_session

from app.order import services
from app.product import services as product_services
from app.infra import deps
from app.infra.deps import get_db

product = APIRouter(
    prefix='/product',
    tags=['product'],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@product.post(
    '/upload-image/{product_id}',
    summary='Put image in product.',
    description='Get product_id and image file and update to image client.',
    status_code=status.HTTP_200_OK,
    tags=['admin'],
)
async def upload_image(
    product_id: int,
    *,
    db: Session = Depends(get_async_session),
    image: UploadFile = File(...),
) -> str:
    """Upload image."""
    try:
        return await product_services.upload_image(product_id, db=db, image=image)
    except Exception:
        raise


@product.get(
    '/inventory',
    status_code=status.HTTP_200_OK,
    tags=['admin'],
)
async def get_product_inventory(
    page: int = 1,
    offset: int = 10,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
):
    """Get products inventory."""
    return await product_services.get_inventory(
        token=token, page=page, offset=offset, db=db,
    )


@product.get(
    '/{product_id}',
    status_code=status.HTTP_200_OK,
    response_model=ProductInDB,
)
async def get_product_by_id(
        product_id: int,
        db = Depends(get_async_session),
) -> ProductInDB:
    """GET product by id."""
    product = await services.get_product_by_id(product_id, db=db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found',
        )
    return product


@product.get(
    '/uri/{uri:path}',
    status_code=status.HTTP_200_OK,
    response_model=ProductInDB,
)
def get_product_uri(uri: str, db: Session = Depends(get_db)) -> ProductInDB:
    """GET product uri."""
    product = services.get_product(db, uri)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found',
        )

    return product


@product.get('/products/{query_name}', status_code=status.HTTP_200_OK)
async def get_product_by_name( # noqa: PLR0913
    query_name: str,
    offset: int = 2,
    page: int = 1,
    currency: CurrencyType = CurrencyType.BRL,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_async_session),
):
    """Get products inventory by name."""
    await verify_admin(token, db=db)
    return await product_services.get_inventory_name(
        query_name, currency=currency, page=page, offset=offset, db=db,
    )


@product.post(
    '/inventory/{product_id}/transaction',
    status_code=status.HTTP_201_CREATED,
    tags=['admin'],
)
async def product_inventory(
    product_id: int,
    inventory: InventoryTransaction,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
):
    """Get products inventory."""
    return await product_services.inventory_transaction(
        product_id,
        inventory=inventory,
        token=token,
        db=db,
    )

@product.post(
    '/',
    summary='[Admin] Create new product',
    status_code=status.HTTP_201_CREATED,
    response_model=ProductInDBResponse,
    tags=['admin'],
)
async def create_product(
    *,
    token: str = Depends(oauth2_scheme),
    db= Depends(get_async_session),
    product_data: ProductCreate,
) -> ProductInDBResponse:
    """Create product."""
    await verify_admin(token, db=db)
    product = await product_services.create_product(product_data, db=db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Error in create product',
        )
    return product


@verify_admin_sync()
@product.post(
    '/media/{product_id}',
    status_code=status.HTTP_201_CREATED,
)
async def upload_media_gallery( #noqa: PLR0913
    product_id: int,
    *,
    media_type: MediaType,
    order: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
    new_media: UploadFile = File(...),
):
    """Upload media in gallery."""
    _ = token
    return await product_services.upload_media_gallery(
        product_id,
        order=order,
        media_type=media_type,
        db=db,
        media=new_media,
    )


@product.get(
    '/media/{uri}',
    status_code=status.HTTP_200_OK,
    tags=['admin'],
 )
async def get_media_gallery(
        uri: str,
        db: Session = Depends(get_async_session),
):
    """Get media gallery."""
    try:
        return await product_services.get_media_gallery(
            uri,
            db=db,
        )
    except Exception:
        raise


@product.delete(
    '/media/{product_id}',
     status_code=status.HTTP_204_NO_CONTENT,
     tags=['admin'],
 )
async def delete_image(
        product_id: int,
        media_id: int,
        db: Session = Depends(get_async_session),
):
    """Delete image."""
    try:
        return await product_services.delete_media_gallery(
            product_id,
            media_id=media_id,
            db=db,
        )
    except Exception:
        raise


@product.patch(
    '/{product_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Update data in product',
    description='Update product information',
    tags=['admin'],
)
async def patch_product(
    product_id: int,
    columns_update: ProductPatchRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
) -> None:
    """Patch product."""
    await verify_admin(token, db=db)
    await product_services.update_product(
        product_id,
        update_data=columns_update,
        db=db,
    )


@product.delete(
    '/delete/{id}',
    status_code=status.HTTP_204_NO_CONTENT,
    tags=['admin'],
)
async def delete_product(
    id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
 ) -> None:
    """Delete product."""
    try:
        _ = token
        return await product_services.delete_product(db, id)
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
