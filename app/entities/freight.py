from pydantic import BaseModel


class ShippingAddress(BaseModel):
    ship_name: str | None
    ship_address: str | None
    ship_number: str | None
    ship_address_complement: str | None
    ship_neighborhood: str | None
    ship_city: str | None
    ship_state: str | None
    ship_country: str | None
    ship_zip: str | None
