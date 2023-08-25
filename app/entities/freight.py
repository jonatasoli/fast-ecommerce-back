from pydantic import BaseModel


class ShippingAddress(BaseModel):
    ship_name: str | None = None
    ship_address: str | None = None
    ship_number: str | None = None
    ship_address_complement: str | None = None
    ship_neighborhood: str | None = None
    ship_city: str | None = None
    ship_state: str | None = None
    ship_country: str | None = None
    ship_zip: str | None = None
