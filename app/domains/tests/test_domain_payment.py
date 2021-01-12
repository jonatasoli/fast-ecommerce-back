# import pytest
# from sqlalchemy.orm import Session
# from domains import domain_payment 
# from loguru import logger


# @pytest.mark.skip(reason="refactoring test")
# def test_payment_process_credit_card(db: Session):
#     checkout_data = {
#             "document": "34826669895",
#             "mail": "contato@jonatasoliveira.me",
#             "password": "asdasd",
#             "name": "Jonatas Oliveira",
#             "address": "Rua São Joaquim",
#             "_number": "123",
#             "complement": "apto 44",
#             "neighborhood": "Jardim Cruzeiro",
#             "city": "São Paulo",
#             "_state": "São Paulo",
#             "country": "Brasil",
#             "zip": "01508000",
#             "shipping_is_payment": True,
#             "ship_name": "",
#             "ship_address": "",
#             "ship_number": "",
#             "ship_complement": "",
#             "ship_neighborhood": "",
#             "ship_city": "",
#             "ship_state": "",
#             "ship_country": "Brasil",
#             "ship_zip": "",
#             "payment_method": "credit-card",
#             "shopping_cart": ["1"],
#             "credit_card_name": "Jonatas Oliveira",
#             "credit_card_number": "4111111111111111",
#             "credit_card_cvv": "123",
#             "credit_card_validate": "2020-08-17T12:55:24.619Z",
#             "installments": [{"value": 1, "name": "1 sem juros"},
#                 {"value": 2, "name": "2 com juros"}],
#             "installment_select": 1,
#             "phone": "11974406877"}

#     _payment = domain_payment.process_checkout(
#             db=db,
#             checkout_data=checkout_data,
#             affiliate=None,
#             cupom=None)
#     logger.info(_payment)

#     assert _payment == {
#                 type("payment_id"): str,
#                 "status": "paid"
#             } 



