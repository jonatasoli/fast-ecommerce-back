from pydantic import BaseModel, SecretStr


class CreditCardPayment(BaseModel):
    api_key: str 
    amount: int
    card_number: str
    card_cvv: str
    card_expiration_date: str
    card_holder_name: str
    customer: dict
    billing: dict
    shipping: dict
    items: list


class SlipPayment(BaseModel):
    amount: int
    api_key: str
    payment_method: str
    customer: dict
    
