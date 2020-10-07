import pytest
from job_service import service
from unittest import mock

db_steps ={'''
        "Order_id":"1",
        "Status":"PAYMENT_PENDING"
        "last_updated":"2020-10-07",
        "sending":"False",
        "active":"True"
        '''}

@mock.patch('job_service.service.main', return_value = db_steps)
def test_order_steps(mocker):
    service.main()
    mocker.assert_called_once_with()

@mock.patch('job_service.service.process', return_value = db_steps)
def test_process(mocker):
    service.process([{"Order_id":"1", "Status": "PAYMENT_PENDING"}])
    mocker.assert_called_once_with([{"Order_id": "1" ,"Status": "PAYMENT_PENDING"}])
