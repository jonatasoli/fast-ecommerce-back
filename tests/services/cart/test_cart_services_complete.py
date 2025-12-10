from contextlib import asynccontextmanager
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from faker import Faker
from fastapi import HTTPException
from pydantic import ValidationError

from app.cart.services import (
    add_address_to_cart,
    add_payment_information,
    add_user_to_cart,
    calculate_freight,
    checkout,
    consistency_inventory,
    create_or_get_cart,
    get_cart_and_send_to_crm,
    get_coupon,
    preview,
    raise_checkout_error,
)
from app.entities.address import AddressBase, CreateAddress
from app.entities.cart import (
    CartBase,
    CartPayment,
    CartShipping,
    CartUser,
    CheckoutProcessingError,
    InvalidCartUUIDError,
)
from app.entities.coupon import CouponDontMatchWithUserError, CouponNotFoundError
from app.entities.payment import CustomerNotFoundError, PaymentNotFoundError
from app.entities.product import ProductCart, ProductSoldOutError
from app.entities.user import UserData, UserDBGet
from app.infra.constants import PaymentGatewayAvailable, PaymentMethod
from tests.factories import (
    CreateCreditCardPaymentMethodFactory,
    CreatePixPaymentMethodFactory,
    FreightFactory,
    ProductCartFactory,
    UserDataFactory,
)
from tests.factories_db import ProductDBFactory
from tests.fake_functions import fake_decimal

fake = Faker()


def test_raise_checkout_error_should_raise():
    with pytest.raises(CheckoutProcessingError):
        raise_checkout_error()


def test_create_or_get_cart_with_token_should_return_cart(memory_bootstrap):
    # Setup
    bootstrap = memory_bootstrap
    token = fake.uuid4()
    cart = CartBase(uuid=fake.uuid4(), cart_items=[], subtotal=Decimal('0'))
    bootstrap.cache.set(token, cart.model_dump_json(), ex=3600)

    # Act
    result = create_or_get_cart(uuid=None, token=token, bootstrap=bootstrap)

    assert result is not None
    if isinstance(result, str):
        result = CartBase.model_validate_json(result)
    assert isinstance(result, CartBase)


def test_create_or_get_cart_with_uuid_should_return_cart(memory_bootstrap):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    cart = CartBase(uuid=uuid, cart_items=[], subtotal=Decimal('0'))
    bootstrap.cache.set(uuid, cart.model_dump_json(), ex=3600)

    # Act
    result = create_or_get_cart(uuid=uuid, token=None, bootstrap=bootstrap)

    assert result is not None
    if isinstance(result, str):
        result = CartBase.model_validate_json(result)
    assert str(result.uuid) == uuid


def test_create_or_get_cart_without_token_or_uuid_should_create_new(memory_bootstrap):
    # Setup
    bootstrap = memory_bootstrap

    # Act
    result = create_or_get_cart(uuid=None, token=None, bootstrap=bootstrap)

    assert result is not None
    assert isinstance(result, CartBase)
    assert isinstance(result.uuid, (UUID, str))
    assert result.cart_items == []


@pytest.mark.asyncio
async def test_calculate_freight_with_zipcode_should_calculate(
    memory_bootstrap, mocker, asyncdb,
):
    # Setup
    bootstrap = memory_bootstrap
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[ProductCartFactory()],
        subtotal=Decimal('100'),
        zipcode='12345-678',
        freight_product_code='04014',
    )
    products_db = [ProductDBFactory()]

    mocker.patch(
        'app.campaign.repository.get_campaign',
        return_value=None,
    )

    freight_result = FreightFactory(price=Decimal('25.50'))
    bootstrap.freight.calculate_volume_weight = Mock(return_value={'weight': 1000})
    bootstrap.freight.get_freight = Mock(return_value=freight_result)

    # Act
    result = await calculate_freight(cart, products_db, bootstrap, asyncdb)

    assert result.zipcode == '12345678'
    assert result.freight == freight_result
    bootstrap.freight.calculate_volume_weight.assert_called_once()
    bootstrap.freight.get_freight.assert_called_once()


