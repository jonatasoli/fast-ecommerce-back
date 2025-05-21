import factory
from faker import Faker
from decimal import Decimal
from uuid import uuid4

from app.entities.coupon import CouponInDB
from app.entities.freight import ShippingAddress, Freight
from app.entities.product import ProductCart, ProductInDB
from app.entities.user import UserAddress, UserData
from app.entities.cart import (
    CartBase,
    CartUser,
    CartShipping,
    CartPayment,
    CreateCreditCardPaymentMethod,
    CreateCreditCardTokenPaymentMethod,
    CreatePixPaymentMethod,
    AddressCreate,
)
from tests.fake_functions import fake_cpf, fake_decimal, fake_email, fake_url

fake = Faker()

class ProductCartFactory(factory.Factory):
    class Meta:
        model = ProductCart

    product_id = fake.pyint()
    quantity = fake.pyint(min_value=1, max_value=5)
    price = fake_decimal()
    name = fake.name()
    image_path = fake_url()
    available_quantity = fake.pyint(min_value=1, max_value=100)
    discount_price = Decimal('0')


class FreightFactory(factory.Factory):
    class Meta:
        model = Freight

    price = fake_decimal()
    product_code = fake.random_int()
    delivery_time = fake.random_int(min=1, max=12)
    max_date = fake.future_date()


class CouponInDBFactory(factory.Factory):
    class Meta:
        model = CouponInDB

    discount = fake_decimal()
    discount_price = fake_decimal()
    limit_price = fake_decimal()


class UserDataFactory(factory.Factory):
    class Meta:
        model = UserData

    user_id = fake.random_int()
    email = fake_email()
    name = fake.name()
    document = fake_cpf()
    phone = fake.phone_number()


class ShippingAddressFactory(factory.Factory):
    class Meta:
        model = ShippingAddress

    address = fake.address()
    city = fake.city()
    state = fake.state_abbr()
    zipcode = fake.postcode()
    country = fake.country()


class UserAddressFactory(factory.Factory):
    class Meta:
        model = UserAddress

    user_id = fake.random_int()
    address = fake.street_address()
    address_number = str(fake.random_int())
    address_complement = None
    city = fake.city()
    state = fake.state_abbr()
    zip_code = fake.postcode()
    country = fake.country()
    neighborhood = fake.language_name()


class CartBaseFactory(factory.Factory):
    class Meta:
        model = CartBase

    uuid = fake.uuid4()
    affiliate = None
    cart_items = [factory.SubFactory(ProductCartFactory) for _ in range(2)]
    coupon = None
    discount = Decimal('0')
    zipcode = fake.postcode()
    freight_product_code = fake.random_int()
    freight = factory.SubFactory(FreightFactory)
    subtotal = fake_decimal()
    total = fake_decimal()


class CartUserFactory(CartBaseFactory):
    class Meta:
        model = CartUser

    user_data = factory.SubFactory(UserDataFactory)

class AddressCreateFactory(factory.Factory):
    class Meta:
        model = AddressCreate

    shipping_is_payment = fake.pybool()
    shipping_address = factory.SubFactory(ShippingAddressFactory)
    user_address = factory.SubFactory(UserAddressFactory)

class CartShippingFactory(CartUserFactory):
    class Meta:
        model = CartShipping

    shipping_is_payment = fake.pybool()
    user_address_id = fake.pyint()
    shipping_address_id = factory.SubFactory(UserAddressFactory)
    user_address = factory.SubFactory(UserAddressFactory)


class CartPaymentFactory(CartShippingFactory):
    class Meta:
        model = CartPayment

    payment_method = 'credit_card'
    payment_method_id = fake.uuid4()
    payment_intent = fake.uuid4()
    customer_id = fake.uuid4()
    card_token = fake.uuid4()
    pix_qr_code = fake.uuid4()
    pix_qr_code_base64 = fake.uuid4()
    pix_payment_id = fake.pyint()
    gateway_provider = fake.word()
    installments = fake.random_int(min=1, max=12)
    subtotal_with_fee = fake_decimal()
    total_with_fee = fake_decimal()


class CreateCreditCardPaymentMethodFactory(factory.Factory):
    class Meta:
        model = CreateCreditCardPaymentMethod

    payment_gateway = 'mercadopago'
    number = fake.credit_card_number()
    exp_month = fake.random_int(min=1, max=12)
    exp_year = fake.random_int(min=2024, max=2030)
    cvc = fake.credit_card_security_code()
    name = fake.name()
    installments = fake.random_int(min=1, max=12)


class CreateCreditCardTokenPaymentMethodFactory(factory.Factory):
    class Meta:
        model = CreateCreditCardTokenPaymentMethod

    payment_gateway = 'mercadopago'
    card_token = fake.uuid4()
    card_issuer = fake.word()
    card_brand = fake.credit_card_provider()
    installments = fake.random_int(min=1, max=12)
    brand = fake.credit_card_provider()


class CreatePixPaymentMethodFactory(factory.Factory):
    class Meta:
        model = CreatePixPaymentMethod

    payment_gateway = 'mercadopago'


