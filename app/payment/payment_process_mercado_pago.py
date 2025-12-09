from decimal import Decimal

from loguru import logger
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
    emoji = '📱' if payment_method.replace('_', '-') == PaymentMethod.PIX.value else '💳'
    logger.info(
        '%s Iniciando processamento de pagamento Mercado Pago | '
        'Método: %s | Gateway: %s | Usuário: %s',
        emoji,
        payment_method,
        payment.payment_gateway,
        user.email,
    )
    logger.debug(f'payment_process MercadoPago: payment_method={payment_method}, payment_gateway={payment.payment_gateway}')
    normalized_payment_method = payment_method.replace('_', '-')
    logger.debug(f'normalized_payment_method={normalized_payment_method}, PIX.value={PaymentMethod.PIX.value}')
    customer = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=payment.payment_gateway,
        bootstrap=bootstrap,
    )
    logger.debug(f'Customer retrieved: {customer.customer_uuid if customer else None}')
    cart = None
    if normalized_payment_method == PaymentMethod.PIX.value:
        cart = await create_payment_pix(
            payment,
            payment_method=payment_method,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
        )
    elif normalized_payment_method == PaymentMethod.CREDIT_CARD.value:
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
    client=mercadopago_gateway,
):
    logger.debug(f'create_payment_pix called: payment_method={payment_method}, payment_gateway={payment.payment_gateway}')
    if not isinstance(
        payment,
        CreatePixPaymentMethod,
    ):
        raise PaymentDataInvalidError

    description = ' '.join(item.name for item in cache_cart.cart_items if item.name)
    amount = cache_cart.total if cache_cart.total > 0 else cache_cart.subtotal
    if not amount or amount <= 0:
        amount = sum((item.price or 0) * item.quantity for item in cache_cart.cart_items)
        cache_cart.subtotal = amount
        cache_cart.total = amount
    logger.debug(
        f'Creating PIX payment: customer={customer.customer_uuid}, total={cache_cart.total}, subtotal={cache_cart.subtotal}, amount={amount}',
    )

    if not amount or amount <= 0:
        logger.error(f'Amount inválido para PIX: total={cache_cart.total}, subtotal={cache_cart.subtotal}')
        raise PaymentDataInvalidError('Amount must be greater than 0')

    logger.info(
        '📱 Criando pagamento PIX | Valor: R$ %s | Cliente: %s',
        amount,
        user.email,
    )
    _payment = client.create_pix(
        customer.customer_uuid,
        customer_email=user.email,
        description=description,
        amount=int(amount * 100),
    )
    qr_code = _payment.point_of_interaction.transaction_data.qr_code
    qr_code_base64 = _payment.point_of_interaction.transaction_data.qr_code_base64
    payment_id = _payment.id
    logger.info(
        '✅ Pagamento PIX criado com sucesso | Payment ID: %s | QR Code gerado',
        payment_id,
    )
    logger.debug(f'PIX payment created: payment_id={payment_id}, qr_code length={len(qr_code) if qr_code else 0}')
    cache_cart.subtotal = Decimal(str(amount))
    cache_cart.total = Decimal(str(amount))
    cart_dict = cache_cart.model_dump()
    cart_payment = CartPayment(
        **cart_dict,
        payment_method=payment_method,
        gateway_provider=payment.payment_gateway,
        customer_id=customer.customer_uuid,
        pix_qr_code=qr_code,
        pix_qr_code_base64=qr_code_base64,
        pix_payment_id=payment_id,
        payment_method_id=str(payment_id),
    )
    logger.info(
        '✅ CartPayment PIX configurado | Gateway: %s | Valor: R$ %s',
        cart_payment.gateway_provider,
        cart_payment.total,
    )
    logger.debug(f'CartPayment created for PIX: payment_method={cart_payment.payment_method}, gateway_provider={cart_payment.gateway_provider}')
    return cart_payment


async def create_payment_credit_card(
    payment,
    *,
    user,
    customer,
    cache_cart,
    db,
    client=mercadopago_gateway,
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

    logger.info(
        '💳 Configurando pagamento cartão Mercado Pago | '
        'PaymentMethod ID: %s | Parcelas: %s',
        payment_method_id,
        installments,
    )
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
    logger.info(
        '✅ Pagamento cartão Mercado Pago configurado com sucesso | '
        'Valor: R$ %s | Parcelas: %s',
        cart.total,
        installments,
    )
    return cart