@pytest.mark.asyncio
async def test_calculate_freight_with_campaign_should_apply_free_shipping(
    memory_bootstrap, mocker, asyncdb,
):
    # Setup
    bootstrap = memory_bootstrap
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[ProductCartFactory()],
        subtotal=Decimal('500'),
        zipcode='12345-678',
        freight_product_code='04014',
    )
    products_db = [ProductDBFactory()]

    mock_campaign = Mock()
    mock_campaign.min_purchase_value = Decimal('100')
    mocker.patch(
        'app.campaign.repository.get_campaign',
        return_value=mock_campaign,
    )

    freight_result = FreightFactory(price=Decimal('25.50'))
    bootstrap.freight.calculate_volume_weight = Mock(return_value={'weight': 1000})
    bootstrap.freight.get_freight = Mock(return_value=freight_result)

    # Act
    result = await calculate_freight(cart, products_db, bootstrap, asyncdb)

    assert result.freight.price.quantize(Decimal('0.01')) == Decimal('0.01')


@pytest.mark.asyncio
async def test_calculate_freight_without_freight_code_should_raise(
    memory_bootstrap, mocker, asyncdb,
):
    # Setup
    bootstrap = memory_bootstrap
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[ProductCartFactory()],
        subtotal=Decimal('100'),
        zipcode='12345-678',
        freight_product_code=None,
    )
    products_db = [ProductDBFactory()]

    mocker.patch('app.campaign.repository.get_campaign', return_value=None)
    bootstrap.freight.calculate_volume_weight = Mock(return_value={'weight': 1000})

    with pytest.raises(HTTPException, match='Freight product code not found'):
        await calculate_freight(cart, products_db, bootstrap, asyncdb)


def test_consistency_inventory_with_different_lengths_should_raise():
    # Setup
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[ProductCartFactory(), ProductCartFactory()],
        subtotal=Decimal('100'),
    )
    products_inventory = [ProductDBFactory()]

    with pytest.raises(ProductSoldOutError):
        consistency_inventory(cart, products_inventory=products_inventory)


def test_consistency_inventory_with_insufficient_quantity_should_raise():
    # Setup
    product_cart = ProductCartFactory(product_id=1, quantity=10)
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[product_cart],
        subtotal=Decimal('100'),
    )
    product_db = ProductDBFactory(product_id=1)
    product_db.quantity = 5
    products_inventory = [product_db]

    with pytest.raises(ProductSoldOutError):
        consistency_inventory(cart, products_inventory=products_inventory)


def test_consistency_inventory_with_valid_quantities_should_update_available():
    # Setup
    product_cart = ProductCartFactory(product_id=1, quantity=3)
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[product_cart],
        subtotal=Decimal('100'),
    )
    product_db = ProductDBFactory(product_id=1)
    product_db.quantity = 10
    products_inventory = [product_db]

    # Act
    result = consistency_inventory(cart, products_inventory=products_inventory)

    assert result.cart_items[0].available_quantity == 10


@pytest.mark.asyncio
async def test_add_user_to_cart_should_add_user_data(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    cart = CartBase(uuid=uuid, cart_items=[], subtotal=Decimal('100'))
    token = fake.uuid4()

    user_data_factory = UserDataFactory()
    user = Mock()
    user.user_id = user_data_factory.user_id
    user.email = user_data_factory.email
    user.name = user_data_factory.name
    user.document = user_data_factory.document
    user.phone = user_data_factory.phone

    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart.model_dump_json())
    bootstrap.cache.set = Mock()

    mock_transaction = AsyncMock()

    @asynccontextmanager
    async def mock_begin():
        yield mock_transaction

    mock_session = AsyncMock()
    mock_session.begin = lambda: mock_begin()
    bootstrap.db = lambda: mock_session

    mocker.patch.object(
        bootstrap.cart_uow,
        'get_customer',
        side_effect=CustomerNotFoundError,
    )

    mock_coupon = None
    mocker.patch.object(
        bootstrap.cart_repository,
        'get_coupon_by_code',
        return_value=mock_coupon,
    )

    bootstrap.message.broker.publish = AsyncMock()

    # Act
    result = await add_user_to_cart(uuid, cart, token, bootstrap)

    assert isinstance(result, CartUser)
    assert result.user_data.user_id == user.user_id
    bootstrap.message.broker.publish.assert_called_once()


