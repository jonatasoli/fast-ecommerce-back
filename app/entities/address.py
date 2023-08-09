from pydantic import BaseModel


class AddressBase(BaseModel):
    user_id: int
    type_address: str
    category: str
    country: str
    city: str
    state: str
    neighborhood: str
    street: str
    street_number: str
    address_complement: str
    zipcode: str
    active: bool


class CreateAddress(AddressBase):
    ...


class AddressInDB(AddressBase):
    ...
