from app.cart import repository
from app.entities.cart import (
    CartPayment,
    CreateCreditCardTokenPaymentMethod,
    CreatePixPaymentMethod,
)
from app.entities.payment import PaymentDataInvalidError, PaymentNotFoundError
from app.infra.constants import PaymentMethod
from app.infra.payment_gateway import mercadopago_gateway


async def payment_process(
    payment_method: str,
    *,
    user,
    payment,
    cache_cart,
    bootstrap,

):
    """Payment Process Mercado pago."""
    customer = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=payment.payment_gateway,
        bootstrap=bootstrap,
    )
    cart = None
    if payment_method == PaymentMethod.PIX.value:
        cart = await create_payment_pix(
            payment,
            payment_method=payment_method,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
        )
    elif payment_method  == PaymentMethod.CREDIT_CARD.value:
        cart = await create_payment_credit_card(
            payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            db=bootstrap.db,
        )
    else:
        raise PaymentNotFoundError

    return cart



async def create_payment_pix(
    payment,
    *,
    payment_method,
    user,
    customer,
    cache_cart,
    client = mercadopago_gateway,
):
    if not isinstance(
        payment,
        CreatePixPaymentMethod,
    ):
        raise PaymentDataInvalidError

    description = " ".join(
        item.name for item in cache_cart.cart_items if item.name
    )

    _payment = client.create_pix(
        customer.customer_uuid,
        customer_email=user.email,
        description=description,
        amount=int(cache_cart.total),
    )
    qr_code = _payment.point_of_interaction.transaction_data.qr_code
    qr_code_base64 = (
        _payment.point_of_interaction.transaction_data.qr_code_base64
    )
    payment_id = _payment.id
    cart = CartPayment(
        **cache_cart.model_dump(),
        payment_method=payment_method,
        gateway_provider=payment.payment_gateway,
        customer_id=customer.customer_uuid,
        pix_qr_code=qr_code,
        pix_qr_code_base64=qr_code_base64,
        pix_payment_id=payment_id,
        payment_method_id=str(payment_id),
    )
    return cart

async def create_payment_credit_card(
    payment,
    *,
    user,
    customer,
    cache_cart,
    db,
    client = mercadopago_gateway,
):

    payment_method_id = None
    match payment:
        case CreateCreditCardTokenPaymentMethod():
            payment_method_id = client.attach_customer_in_payment_method(
                payment_method_id=payment.card_brand,
                card_token=payment.card_token,
                card_issuer=payment.card_issuer,
                customer_uuid=customer.customer_uuid,
            )
        case _:
            raise PaymentNotFoundError

    installments = payment.installments
    if not payment_method_id:
        raise PaymentNotFoundError

    cart = CartPayment(
        **cache_cart.model_dump(),
        payment_method=PaymentMethod.CREDIT_CARD.value,
        payment_method_id=payment_method_id,
        gateway_provider=payment.payment_gateway,
        card_token=getattr(payment, 'card_token', None),
        customer_id=customer.customer_uuid,
        installments=installments,
    )
    async with db().begin() as transaction:
        _payment_installment_fee = await repository.get_installment_fee(
            transaction=transaction,
        )

        if cart.installments >= _payment_installment_fee.min_installment_with_fee:
            cart.calculate_fee(_payment_installment_fee.fee)
        await repository.update_payment_method_to_user(
            user.user_id,
            payment_method_id,
            transaction=transaction,
        )
    return cart
