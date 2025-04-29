import enum


class DocumentType(enum.Enum):
    CPF = 'CPF'


class Roles(enum.Enum):
    ADMIN = 1
    USER = 2
    PARTNER = 3


class PaymentGatewayAvailable(enum.Enum):
    MERCADOPAGO = 'MERCADOPAGO'
    STRIPE = 'STRIPE'


class PaymentGatewayDB(enum.Enum):
    MERCADOPAGO = 1
    STRIPE = 2
    CIELO = 3


class PaymentMethod(enum.Enum):
    CREDIT_CARD = 'credit_card'
    BOLETO = 'boleto'
    PIX = 'pix'
    DEBIT_CARD = 'debit_card'
    CASH = 'cash'


class PaymentStatus(enum.Enum):
    PENDING = 'PENDING'
    PAID = 'PAID'
    CANCELLED = 'CANCELLED'


class InventoryOperation(enum.StrEnum):
    INCREASE = 'INCREASE'
    DECREASE = 'DECREASE'


class FeeType(enum.StrEnum):
    FIXED = 'FIXED'
    PERCENTAGE = 'PERCENTAGE'


class StepsOrder(enum.StrEnum):
    PAYMENT_PENDING = 'PAYMENT_PENDING'
    ORDER_CANCELLED = 'ORDER_CANCELLED'
    PAYMENT_ACCEPT = 'PAYMENT_ACCEPT'
    SELECTED_ITEMS = 'SELECTED_ITEMS'
    GENERATE_INVOICE = 'GENERATE_INVOICE'
    IN_TRANSIT = 'IN_TRANSIT'
    DELIVERED_ORDER = 'DELIVERED_ORDER'


class OrderStatus(enum.StrEnum):
    PAYMENT_PENDING = 'PAYMENT_PENDING'
    PAYMENT_PAID = 'PAYMENT_PAID'
    PAYMENT_CANCELLED = 'PAYMENT_CANCELLED'
    PREPARING_ORDER = 'PREPARING_ORDER'
    SHIPPING_ORDER = 'SHIPPING_ORDER'
    GENERATE_INVOICE = 'GENERATE_INVOICE'
    SHIPPING_COMPLETE = 'SHIPPING_COMPLETE'


class Direction(enum.StrEnum):
    asc = 'asc'
    desc = 'desc'


class UserOrderBy(enum.StrEnum):
    user_id = 'user_id'
    username = 'username'
    string_name = 'string_name'
    mail = 'mail'
    document = 'document'
    phone = 'phone'


class DiscountType(enum.StrEnum):
    PERCENTAGE = 'PERCENTAGE'
    FIXED = 'FIXED'
    FREE_SHIPPING = 'FREE_SHIPPING'


class CurrencyType(enum.StrEnum):
    BRL = 'BRL'
    USD = 'USD'
    EUR = 'EUR'


class MediaType(enum.StrEnum):
    video = 'VIDEO'
    photo = 'PHOTO'
