from app.entities.cart import (
    CartPayment,
    CreateCreditCardPaymentMethod,
    CreateCreditCardTokenPaymentMethod,
)
from app.entities.payment import PaymentNotFoundError
from app.infra.constants import PaymentMethod
from loguru import logger


async def payment_process(
    payment_method: str,
    *,
    user,
    payment,
    cache_cart,
    bootstrap,
):
    """Payment Process Stripe."""
    logger.info(
        '💳 Iniciando processamento de pagamento Stripe | '
        'Método: %s | Gateway: %s | Usuário: %s',
        payment_method,
        getattr(payment, 'payment_gateway', None),
        user.email,
    )
    logger.debug(f'payment_process called: payment_method={payment_method}, payment_gateway={getattr(payment, "payment_gateway", None)}')
    customer = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=payment.payment_gateway,
        bootstrap=bootstrap,
    )
    logger.debug(f'Customer retrieved: {customer.customer_uuid if customer else None}')
    logger.debug(f'PaymentMethod.CREDIT_CARD.value={PaymentMethod.CREDIT_CARD.value}, payment_method={payment_method}')
    normalized_payment_method = payment_method.replace('_', '-')
    logger.debug(f'normalized_payment_method={normalized_payment_method}, match={normalized_payment_method == PaymentMethod.CREDIT_CARD.value}')
    cart = None
    if normalized_payment_method == PaymentMethod.CREDIT_CARD.value:
        logger.debug('Calling create_payment_credit_card')
        cart = await create_payment_credit_card(
            payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            bootstrap=bootstrap,
        )
    else:
        logger.error(f'Invalid payment_method: {payment_method} (normalized: {normalized_payment_method}), expected: {PaymentMethod.CREDIT_CARD.value}')
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
    """Create payment with credit card using Stripe token (PaymentMethod ID)."""
    logger.debug(f'create_payment_credit_card called with payment type: {type(payment)}')
    logger.debug(f'payment object: {payment}')
    _payment_method_id = None
    match payment:
        case CreateCreditCardPaymentMethod():
            raise PaymentNotFoundError(
                'Stripe now requires PaymentMethod token. '
                'Use CreateCreditCardTokenPaymentMethod com o PaymentMethod ID do Stripe Elements.',
            )
        case CreateCreditCardTokenPaymentMethod():
            _payment_method_id = payment.card_token
            logger.debug(
                f'Creating payment with card_token={_payment_method_id}, customer_uuid={customer.customer_uuid}',
            )
            try:
                payment_method_id = bootstrap.payment.attach_customer_in_payment_method(
                    payment_gateway=payment.payment_gateway,
                    payment_method_id=_payment_method_id,
                    customer_uuid=customer.customer_uuid,
                )
                logger.debug(
                    f'Attached payment method, response={payment_method_id}, type={type(payment_method_id)}',
                )
                if isinstance(payment_method_id, dict):
                    _payment_method_id = payment_method_id.get('id', _payment_method_id)
                elif payment_method_id:
                    _payment_method_id = payment_method_id
                logger.debug(
                    f'Final payment_method_id set to {_payment_method_id}',
                )
            except Exception as e:
                logger.error(f'Erro ao anexar payment method: {e}')
                raise PaymentNotFoundError(f'Erro ao processar payment method: {e}') from e
        case _:
            raise PaymentNotFoundError

    installments = payment.installments
    logger.debug(f'After match, _payment_method_id={_payment_method_id}, installments={installments}')
    if not _payment_method_id:
        logger.error(f'Payment method ID não encontrado. payment={payment}, _payment_method_id={_payment_method_id}')
        raise PaymentNotFoundError('Payment method ID não encontrado')

    cart = CartPayment(
        **cache_cart.model_dump(),
        payment_method=PaymentMethod.CREDIT_CARD.value,
        payment_method_id=_payment_method_id,
        gateway_provider=payment.payment_gateway,
        card_token=_payment_method_id,
        customer_id=customer.customer_uuid,
        installments=installments,
    )
    if cart.subtotal <= 0 and cart.cart_items:
        cart.subtotal = sum((item.price or Decimal('0')) * item.quantity for item in cart.cart_items)
        cart.total = cart.subtotal
        logger.warning(f'Subtotal estava 0; recalculado para {cart.subtotal} a partir dos itens')
    logger.info(
        '✅ Pagamento Stripe configurado com sucesso | '
        'PaymentMethod ID: %s | Parcelas: %s | Valor: R$ %s',
        _payment_method_id,
        installments,
        cart.total,
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
