from pydantic import BaseModel, SecretStr


class CreditCardPayment(BaseModel):
    api_key: str
    amount: int
    card_number: str
    card_cvv: str
    card_expiration_date: str
    card_holder_name: str
    installments: str
    customer: dict
    billing: dict
    shipping: dict
    items: list


class SlipPayment(BaseModel):
    amount: int
    api_key: str
    customer: dict
    type: str
    payment_method: str
    country: str
    boleto_expiration_date: str
    email: str
    name: str
    documents: list


class ConfigCreditCard(BaseModel):
    fee: str
    min_installment: int
    max_installment: int

    class Config:
        orm_mode = True


class ConfigCreditCardResponse(BaseModel):
    id: int
    fee: str
    min_installment_with_fee: int
    mx_installments: int

    class Config:
        orm_mode = True
