import pytest
from job_v2.service.status import ReturnGatewayID, UpdateStatus
from unittest import mock
from models.order import Order

order = {
    'id': '4',
    'customer_id': '1',
    'order_date': '' ,
    'tracking_number': 'None',
    'payment_id': '10956582',
    'order_status': 'pending',
    'last_updated': 'None'
    }

@mock.patch('job_v2.service.status.ReturnGatewayID', return_value=order)
def test_gateway_id(mocker):
    gateway_id = ReturnGatewayID(order['payment_id']).gateway_id()
    print(gateway_id)
    assert gateway_id.get('status') == 'paid'


@mock.patch('job_v2.service.status.get_db', return_value=order)
@mock.patch('job_v2.service.status.UpdateStatus', return_value="db")
def test_update_status(mocker, db):
    gateway_id = ReturnGatewayID(order['payment_id']).gateway_id()
    update = UpdateStatus(Order, gateway_id, db).update_status()
    assert update.order_status == "paid"