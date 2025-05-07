from app.entities.cart import CartPayment, CreateCreditCardPaymentMethod
from app.entities.payment import PaymentNotFoundError
from app.infra.constants import PaymentMethod


async def payment_process(
    payment_method: str,
    *,
    user,
    payment,
    cache_cart,
    bootstrap,
):
    """Payment Process Stripe."""
    customer = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=payment.payment_gateway,
        bootstrap=bootstrap,
    )
    cart = None
    if payment_method  == PaymentMethod.CREDIT_CARD.value:
        cart = await create_payment_credit_card(
            payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            bootstrap=bootstrap,
        )
    else:
        raise PaymentNotFoundError

    return cart


async def create_payment_credit_card(
    payment,
    *,
    user,
    customer,
    cache_cart,
    bootstrap,

):
    payment_method_id = None
    match payment:
        case CreateCreditCardPaymentMethod():
            payment_method_id= bootstrap.payment.create_payment_method(
                payment=payment,
            )
            payment_method_id = bootstrap.payment.attach_customer_in_payment_method(
                payment_gateway=payment.payment_gateway,
                payment_method_id=payment_method_id.get('id'),
                customer_uuid=customer.customer_uuid,
            )
        case _:
            raise PaymentNotFoundError

    installments = payment.installments
    if not payment_method_id:
        raise PaymentNotFoundError

    _payment_method_id = payment_method_id.get('id')
    cart = CartPayment(
        **cache_cart.model_dump(),
        payment_method=PaymentMethod.CREDIT_CARD.value,
        payment_method_id=_payment_method_id,
        gateway_provider=payment.payment_gateway,
        card_token=_payment_method_id,
        customer_id=customer.customer_uuid,
        installments=installments,
    )
    _payment_installment_fee = await bootstrap.cart_uow.get_installment_fee(
        bootstrap=bootstrap,
    )
    if cart.installments >= _payment_installment_fee.min_installment_with_fee:
        cart.calculate_fee(_payment_installment_fee.fee)
    await bootstrap.uow.update_payment_method_to_user(
        user.user_id,
        _payment_method_id,
    )
    return cart