@pytest.mark.asyncio
async def test_add_user_to_cart_with_invalid_coupon_should_raise(
    memory_bootstrap, mocker,
):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    cart = CartBase(uuid=uuid, cart_items=[], subtotal=Decimal('100'), coupon='INVALID')
    token = fake.uuid4()

    user_data_factory = UserDataFactory()
    user = Mock()
    user.user_id = user_data_factory.user_id
    user.email = user_data_factory.email
    user.name = user_data_factory.name
    user.document = user_data_factory.document
    user.phone = user_data_factory.phone

    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart.model_dump_json())

    mock_transaction = AsyncMock()

    @asynccontextmanager
    async def mock_begin():
        yield mock_transaction

    mock_session = AsyncMock()
    mock_session.begin = lambda: mock_begin()
    bootstrap.db = lambda: mock_session

    mocker.patch.object(
        bootstrap.cart_uow, 'get_customer', side_effect=CustomerNotFoundError,
    )
    bootstrap.message.broker.publish = AsyncMock()

    async def mock_get_coupon(*args, **kwargs):
        return None

    mocker.patch.object(
        bootstrap.cart_repository,
        'get_coupon_by_code',
        side_effect=mock_get_coupon,
    )

    with pytest.raises(CouponNotFoundError):
        await add_user_to_cart(uuid, cart, token, bootstrap)


@pytest.mark.asyncio
async def test_add_user_to_cart_with_coupon_user_mismatch_should_raise(
    memory_bootstrap, mocker,
):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    cart = CartBase(uuid=uuid, cart_items=[], subtotal=Decimal('100'), coupon='USER123')
    token = fake.uuid4()

    user_data_factory = UserDataFactory()
    user = Mock()
    user.user_id = user_data_factory.user_id
    user.email = user_data_factory.email
    user.name = user_data_factory.name
    user.document = user_data_factory.document
    user.phone = user_data_factory.phone

    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart.model_dump_json())

    mock_transaction = AsyncMock()

    @asynccontextmanager
    async def mock_begin():
        yield mock_transaction

    mock_session = AsyncMock()
    mock_session.begin = lambda: mock_begin()
    bootstrap.db = lambda: mock_session

    mocker.patch.object(
        bootstrap.cart_uow, 'get_customer', side_effect=CustomerNotFoundError,
    )
    bootstrap.message.broker.publish = AsyncMock()

    mock_coupon = Mock()
    mock_coupon.user_id = user.user_id + 999

    async def mock_get_coupon(*args, **kwargs):
        return mock_coupon

    mocker.patch.object(
        bootstrap.cart_repository,
        'get_coupon_by_code',
        side_effect=mock_get_coupon,
    )

    with pytest.raises(CouponDontMatchWithUserError):
        await add_user_to_cart(uuid, cart, token, bootstrap)


@pytest.mark.asyncio
async def test_add_address_to_cart_should_create_addresses(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_user = CartUser(
        uuid=uuid,
        cart_items=[],
        subtotal=Decimal('100'),
        user_data=user_data,
    )

    address = CreateAddress(
        user_address=AddressBase(
            address_id=None,
            user_id=None,
            zipcode=fake.postcode(),
            street=fake.street_address(),
            street_number=fake.building_number(),
            city=fake.city(),
            state=fake.state_abbr(),
            address_complement=fake.secondary_address() or '',
            neighborhood=fake.city(),
            country='BR',
            active=True,
        ),
        shipping_address=AddressBase(
            address_id=None,
            user_id=None,
            zipcode=fake.postcode(),
            street=fake.street_address(),
            street_number=fake.building_number(),
            city=fake.city(),
            state=fake.state_abbr(),
            address_complement=fake.secondary_address() or '',
            neighborhood=fake.city(),
            country='BR',
            active=True,
        ),
        shipping_is_payment=False,
    )

    token = fake.uuid4()
    user = Mock()
    user.user_id = user_data.user_id

    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart_user.model_dump_json())
    bootstrap.cache.set = Mock()

    user_address_id = fake.random_int()
    shipping_address_id = fake.random_int()
    bootstrap.uow.get_address_by_id = AsyncMock(return_value=None)
    bootstrap.uow.create_address = AsyncMock(
        side_effect=[user_address_id, shipping_address_id],
    )

    # Act
    result = await add_address_to_cart(uuid, cart_user, address, token, bootstrap)

    assert isinstance(result, CartShipping)
    assert result.user_address_id == user_address_id
    assert result.shipping_address_id == shipping_address_id
    assert not result.shipping_is_payment


