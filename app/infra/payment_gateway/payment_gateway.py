
from typing import Any
from app.infra.payment_gateway import stripe, mercadopago_gateway
from pydantic import BaseModel


class PaymentGatewayCommmand(BaseModel):
    STRIPE: Any = stripe
    MERCADOPAGO: Any = mercadopago_gateway
