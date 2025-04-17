POST https://apisandbox.cieloecommerce.cielo.com.br/1/card/
Content-Type: application/json
MerchantId: 8937bd5b-9796-494d-9fe5-f76b3e4da633
MerchantKey: XKGHUBSBKIRXKAVPSKWLVXYCLVJUGTNZLIHPUSYV
accept: application/json
{
  "CustomerName": "Comprador Teste Cielo",
  "CardNumber": "4024007110880035",
  "Holder": "Comprador T Cielo",
  "ExpirationDate": "10/2026",
  "Brand": "Visa"
}

POST https://apisandbox.cieloecommerce.cielo.com.br/1/sales/
Content-Type: application/json
MerchantId: 8937bd5b-9796-494d-9fe5-f76b3e4da633
MerchantKey: XKGHUBSBKIRXKAVPSKWLVXYCLVJUGTNZLIHPUSYV
accept: application/json
{
  "MerchantOrderId": "Loja123456",
  "Customer": {
    "Name": "Comprador Teste"
  },
  "Payment": {
    "Type": "CreditCard",
    "Amount": 100,
    "Installments": 1,
    "Capture": false,
    "SoftDescriptor": "compra x",
    "CreditCard": {
      "CardToken": "e3e93df5-cfd8-4546-a5f5-76c9c1f076a1",
      "SecurityCode": "262",
      "Brand": "Visa"
    }
  }
}
