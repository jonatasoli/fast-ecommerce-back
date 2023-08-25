from pydantic import BaseModel


class AddressBase(BaseModel):
    address_id: int | None
    user_id: int | None
    country: str
    city: str
    state: str
    neighborhood: str
    street: str
    street_number: str
    address_complement: str
    zipcode: str
    active: bool


class CreateAddress(BaseModel):
    shipping_is_payment: bool
    user_address: AddressBase
    shipping_address: AddressBase | None = None


class AddressInDB(BaseModel):
    address_id: int
    user_id: int
    country: str
    city: str
    state: str
    neighborhood: str
    street: str
    street_number: str
    address_complement: str
    zipcode: str
    active: bool