@pytest.mark.asyncio
async def test_add_address_to_cart_with_existing_address_should_use_it(
    memory_bootstrap, mocker,
):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_user = CartUser(
        uuid=uuid,
        cart_items=[],
        subtotal=Decimal('100'),
        user_data=user_data,
    )

    existing_address_id = fake.random_int()
    address = CreateAddress(
        user_address=AddressBase(
            address_id=existing_address_id,
            user_id=None,
            zipcode=fake.postcode(),
            street=fake.street_address(),
            street_number=fake.building_number(),
            city=fake.city(),
            state=fake.state_abbr(),
            address_complement=fake.secondary_address() or '',
            neighborhood=fake.city(),
            country='BR',
            active=True,
        ),
        shipping_address=None,
        shipping_is_payment=True,
    )

    token = fake.uuid4()
    user = Mock()
    user.user_id = user_data.user_id

    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart_user.model_dump_json())
    bootstrap.cache.set = Mock()

    bootstrap.uow.get_address_by_id = AsyncMock(return_value=existing_address_id)

    # Act
    result = await add_address_to_cart(uuid, cart_user, address, token, bootstrap)

    assert isinstance(result, CartShipping)
    assert result.user_address_id == existing_address_id
    assert result.shipping_is_payment


@pytest.mark.asyncio
async def test_add_payment_information_should_process_payment(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_shipping = CartShipping(
        uuid=uuid,
        cart_items=[],
        subtotal=Decimal('100'),
        user_data=user_data,
        user_address_id=fake.random_int(),
        shipping_address_id=fake.random_int(),
        shipping_is_payment=True,
    )

    payment = CreateCreditCardPaymentMethodFactory()
    payment.payment_gateway = PaymentGatewayAvailable.STRIPE.name
    payment_method = PaymentMethod.CREDIT_CARD.value
    token = fake.uuid4()

    user = Mock()
    user.user_id = user_data.user_id

    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart_shipping.model_dump_json())
    bootstrap.cache.set = Mock()

    bootstrap.cart_uow.get_customer = AsyncMock(return_value=None)

    cart_payment = CartPayment(
        **cart_shipping.model_dump(),
        payment_method_id=fake.uuid4(),
        gateway_provider=PaymentGatewayAvailable.STRIPE.name,
        payment_method=payment_method,
    )

    mock_payment_process = AsyncMock(return_value=cart_payment)
    mocker.patch(
        'app.payment.payment_process_stripe.payment_process',
        new=mock_payment_process,
    )

    # Act
    result = await add_payment_information(
        uuid, payment_method, cart_shipping, payment, token, bootstrap,
    )

    assert isinstance(result, CartPayment)


@pytest.mark.asyncio
async def test_add_payment_information_without_gateway_should_raise(memory_bootstrap):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_shipping = CartShipping(
        uuid=uuid,
        cart_items=[],
        subtotal=Decimal('100'),
        user_data=user_data,
        user_address_id=fake.random_int(),
        shipping_address_id=fake.random_int(),
        shipping_is_payment=True,
    )

    payment = CreatePixPaymentMethodFactory()
    payment.payment_gateway = None
    payment_method = PaymentMethod.PIX.value
    token = fake.uuid4()

    user = Mock()
    bootstrap.user.get_user = Mock(return_value=user)
    bootstrap.cache.get = Mock(return_value=cart_shipping.model_dump_json())

    with pytest.raises(PaymentNotFoundError):
        await add_payment_information(
            uuid, payment_method, cart_shipping, payment, token, bootstrap,
        )


