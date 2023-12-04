import factory
from factory.declarations import SelfAttribute, SubFactory
from faker import Faker
from app.infra.models.transaction import CreditCardFeeConfig, Payment

from app.infra.models.uploadedimage import UploadedImage
from app.infra.models.users import User
from app.infra.models.role import Role
from app.infra.models.order import Category, Order, OrderStatusSteps, Product
from constants import OrderStatus, StepsOrder
from tests.fake_functions import (
    fake_cpf,
    fake_decimal,
    fake_email,
    fake_url,
    fake_url_path,
)


fake = Faker()

USER_ID_ROLE = 2


class RoleFactory(factory.Factory):
    class Meta:
        model = Role

    role = fake.name()
    active = fake.pybool()


class UserFactory(factory.Factory):
    class Meta:
        model = User

    class Params:
        role = SubFactory(RoleFactory)

    name = fake.name()
    username = fake.user_name()
    email = fake_email()
    document = fake_cpf()
    phone = fake.phone_number()
    password = fake.password()
    role_id = SelfAttribute('role.role_id')


class CategoryFactory(factory.Factory):
    class Meta:
        model = Category

    name = fake.name()
    path = fake_url_path()


class CreditCardFeeConfigFactory(factory.Factory):
    class Meta:
        model = CreditCardFeeConfig

    min_installment_with_fee = factory.LazyFunction(
        lambda: fake.pyint(min_value=1, max_value=5),
    )
    max_installments = factory.LazyFunction(
        lambda: fake.pyint(min_value=6, max_value=12),
    )
    fee = fake_decimal()


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    class Params:
        category = SubFactory(RoleFactory)
        installment_config = SubFactory(CreditCardFeeConfigFactory)

    name = fake.name()
    price = fake.pyint()
    description = fake.json()
    direct_sales = fake.pybool()
    installments_config = SelfAttribute(
        'installment_config.credit_card_fee_config_id',
    )
    uri = fake_url_path()
    sku = fake.pystr()
    category_id = SelfAttribute('category.category_id')
    weight = fake.pyint()
    height = fake.pyint()
    width = fake.pyint()
    length = fake.pyint()
    diameter = fake.pyint()
    active = True


class OrderFactory(factory.Factory):
    class Meta:
        model = Order

    class Params:
        user = SubFactory(UserFactory)

    cart_uuid = fake.uuid4()
    order_date = fake.date_time()
    tracking_number = fake.pystr()
    order_status = OrderStatus.PAYMENT_PENDING.value
    last_updated = fake.date_time()
    checked = fake.pybool()
    customer_id = SelfAttribute('user.user_id')
    discount = fake.pyint()


class PaymentFactory(factory.Factory):
    class Meta:
        model = Payment

    class Params:
        user = SubFactory(UserFactory)

    user_id = SelfAttribute('user.user_id')
    amount = fake.pyint()
    token = fake.pystr()
    gateway_id = fake.pyint()
    status = StepsOrder.PAYMENT_PENDING.value
    authorization = fake.pystr()
    payment_method = fake.pystr()
    payment_gateway = fake.pystr()
    installments = fake.pyint()
    processed = fake.pybool()


class OrderStatusStepsFactory(factory.Factory):
    class Meta:
        model = OrderStatusSteps

    class Params:
        order = SubFactory(OrderFactory)

    order_id = SelfAttribute('order.order_id')
    status = StepsOrder.PAYMENT_PENDING.value
    last_updated = fake.date_time()
    sending = fake.pybool()
    active = fake.pybool()


class UploadedImageFactory(factory.Factory):
    class Meta:
        model = UploadedImage

    original = fake_url()
    small = fake_url()
    thumb = fake_url()
    icon = fake_url()
    uploaded = fake.pybool()
