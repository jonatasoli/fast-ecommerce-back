from pydantic import BaseModel


class CreditCardInformation(BaseModel):
    credit_card_name: str | None
    credit_card_number: str | None
    credit_card_cvv: str | None
    credit_card_validate: str | None
    installments: int | None