@pytest.mark.asyncio
async def test_preview_should_create_payment_intent_for_stripe(
    memory_bootstrap, mocker,
):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_payment = CartPayment(
        uuid=uuid,
        cart_items=[],
        subtotal=Decimal('100'),
        user_data=user_data,
        user_address_id=fake.random_int(),
        shipping_address_id=fake.random_int(),
        shipping_is_payment=True,
        payment_method_id=fake.uuid4(),
        gateway_provider=PaymentGatewayAvailable.STRIPE.name,
        payment_method=PaymentMethod.CREDIT_CARD.value,
    )

    token = fake.uuid4()
    user = Mock()
    user.user_id = user_data.user_id

    user_db = UserDBGet(
        user_id=user_data.user_id,
        email=user_data.email,
        name=user_data.name,
        document=user_data.document,
        phone=user_data.phone,
        role_id=1,
        customer_id=None,
    )
    bootstrap.user.get_user = Mock(return_value=user_db)
    bootstrap.cache.get = Mock(return_value=cart_payment.model_dump_json().encode())
    bootstrap.cache.set = Mock()

    mock_customer = Mock()
    mock_customer.customer_uuid = fake.uuid4()
    bootstrap.cart_uow.get_customer = AsyncMock(return_value=mock_customer)

    payment_intent_id = fake.uuid4()
    bootstrap.payment.create_payment_intent = Mock(
        return_value={'id': payment_intent_id},
    )

    # Act
    result = await preview(uuid, token, bootstrap)

    assert result.payment_intent == payment_intent_id
    bootstrap.payment.create_payment_intent.assert_called_once()


