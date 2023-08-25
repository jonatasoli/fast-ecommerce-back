import pytest


@pytest.mark.skip()
def test_create_order(t_client):
    order = {
        'id': 3,
        'customer_id': 1,
        'order_date': '2020-11-11 17:01:01',
        'tracking_number': '2341231',
        'payment_id': 1,
        'last_updated': '2020-11-11 17:01:01',
        'order_status': 'pending',
    }
    r = t_client.post('/order/create_order', json=order)
    response = r.json()
    assert r.status_code == 200
    assert response.get('id') == 3


def test_put_order(t_client):
    order = {
        'id': 2,
        'customer_id': 1,
        'order_date': '2020-11-11 17:30:01',
        'payment_id': 1,
        'tracking_number': '3334131',
    }
    r = t_client.put('/order/2', json=order)
    response = r.json()
    assert r.status_code == 200
    assert response.get('tracking_number') == '3334131'


@pytest.mark.skip()
def test_get_order_id(t_client):
    r = t_client.get('/order/1')
    response = r.json()
    assert r.status_code == 200
    assert response.get('name') == 'Jonatas L Oliveira'


@pytest.mark.skip()
def test_get_order_user_id(t_client):
    r = t_client.get('/order/user/1')
    response = r.json()
    assert r.status_code == 200
    assert response.get('name') == 'Jonatas L Oliveira'


@pytest.mark.skip()
def test_order_status(t_client: str) -> None:
    """Test order status."""
    orderState = {'order_id': 1, 'payment_id': 1, 'order_status': 'paid'}
    r = t_client.post('/update-payment-and-order-status', json=orderState)
    r.json()
    assert r.status_code == 200


# def test_check_status():


# def test_status_pending():


# def test_status_paid():
