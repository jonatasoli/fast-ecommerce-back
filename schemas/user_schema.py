from pydantic import BaseModel




class AddressSchema(BaseModel):
    country: str
    state: str
    city: str
    neighborhood: str
    street: str
    street_number: str
    zipcode: str
    complement: str
    type_address: str
    category: str
