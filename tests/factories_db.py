from datetime import UTC, datetime
from decimal import Decimal
import factory
from factory.declarations import SelfAttribute, SubFactory
from faker import Faker
from app.infra.constants import InventoryOperation, OrderStatus, StepsOrder
from app.infra.models import (
    CouponsDB,
    CreditCardFeeConfigDB,
    CustomerDB,
    InformUserProductDB,
    InventoryDB,
    PaymentDB,
    UploadedMediaDB,
)
from factory.alchemy import SQLAlchemyModelFactory


from app.infra.models import UserDB
from app.infra.models import RoleDB
from app.infra.models import CategoryDB, OrderDB, OrderStatusStepsDB, ProductDB
from tests.fake_functions import (
    fake_cpf,
    fake_decimal,
    fake_email,
    fake_url,
    fake_url_path,
)


fake = Faker()

USER_ID_ROLE = 2


class FactoryDB(SQLAlchemyModelFactory):  # type: ignore[misc]
    class Meta:
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'flush'


class RoleDBFactory(factory.Factory):
    class Meta:
        model = RoleDB

    role = fake.name()
    active = fake.pybool()


class UserDBFactory(factory.Factory):
    class Meta:
        model = UserDB

    class Params:
        role = SubFactory(RoleDBFactory)

    name = factory.LazyAttribute(lambda _: fake.name())
    username = factory.LazyAttribute(lambda _: fake.user_name())
    email = factory.LazyAttribute(lambda _: fake_email())
    document = factory.LazyAttribute(lambda _: fake_cpf())
    phone = factory.LazyAttribute(lambda _: fake.phone_number())
    password = fake.password()
    role_id = SelfAttribute('role.role_id')


class CategoryFactory(factory.Factory):
    class Meta:
        model = CategoryDB

    name = fake.name()
    path = fake_url_path()


class CreditCardFeeConfigFactory(factory.Factory):
    class Meta:
        model = CreditCardFeeConfigDB

    min_installment_with_fee = factory.LazyFunction(
        lambda: fake.pyint(min_value=1, max_value=5),
    )
    max_installments = factory.LazyFunction(
        lambda: fake.pyint(min_value=6, max_value=12),
    )
    fee = fake_decimal()


class ProductDBFactory(factory.Factory):
    class Meta:
        model = ProductDB

    class Params:
        category = SubFactory(CategoryFactory)
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
        model = OrderDB

    class Params:
        user = SubFactory(UserDBFactory)

    user_id = SelfAttribute('user.user_id')
    cart_uuid = fake.uuid4()
    order_date = fake.date_time()
    tracking_number = fake.pystr()
    order_status = OrderStatus.PAYMENT_PENDING.value
    last_updated = fake.date_time()
    checked = fake.pybool()
    customer_id = str(SelfAttribute('user.user_id'))
    discount = fake.pyint()

class CustomerDBFactory(factory.Factory):
    class Meta:
        model = CustomerDB

    class Params:
        user = SubFactory(UserDBFactory)

    user_id = SelfAttribute('user.user_id')
    customer_uuid = fake.uuid4()
    payment_gateway = fake.random_choices(elements=['mercadopago', 'stripe', 'cielo'])
    payment_method = fake.random_choices(elements=['credit-card', 'pix', 'boleto'])
    token = fake.uuid4()
    issuer_id = fake.random_int()
    status = fake.boolean()
    created_at = fake.date()


class PaymentFactory(factory.Factory):
    class Meta:
        model = PaymentDB

    class Params:
        user = SubFactory(UserDBFactory)

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
        model = OrderStatusStepsDB

    class Params:
        order = SubFactory(OrderFactory)

    order_id = SelfAttribute('order.order_id')
    status = StepsOrder.PAYMENT_PENDING.value
    last_updated = fake.date_time()
    sending = fake.pybool()
    active = fake.pybool()


class UploadedMediaFactory(factory.Factory):
    class Meta:
        model = UploadedMediaDB

    type = fake.pystr()
    uri = fake_url()
    order = fake.random_int()


class InventoryDBFactory(factory.Factory):
    class Meta:
        model = InventoryDB

    class Params:
        product = SubFactory(ProductDBFactory)

    product_id = SelfAttribute('product.product_id')
    quantity = fake.pyint(min_value=10, max_value=999)
    operation = InventoryOperation.INCREASE.value


class CouponFactory(factory.Factory):
    class Meta:
        model = CouponsDB

    code = fake.pystr()
    discount = Decimal('0.1')
    qty = fake.pyint(min_value=1, max_value=999)
    active = True


class InformUserProductDBFactory(factory.Factory):
    class Meta:
        model = InformUserProductDB

    product_id = fake.pyint(min_value=1, max_value=999)
    product_name = fake.pystr()
    user_mail = fake_email()
    user_phone = fake.phone_number()
    sended = fake.pybool()
