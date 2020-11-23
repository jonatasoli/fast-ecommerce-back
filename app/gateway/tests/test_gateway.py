from gateway.payment_gateway import return_transaction

def test_return_transaction():
    transaction = return_transaction(10460784)
    assert transaction.get("gateway_id") == 10460784
