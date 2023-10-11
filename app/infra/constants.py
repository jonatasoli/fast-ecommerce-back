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


class PaymentMethod(enum.Enum):
    CREDIT_CARD = 'credit_card'
    BOLETO = 'boleto'
    PIX = 'pix'
    DEBIT_CARD = 'debit_card'
    CASH = 'cash'


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


class PaymentStatus(enum.Enum):
    PENDING = 'PENDING'
    PAID = 'PAID'
    CANCELLED = 'CANCELLED'


class InventoryOperation(enum.Enum):
    INCREASE = 'INCREASE'
    DECREASE = 'DECREASE'
