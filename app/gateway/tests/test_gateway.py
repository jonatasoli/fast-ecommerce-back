from gateway.payment_gateway import return_transaction

def test_return_transaction():
    transaction = return_transaction(10517987) 
    assert transaction.get("gateway_id") == 10517987