@pytest.mark.asyncio
async def test_checkout_should_process_order(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_payment = CartPayment(
        uuid=uuid,
        cart_items=[ProductCartFactory()],
        subtotal=Decimal('100'),
        user_data=user_data,
        user_address_id=fake.random_int(),
        shipping_address_id=fake.random_int(),
        shipping_is_payment=True,
        payment_method_id=fake.uuid4(),
        gateway_provider=PaymentGatewayAvailable.STRIPE.name,
        payment_method=PaymentMethod.CREDIT_CARD.value,
    )

    token = fake.uuid4()
    user = Mock()
    user.user_id = user_data.user_id
    user.email = user_data.email
    user.name = user_data.name
    user.document = user_data.document

    from app.entities.user import UserDBGet

    user_db = UserDBGet(
        user_id=user_data.user_id,
        email=user_data.email,
        name=user_data.name,
        document=user_data.document,
        phone=user_data.phone,
        role_id=1,
        customer_id=None,
    )
    bootstrap.user.get_user = Mock(return_value=user_db)
    bootstrap.cache.get = Mock(return_value=cart_payment.model_dump_json().encode())

    order_id = fake.random_int()
    gateway_payment_id = fake.uuid4()
    checkout_result = {
        'message': 'Order created successfully',
        'order_id': [order_id],
        'gateway_payment_id': [gateway_payment_id],
    }
    bootstrap.message.broker.publish = AsyncMock(return_value=checkout_result)

    # Act
    result = await checkout(uuid, cart_payment, token, bootstrap)

    assert result.order_id == str(order_id)
    assert result.gateway_payment_id == str(gateway_payment_id)
    assert result.status == 'processing'


@pytest.mark.asyncio
async def test_checkout_without_order_id_should_raise(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    uuid = str(fake.uuid4())
    user_data = UserDataFactory()
    cart_payment = CartPayment(
        uuid=uuid,
        cart_items=[ProductCartFactory()],
        subtotal=Decimal('100'),
        user_data=user_data,
        user_address_id=fake.random_int(),
        shipping_address_id=fake.random_int(),
        shipping_is_payment=True,
        payment_method_id=fake.uuid4(),
        gateway_provider=PaymentGatewayAvailable.STRIPE.name,
        payment_method=PaymentMethod.CREDIT_CARD.value,
    )

    token = fake.uuid4()
    user = Mock()
    user.user_id = user_data.user_id
    user.email = user_data.email
    user.name = user_data.name
    user.document = user_data.document

    from app.entities.user import UserDBGet

    user_db = UserDBGet(
        user_id=user_data.user_id,
        email=user_data.email,
        name=user_data.name,
        document=user_data.document,
        phone=user_data.phone,
        role_id=1,
        customer_id=None,
    )
    bootstrap.user.get_user = Mock(return_value=user_db)
    bootstrap.cache.get = Mock(return_value=cart_payment.model_dump_json().encode())

    checkout_result = {'message': 'Error', 'order_id': None}
    bootstrap.message.broker.publish = AsyncMock(return_value=checkout_result)

    with pytest.raises(CheckoutProcessingError):
        await checkout(uuid, cart_payment, token, bootstrap)


@pytest.mark.asyncio
async def test_get_coupon_should_return_coupon(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    code = 'DISCOUNT50'

    mock_transaction = AsyncMock()

    @asynccontextmanager
    async def mock_begin():
        yield mock_transaction

    mock_session = AsyncMock()
    mock_session.begin = lambda: mock_begin()
    bootstrap.db = lambda: mock_session

    mock_coupon = Mock()
    mock_coupon.coupon_id = fake.random_int()
    mock_coupon.code = code
    mock_coupon.discount = Decimal('0.50')

    async def mock_get_coupon(*args, **kwargs):
        return mock_coupon

    mocker.patch.object(
        bootstrap.cart_uow,
        'get_coupon_by_code',
        side_effect=mock_get_coupon,
    )

    # Act
    result = await get_coupon(code, bootstrap)

    assert result == mock_coupon


@pytest.mark.asyncio
async def test_get_coupon_not_found_should_raise(memory_bootstrap, mocker):
    # Setup
    bootstrap = memory_bootstrap
    code = 'INVALID'

    mock_transaction = AsyncMock()

    @asynccontextmanager
    async def mock_begin():
        yield mock_transaction

    mock_session = AsyncMock()
    mock_session.begin = lambda: mock_begin()
    bootstrap.db = lambda: mock_session

    async def mock_get_coupon_none(*args, **kwargs):
        return None

    mocker.patch.object(
        bootstrap.cart_uow,
        'get_coupon_by_code',
        side_effect=mock_get_coupon_none,
    )

    with pytest.raises(HTTPException, match='Coupon not found'):
        await get_coupon(code, bootstrap)


@pytest.mark.asyncio
async def test_get_cart_and_send_to_crm_should_process_carts(mocker):
    # Setup
    mock_cache = Mock()
    mock_redis = Mock()

    user_data = UserDataFactory()
    cart_user = CartUser(
        uuid=fake.uuid4(),
        cart_items=[ProductCartFactory()],
        subtotal=Decimal('100'),
        user_data=user_data,
    )

    keys = [f'cart:{fake.uuid4()}', f'cart:{fake.uuid4()}']
    mock_cache.get_all_keys_with_lower_ttl = Mock(return_value=keys)
    mock_redis.get = Mock(return_value=cart_user.model_dump_json())
    mock_redis.delete = Mock()
    mock_cache.redis = mock_redis

    mock_send_crm = mocker.patch(
        'app.cart.services.send_abandonated_cart_to_crm',
        new=AsyncMock(),
    )

    mock_cache_class = Mock(return_value=mock_cache)

    # Act
    await get_cart_and_send_to_crm(_cache=mock_cache_class)

    assert mock_send_crm.call_count == 2
    assert mock_redis.delete.call_count == 2


@pytest.mark.asyncio
async def test_get_cart_and_send_to_crm_should_delete_invalid_carts(mocker):
    # Setup
    mock_cache = Mock()
    mock_redis = Mock()

    keys = [f'cart:{fake.uuid4()}']
    mock_cache.get_all_keys_with_lower_ttl = Mock(return_value=keys)
    mock_redis.get = Mock(return_value='invalid json')
    mock_redis.delete = Mock()
    mock_cache.redis = mock_redis

    mock_cache_class = Mock(return_value=mock_cache)

    # Act
    await get_cart_and_send_to_crm(_cache=mock_cache_class)

    mock_redis.delete.assert_called_once_with(keys[0])
