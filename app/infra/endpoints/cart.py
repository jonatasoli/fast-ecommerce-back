# ruff: noqa:  PLR0913
from fastapi.security import OAuth2PasswordBearer
from app.entities.address import CreateAddress
from app.entities.cart import (
    CartBase,
    CartPayment,
    CartShipping,
    CartUser,
    CreateCheckoutResponse,
    CreateCreditCardPaymentMethod,
    CreateCreditCardTokenPaymentMethod,
    CreatePixPaymentMethod,
)
from app.entities.coupon import CouponResponse
from app.entities.product import ProductCart
from app.infra.bootstrap.cart_bootstrap import Command, bootstrap
from fastapi import APIRouter, Depends, status
from app.infra.database import get_async_session, get_session
from loguru import logger

from app.cart import services

cart = APIRouter(
    prefix='/cart',
    tags=['cart'],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@cart.get(
    '/{coupon}',
    summary='Get coupon',
    description='Search coupon by code and return the coupon if exists',
    status_code=status.HTTP_200_OK,
    response_description='Search Coupon',
    response_model=CouponResponse,
    #     status.HTTP_400_BAD_REQUEST: {
    #         "coupon is invalid",
    #     },
    #     status.HTTP_500_INTERNAL_SERVER_ERROR: {
    #     },
    # },
)
async def get_coupon(
    coupon: str,
    *,
    bootstrap: Command = Depends(get_bootstrap),
) -> CouponResponse:
    """Get coupon."""
    return await services.get_coupon(
        code=coupon,
        bootstrap=bootstrap,
    )


@cart.post('/', response_model=CartBase, status_code=status.HTTP_201_CREATED)
def create_cart(
    *,
    bootstrap: Command = Depends(get_bootstrap),
) -> CartBase:
    """Create or get cart."""
    return services.create_or_get_cart(
        uuid=None,
        token=None,
        bootstrap=bootstrap,
    )


@cart.get('/{uuid}', response_model=CartBase, status_code=201)
def get_cart(
    uuid: str | None = None,
    *,
    token: str = Depends(oauth2_scheme),
    bootstrap: Command = Depends(get_bootstrap),
) -> CartBase:
    """Create or get cart."""
    return services.create_or_get_cart(
        uuid=uuid,
        token=token,
        bootstrap=bootstrap,
    )


@cart.post('/{uuid}/product', status_code=201, response_model=CartBase)
async def add_product_to_cart(  # noqa: ANN201
    uuid: str | None = None,
    *,
    product: ProductCart,
    bootstrap: Command = Depends(get_bootstrap),
):
    """Add product to cart."""
    # TODO: Implementar o retorno 404 caso o estoque tenha acabado
    return await services.add_product_to_cart(
        cart_uuid=uuid,
        product=product,
        bootstrap=bootstrap,
    )


@cart.post('/{uuid}/estimate', status_code=201, response_model=CartBase)
async def estimate(
    uuid: str,
    *,
    cart: CartBase,
    bootstrap: Command = Depends(get_bootstrap),
    session = Depends(get_session),
) -> CartBase:
    """Add product to cart."""
    return await services.calculate_cart(
        uuid=uuid,
        cart=cart,
        bootstrap=bootstrap,
        session=session,
    )


@cart.get('/upsell/{id}', status_code=200)
async def get_upsell_products():   # noqa: ANN201
    """Get products and upsell."""


@cart.post('/{uuid}/user', status_code=201, response_model=CartUser)
async def add_user_to_cart(
    uuid: str,
    *,
    cart: CartBase,
    token: str = Depends(oauth2_scheme),
    bootstrap: Command = Depends(get_bootstrap),
) -> CartUser:
    """Add user to cart."""
    return await services.add_user_to_cart(
        uuid=uuid,
        cart=cart,
        token=token,
        bootstrap=bootstrap,
    )


@cart.post('/{uuid}/address', status_code=201, response_model=CartShipping)
async def add_address_to_cart(
    uuid: str,
    *,
    cart: CartUser,
    address: CreateAddress,
    token: str = Depends(oauth2_scheme),
    bootstrap: Command = Depends(get_bootstrap),
) -> CartShipping:
    """Add user to cart."""
    return await services.add_address_to_cart(
        uuid=uuid,
        cart=cart,
        address=address,
        token=token,
        bootstrap=bootstrap,
    )


@cart.post(
    '/{uuid}/payment/{payment_method}',
    status_code=201,
    response_model=CartPayment,
)
async def add_payment_information_to_cart(
    uuid: str,
    payment_method: str,
    *,
    cart: CartShipping,
    payment: CreateCreditCardPaymentMethod
    | CreateCreditCardTokenPaymentMethod
    | CreatePixPaymentMethod,
    token: str = Depends(oauth2_scheme),
    bootstrap: Command = Depends(get_bootstrap),
) -> CartPayment:
    """Add user to cart."""
    return await services.add_payment_information(
        uuid=uuid,
        payment_method=payment_method,
        cart=cart,
        payment=payment,
        token=token,
        bootstrap=bootstrap,
    )


@cart.get('/{uuid}/preview', status_code=200, response_model=CartPayment)
async def preview_cart(
    uuid: str,
    *,
    token: str = Depends(oauth2_scheme),
    bootstrap: Command = Depends(get_bootstrap),
) -> CartShipping:
    """Add user to cart."""
    return await services.preview(
        uuid=uuid,
        token=token,
        bootstrap=bootstrap,
    )


@cart.post(
    '/{uuid}/checkout',
    status_code=202,
    response_model=CreateCheckoutResponse,
)
async def checkout_cart(
    uuid: str,
    *,
    cart: CartPayment,
    token: str = Depends(oauth2_scheme),
    bootstrap: Command = Depends(get_bootstrap),
) -> CreateCheckoutResponse:
    """Add user to cart."""
    return await services.checkout(
        uuid=uuid,
        cart=cart,
        token=token,
        bootstrap=bootstrap,
    )


@cart.get('/{uuid}/upsell/{id}', status_code=200)
async def get_upsell_products(id):   # noqa: ANN201, ANN001
    """Get upsell products."""
    try:
        # TODO: Implementar o retorno dos produtos upsell
        _ = id
        return True   # noqa: TRY300
    except Exception as e:
        logger.error('Erro ao retornar upsell {e}')
        raise e   # noqa: TRY201
