import enum


class StepsOrder(enum.Enum):
    PAYMENT_PENDING = 'PAYMENT_PENDING'
    ORDER_CANCELLED = 'ORDER_CANCELLED'
    PAYMENT_ACCEPT = 'PAYMENT_ACCEPT'
    SELECTED_ITEMS = 'SELECTED_ITEMS'
    GENERATE_INVOICE = 'GENERATE_INVOICE'
    IN_TRANSIT = 'IN_TRANSIT'
    DELIVERED_ORDER = 'DELIVERED_ORDER'


class OrderStatus(enum.Enum):
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
    string_name = 'name'
    mail = 'mail'
    document = 'document'
    phone = 'phone'
